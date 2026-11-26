"""Resilient public GitHub REST, GraphQL, and calendar client using Python stdlib."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any

USER_AGENT = "dandisetiawanco-profile-engine/2.0"


def resolve_token() -> tuple[str, str]:
    """Return (token, source) without ever logging credential contents."""
    env_token = os.environ.get("GITHUB_TOKEN", "").strip()
    if env_token:
        return env_token, "env"
    try:
        res = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n",
            text=True,
            capture_output=True,
            timeout=5,
        )
        for line in res.stdout.splitlines():
            if line.startswith("password="):
                val = line.split("=", 1)[1].strip()
                if val:
                    return val, "git-credential"
    except Exception:
        pass
    return "", "unauthenticated"


def _request_with_retry(
    url: str,
    headers: dict[str, str],
    payload: bytes | None = None,
    retries: int = 3,
    timeout: int = 20,
) -> bytes:
    last_err: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, data=payload, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as err:
            last_err = err
            if err.code in (403, 429):
                remaining = err.headers.get("X-RateLimit-Remaining", "")
                retry_after = err.headers.get("Retry-After", "")
                if remaining == "0" and not retry_after:
                    raise RuntimeError(f"GitHub API rate limit exhausted ({err.code}) for {url}") from err
                wait_s = min(int(retry_after) if retry_after.isdigit() else (2 ** attempt), 10)
                time.sleep(wait_s)
                continue
            if err.code >= 500 and attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as err:
            last_err = err
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"Request failed after {retries} attempts: {last_err}")


def api_get_json(url: str, token: str) -> Any:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    raw = _request_with_retry(url, headers=headers)
    return json.loads(raw.decode("utf-8"))


def api_graphql(query: str, variables: dict[str, Any], token: str) -> dict[str, Any] | None:
    if not token:
        return None
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    raw = _request_with_retry("https://api.github.com/graphql", headers=headers, payload=body)
    data = json.loads(raw.decode("utf-8"))
    if data.get("errors"):
        raise RuntimeError(f"GraphQL error: {data['errors']}")
    return data


def fetch_public_calendar_days(username: str) -> list[dict[str, Any]] | None:
    """Parse github.com public contribution calendar so totals match public profile view."""
    url = f"https://github.com/users/{username}/contributions"
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html"}
    try:
        raw_html = _request_with_retry(url, headers=headers).decode("utf-8", errors="replace")
    except Exception:
        return None

    id_to_date: dict[str, str] = {}
    for td_match in re.finditer(r"<td\b[^>]*>", raw_html):
        tag = td_match.group(0)
        d_m = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', tag)
        i_m = re.search(r'id="([^"]+)"', tag)
        if d_m and i_m:
            id_to_date[i_m.group(1)] = d_m.group(1)

    if not id_to_date:
        return None

    counts_by_date: dict[str, int] = {d: 0 for d in id_to_date.values()}
    for tip_match in re.finditer(
        r'<tool-tip\b[^>]*for="([^"]+)"[^>]*>(.*?)</tool-tip>',
        raw_html,
        flags=re.DOTALL,
    ):
        comp_id = tip_match.group(1)
        tip_text = tip_match.group(2).strip()
        if comp_id in id_to_date:
            c_m = re.match(r"^(\d+)\s+contribution", tip_text)
            counts_by_date[id_to_date[comp_id]] = int(c_m.group(1)) if c_m else 0

    return [{"date": d, "count": counts_by_date[d]} for d in sorted(counts_by_date.keys())]


def _group_sunday_weeks(days: list[dict[str, Any]]) -> list[dict[str, Any]]:
    weeks: list[dict[str, Any]] = []
    cur_first: str | None = None
    cur_total = 0
    for item in days:
        d_obj = dt.date.fromisoformat(item["date"])
        if cur_first is None or d_obj.weekday() == 6:
            if cur_first is not None:
                weeks.append({"first_day": cur_first, "count": cur_total})
            cur_first = item["date"]
            cur_total = int(item["count"])
        else:
            cur_total += int(item["count"])
    if cur_first is not None:
        weeks.append({"first_day": cur_first, "count": cur_total})
    return weeks


def _is_meaningful_commit(
    message: str,
    author: str,
    exclude_prefixes: list[str],
    exclude_authors: list[str],
) -> bool:
    low_msg = message.strip().lower()
    low_author = author.strip().lower()
    if not low_msg:
        return False
    if any(low_author == a.lower() or low_author.endswith("[bot]") for a in exclude_authors):
        return False
    if any(low_msg.startswith(p.lower()) for p in exclude_prefixes):
        return False
    if "refresh public github analytics" in low_msg or "automated profile refresh" in low_msg:
        return False
    return True


def fetch_profile_dataset(config: dict[str, Any]) -> dict[str, Any]:
    """Fetch complete verified public dataset for the configured GitHub user."""
    username = os.environ.get("GITHUB_USERNAME", config["username"]).strip() or config["username"]
    token, token_source = resolve_token()

    auto_cfg = config.get("automation", {})
    exclude_recent = {r.lower() for r in auto_cfg.get("exclude_repos_from_recent", [])}
    exclude_prefixes = list(auto_cfg.get("exclude_commit_prefixes", []))
    exclude_authors = list(auto_cfg.get("exclude_authors", []))
    max_recent = int(auto_cfg.get("max_recent_repos", 6))

    user_rest = api_get_json(f"https://api.github.com/users/{username}", token)
    raw_repos = api_get_json(
        f"https://api.github.com/users/{username}/repos?per_page=100&sort=pushed&type=owner",
        token,
    )

    public_repos: list[dict[str, Any]] = []
    lang_bytes: dict[str, int] = {}
    total_stars = 0
    total_forks = 0
    latest_releases: list[dict[str, Any]] = []

    for repo in raw_repos:
        if repo.get("private") or repo.get("fork") or repo.get("archived"):
            continue
        name = repo["name"]
        try:
            langs = api_get_json(repo["languages_url"], token)
            if not isinstance(langs, dict):
                langs = {}
        except Exception:
            langs = {}

        try:
            commits_raw = api_get_json(
                f"https://api.github.com/repos/{username}/{name}/commits?per_page=8",
                token,
            )
            if not isinstance(commits_raw, list):
                commits_raw = []
        except Exception:
            commits_raw = []

        # Skip genuinely empty repositories (GitHub can briefly report size=0 right after push).
        if repo.get("size", 0) == 0 and not langs and not commits_raw:
            continue

        try:
            releases_raw = api_get_json(
                f"https://api.github.com/repos/{username}/{name}/releases?per_page=3",
                token,
            )
            if not isinstance(releases_raw, list):
                releases_raw = []
        except Exception:
            releases_raw = []

        meaningful_commits: list[dict[str, Any]] = []
        for c in commits_raw:
            c_info = c.get("commit", {})
            msg = (c_info.get("message") or "").splitlines()[0].strip()
            author_name = (c_info.get("author") or {}).get("name") or (c.get("author") or {}).get("login") or ""
            if _is_meaningful_commit(msg, author_name, exclude_prefixes, exclude_authors):
                meaningful_commits.append(
                    {
                        "sha": (c.get("sha") or "")[:7],
                        "message": msg,
                        "date": (c_info.get("author") or {}).get("date") or "",
                        "url": c.get("html_url") or repo["html_url"],
                    }
                )
            if len(meaningful_commits) >= 3:
                break

        releases = [
            {
                "repo": name,
                "tag": rel.get("tag_name") or "",
                "name": rel.get("name") or rel.get("tag_name") or "",
                "published_at": rel.get("published_at") or "",
                "url": rel.get("html_url") or repo["html_url"],
            }
            for rel in releases_raw
            if not rel.get("draft")
        ]
        latest_releases.extend(releases)

        stars = int(repo.get("stargazers_count") or 0)
        forks = int(repo.get("forks_count") or 0)
        total_stars += stars
        total_forks += forks

        for lang_name, b_count in langs.items():
            lang_bytes[lang_name] = lang_bytes.get(lang_name, 0) + int(b_count)

        homepage = (repo.get("homepage") or "").strip()
        if homepage and not homepage.startswith(("http://", "https://")):
            homepage = ""

        public_repos.append(
            {
                "name": name,
                "full_name": repo["full_name"],
                "url": repo["html_url"],
                "description": (repo.get("description") or "").strip(),
                "homepage": homepage,
                "language": repo.get("language") or (next(iter(langs.keys()), "Multi")),
                "languages": langs,
                "topics": list(repo.get("topics") or []),
                "stars": stars,
                "forks": forks,
                "license": (repo.get("license") or {}).get("spdx_id") or "",
                "created_at": repo.get("created_at") or "",
                "updated_at": repo.get("updated_at") or "",
                "pushed_at": repo.get("pushed_at") or "",
                "latest_release": releases[0] if releases else None,
                "recent_commits": meaningful_commits,
            }
        )

    # Fetch public GraphQL commit breakdown and fallback calendar when authenticated.
    gql_commits_by_repo: list[dict[str, Any]] = []
    public_commits_total = 0
    gql_calendar_days: list[dict[str, Any]] = []

    gql_query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          commitContributionsByRepository(maxRepositories: 100) {
            repository {
              name
              isPrivate
              isFork
              isArchived
            }
            contributions {
              totalCount
            }
          }
          contributionCalendar {
            totalContributions
            weeks {
              firstDay
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    try:
        gql_resp = api_graphql(gql_query, {"login": username}, token)
    except Exception:
        gql_resp = None

    if gql_resp and gql_resp.get("data", {}).get("user"):
        cc = gql_resp["data"]["user"]["contributionsCollection"]
        for entry in cc.get("commitContributionsByRepository", []):
            r_meta = entry["repository"]
            if r_meta.get("isPrivate") or r_meta.get("isFork"):
                continue
            cnt = int(entry["contributions"]["totalCount"])
            public_commits_total += cnt
            gql_commits_by_repo.append({"repo": r_meta["name"], "commits": cnt})
        cal = cc.get("contributionCalendar", {})
        for w in cal.get("weeks", []):
            for d in w.get("contributionDays", []):
                gql_calendar_days.append({"date": d["date"], "count": int(d["contributionCount"])})

    public_days = fetch_public_calendar_days(username)
    all_days = public_days if public_days else gql_calendar_days
    weekly_totals = _group_sunday_weeks(all_days)
    total_contributions = sum(int(d["count"]) for d in all_days)

    longest_streak = 0
    cur_run = 0
    for day in all_days:
        if day["count"] > 0:
            cur_run += 1
            longest_streak = max(longest_streak, cur_run)
        else:
            cur_run = 0

    rev_days = list(reversed(all_days))
    start_idx = 1 if (rev_days and rev_days[0]["count"] == 0) else 0
    current_streak = 0
    for day in rev_days[start_idx:]:
        if day["count"] > 0:
            current_streak += 1
        else:
            break

    active_days = sum(1 for d in all_days if d["count"] > 0)
    peak_day = max((int(d["count"]) for d in all_days), default=0)
    peak_week = max((int(w["count"]) for w in weekly_totals), default=0)

    sorted_langs = sorted(lang_bytes.items(), key=lambda kv: -kv[1])
    total_bytes = sum(v for _, v in sorted_langs) or 1
    top_langs = [
        {
            "name": name,
            "bytes": b_val,
            "pct": round((b_val / total_bytes) * 100.0, 1),
        }
        for name, b_val in sorted_langs[:7]
    ]

    # Sort public commits per non-profile repo for velocity breakdown.
    product_repo_commits = sorted(
        [item for item in gql_commits_by_repo if item["repo"].lower() not in exclude_recent],
        key=lambda x: -x["commits"],
    )[:6]

    # Build recently shipped feed strictly from active non-profile public repos.
    recent_feed = [
        r
        for r in sorted(public_repos, key=lambda x: x["pushed_at"], reverse=True)
        if r["name"].lower() not in exclude_recent and r["recent_commits"]
    ][:max_recent]

    latest_releases.sort(key=lambda rel: rel.get("published_at") or "", reverse=True)

    now_utc = dt.datetime.now(dt.timezone.utc)
    return {
        "schema_version": 2,
        "generated_at_utc": now_utc.strftime("%Y-%m-%d %H:%M UTC"),
        "updated_date_utc": now_utc.strftime("%Y-%m-%d"),
        "token_source": token_source,
        "scope": "public_owned_non_fork",
        "user": {
            "login": user_rest.get("login") or username,
            "name": user_rest.get("name") or config["identity"]["name"],
            "location": user_rest.get("location") or config["identity"]["location"],
            "public_repos": len(public_repos),
            "followers": int(user_rest.get("followers") or 0),
        },
        "stats": {
            "public_repos": len(public_repos),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "total_contributions": total_contributions,
            "public_commits": public_commits_total,
            "active_days": active_days,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "peak_day": peak_day,
            "peak_week": peak_week,
            "releases_count": len(latest_releases),
        },
        "languages": top_langs,
        "repo_commits": product_repo_commits,
        "weekly_totals": weekly_totals,
        "calendar_days": all_days,
        "repos": public_repos,
        "recent_feed": recent_feed,
        "latest_releases": latest_releases[:5],
    }
