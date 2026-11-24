#!/usr/bin/env python3
"""Generate repository-hosted dark and light GitHub analytics SVGs.

Uses only the Python 3 standard library and real GitHub public profile, GraphQL,
and REST API data. All metrics strictly reflect public GitHub activity so local
runs and GitHub Actions runs (using GITHUB_TOKEN) report identical counts that
match the public contribution graph on github.com/<username>.
Never logs or writes credentials.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

USERNAME = os.environ.get("GITHUB_USERNAME", "dandisetiawanco")
REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "assets" / "analytics"

THEMES: dict[str, dict[str, Any]] = {
    "dark": {
        "suffix": "",
        "bg": "#0D1117",
        "card_inner": "#101A17",
        "border": "#24352E",
        "divider": "#1E2D27",
        "ink": "#F0F6FC",
        "ink_sec": "#D1D5DB",
        "ink_muted": "#9CA3AF",
        "accent_text": "#34D399",
        "line_stroke": "#10B981",
        "dot_fill": "#34D399",
        "area_top": "#10B981",
        "grid_line": "#192520",
        "lang_colors": ["#34D399", "#10B981", "#6EE7B7", "#059669", "#9CA3AF", "#526D63"],
    },
    "light": {
        "suffix": "-light",
        "bg": "#FFFFFF",
        "card_inner": "#F6F9F8",
        "border": "#D5E0DC",
        "divider": "#DCE5E1",
        "ink": "#0F1715",
        "ink_sec": "#2E3A36",
        "ink_muted": "#566560",
        "accent_text": "#047857",
        "line_stroke": "#059669",
        "dot_fill": "#047857",
        "area_top": "#059669",
        "grid_line": "#E5EDE9",
        "lang_colors": ["#047857", "#10B981", "#065F46", "#34D399", "#566560", "#8CA19A"],
    },
}


def _resolve_token() -> str:
    env_token = os.environ.get("GITHUB_TOKEN", "").strip()
    if env_token:
        return env_token
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
                    return val
    except Exception:
        pass
    raise RuntimeError("GITHUB_TOKEN is required to query the GitHub GraphQL API.")


def _api_request(url: str, token: str, payload: dict[str, Any] | None = None) -> Any:
    headers = {
        "User-Agent": "dandisetiawanco-profile-analytics",
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
    }
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fetch_public_calendar_days(username: str) -> list[dict[str, Any]] | None:
    """Fetch unauthenticated public daily contributions so counts match public GitHub."""
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "dandisetiawanco-profile-analytics",
            "Accept": "text/html",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw_html = resp.read().decode("utf-8", errors="replace")
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

    return [
        {"date": d_str, "count": counts_by_date[d_str]}
        for d_str in sorted(counts_by_date.keys())
    ]


def _group_days_into_sunday_weeks(days: list[dict[str, Any]]) -> list[dict[str, Any]]:
    weeks: list[dict[str, Any]] = []
    cur_first: str | None = None
    cur_total = 0
    for item in days:
        d_obj = dt.date.fromisoformat(item["date"])
        # Sunday starts a new GitHub contribution calendar column (weekday(): Mon=0..Sun=6)
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


def fetch_github_data(username: str, token: str) -> dict[str, Any]:
    query = """
    query($login: String!) {
      user(login: $login) {
        login
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
          totalCount
          nodes {
            name
            stargazerCount
          }
        }
        contributionsCollection {
          commitContributionsByRepository(maxRepositories: 100) {
            repository {
              isPrivate
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
    gql = _api_request(
        "https://api.github.com/graphql",
        token,
        {"query": query, "variables": {"login": username}},
    )
    if gql.get("errors"):
        raise RuntimeError(f"GraphQL error: {gql['errors']}")

    user = gql["data"]["user"]
    cc = user["contributionsCollection"]

    public_commits = sum(
        int(entry["contributions"]["totalCount"])
        for entry in cc["commitContributionsByRepository"]
        if not entry["repository"]["isPrivate"]
    )

    public_days = _fetch_public_calendar_days(username)
    if public_days:
        all_days = public_days
        weekly_totals = _group_days_into_sunday_weeks(all_days)
        total_contributions = sum(int(d["count"]) for d in all_days)
    else:
        cal = cc["contributionCalendar"]
        weeks = cal["weeks"]
        all_days = [
            {"date": d["date"], "count": int(d["contributionCount"])}
            for w in weeks
            for d in w["contributionDays"]
        ]
        weekly_totals = [
            {
                "first_day": w["firstDay"],
                "count": sum(int(d["contributionCount"]) for d in w["contributionDays"]),
            }
            for w in weeks
        ]
        total_contributions = int(cal["totalContributions"])

    longest_streak = 0
    cur_run = 0
    for day in all_days:
        if day["count"] > 0:
            cur_run += 1
            if cur_run > longest_streak:
                longest_streak = cur_run
        else:
            cur_run = 0

    rev = list(reversed(all_days))
    start_idx = 1 if (rev and rev[0]["count"] == 0) else 0
    current_streak = 0
    for day in rev[start_idx:]:
        if day["count"] > 0:
            current_streak += 1
        else:
            break

    repos = _api_request(
        f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated",
        token,
    )
    lang_bytes: dict[str, int] = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        langs = _api_request(repo["languages_url"], token)
        for lang, count in langs.items():
            lang_bytes[lang] = lang_bytes.get(lang, 0) + int(count)

    sorted_langs = sorted(lang_bytes.items(), key=lambda item: -item[1])
    total_bytes = sum(v for _, v in sorted_langs) or 1
    top_langs = [
        {"name": name, "bytes": count, "pct": round((count / total_bytes) * 100.0, 1)}
        for name, count in sorted_langs[:6]
    ]

    return {
        "updated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        "public_repos": int(user["repositories"]["totalCount"]),
        "total_contributions": total_contributions,
        "public_commits": public_commits,
        "active_days": sum(1 for d in all_days if d["count"] > 0),
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "top_langs": top_langs,
        "weekly_totals": weekly_totals,
    }


def render_stats_svg(data: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    metrics = [
        ("Public Contributions", str(data["total_contributions"])),
        ("Public Repositories", str(data["public_repos"])),
        ("Public Commits", str(data["public_commits"])),
        ("Active Days (12m)", str(data["active_days"])),
        ("Current Streak", f"{data['current_streak']}d"),
        ("Longest Streak", f"{data['longest_streak']}d"),
    ]

    cells = []
    for idx, (label, value) in enumerate(metrics):
        col = idx % 3
        row = idx // 3
        x = 20 + col * 136
        y = 58 + row * 68
        val_fill = t["accent_text"] if idx in (0, 4) else t["ink"]
        cells.append(
            f'  <rect x="{x}" y="{y}" width="128" height="58" rx="8" fill="{t["card_inner"]}" stroke="{t["divider"]}" stroke-width="1" />\n'
            f'  <text x="{x + 12}" y="{y + 24}" class="mono" font-size="18" font-weight="700" fill="{val_fill}">{html.escape(value)}</text>\n'
            f'  <text x="{x + 12}" y="{y + 42}" class="sans" font-size="10.8" font-weight="500" fill="{t["ink_sec"]}">{html.escape(label)}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 204" width="440" height="204" role="img" aria-labelledby="stats-t-{theme_name} stats-d-{theme_name}">
  <title id="stats-t-{theme_name}">GitHub Statistics for {USERNAME} (Public Scope)</title>
  <desc id="stats-d-{theme_name}">Public GitHub metrics over the last 12 months: {data['total_contributions']} public contributions, {data['public_repos']} public repositories, {data['public_commits']} public commits, {data['current_streak']} day current streak.</desc>
  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
  </style>
  <rect x="0.75" y="0.75" width="438.5" height="202.5" rx="12" fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="1.2" />
  <text x="20" y="32" class="sans" font-size="14.5" font-weight="700" fill="{t["ink"]}">GitHub Statistics</text>
  <text x="420" y="31.5" text-anchor="end" class="mono" font-size="10.8" fill="{t["ink_muted"]}">Public scope  ·  {data["updated_utc"]}</text>
  <line x1="20" y1="45" x2="420" y2="45" stroke="{t["divider"]}" stroke-width="1" />
{chr(10).join(cells)}
</svg>
"""


def render_languages_svg(data: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    langs = data["top_langs"]
    total_pct = sum(item["pct"] for item in langs) or 100.0

    gap = 2.0
    total_gaps = gap * max(0, len(langs) - 1)
    avail_w = 400.0 - total_gaps
    bar_x = 20.0
    bar_parts = []
    for idx, item in enumerate(langs):
        seg_w = max(4.0, (item["pct"] / total_pct) * avail_w)
        color = t["lang_colors"][idx % len(t["lang_colors"])]
        bar_parts.append(
            f'    <rect x="{bar_x:.1f}" y="60" width="{seg_w:.1f}" height="10" fill="{color}" />'
        )
        bar_x += seg_w + gap

    legend_parts = []
    for idx, item in enumerate(langs):
        col = idx % 2
        row = idx // 2
        x = 20 + col * 210
        y = 104 + row * 32
        color = t["lang_colors"][idx % len(t["lang_colors"])]
        legend_parts.append(
            f'  <rect x="{x}" y="{y - 10}" width="10" height="10" rx="2.5" fill="{color}" />\n'
            f'  <text x="{x + 18}" y="{y}" class="sans" font-size="13" font-weight="600" fill="{t["ink"]}">{html.escape(item["name"])}</text>\n'
            f'  <text x="{x + 186}" y="{y}" text-anchor="end" class="mono" font-size="12" fill="{t["ink_sec"]}">{item["pct"]:.1f}%</text>'
        )

    clip_id = f"lang-bar-{theme_name}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 204" width="440" height="204" role="img" aria-labelledby="langs-t-{theme_name} langs-d-{theme_name}">
  <title id="langs-t-{theme_name}">Most-Used Languages for {USERNAME}</title>
  <desc id="langs-d-{theme_name}">Programming language byte share across owned non-fork public GitHub repositories.</desc>
  <defs>
    <clipPath id="{clip_id}">
      <rect x="20" y="60" width="400" height="10" rx="5" />
    </clipPath>
  </defs>
  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
  </style>
  <rect x="0.75" y="0.75" width="438.5" height="202.5" rx="12" fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="1.2" />
  <text x="20" y="32" class="sans" font-size="14.5" font-weight="700" fill="{t["ink"]}">Most-Used Languages</text>
  <text x="420" y="31.5" text-anchor="end" class="mono" font-size="10.8" fill="{t["ink_muted"]}">Owned public repos</text>
  <line x1="20" y1="45" x2="420" y2="45" stroke="{t["divider"]}" stroke-width="1" />
  <g clip-path="url(#{clip_id})">
{chr(10).join(bar_parts)}
  </g>
{chr(10).join(legend_parts)}
</svg>
"""


def render_activity_svg(data: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    weekly = data["weekly_totals"]
    max_val = max((w["count"] for w in weekly), default=1)
    max_scale = max(4, ((max_val + 3) // 4) * 4)

    chart_x, chart_y, chart_w, chart_h = 48.0, 58.0, 824.0, 96.0
    n = max(1, len(weekly) - 1)

    points: list[tuple[float, float, int, str]] = []
    for i, item in enumerate(weekly):
        px = chart_x + (i / n) * chart_w
        py = chart_y + chart_h - (item["count"] / max_scale) * chart_h
        points.append((px, py, item["count"], item["first_day"]))

    line_coords = " ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in points)
    area_path = (
        f"M {points[0][0]:.1f} {chart_y + chart_h:.1f} "
        + " ".join(f"L {x:.1f} {y:.1f}" for x, y, _, _ in points)
        + f" L {points[-1][0]:.1f} {chart_y + chart_h:.1f} Z"
    )

    grid_svg = []
    for frac in (0.0, 0.5, 1.0):
        gy = chart_y + chart_h - frac * chart_h
        gval = int(round(frac * max_scale))
        grid_svg.append(
            f'  <line x1="{chart_x:.0f}" y1="{gy:.1f}" x2="{chart_x + chart_w:.0f}" y2="{gy:.1f}" stroke="{t["grid_line"]}" stroke-width="1" />\n'
            f'  <text x="{chart_x - 10:.0f}" y="{gy + 4:.1f}" text-anchor="end" class="mono" font-size="10.5" fill="{t["ink_muted"]}">{gval}</text>'
        )

    month_labels = []
    seen_months: set[str] = set()
    last_label_x = -100.0
    for px, _, _, first_day in points:
        ym = first_day[:7]
        if ym not in seen_months:
            seen_months.add(ym)
            label = dt.date.fromisoformat(first_day).strftime("%b")
            if px - last_label_x >= 38.0 and px <= chart_x + chart_w - 18:
                month_labels.append(
                    f'  <text x="{px:.1f}" y="{chart_y + chart_h + 20:.1f}" class="mono" font-size="10.5" fill="{t["ink_muted"]}">{label}</text>'
                )
                last_label_x = px

    dot_svg = []
    for px, py, cnt, _ in points:
        if cnt > 0:
            dot_svg.append(
                f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="{t["dot_fill"]}" stroke="{t["bg"]}" stroke-width="1.2" />'
            )

    grad_id = f"act-grad-{theme_name}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 192" width="900" height="192" role="img" aria-labelledby="act-t-{theme_name} act-d-{theme_name}">
  <title id="act-t-{theme_name}">Weekly Public Contribution Activity for {USERNAME}</title>
  <desc id="act-d-{theme_name}">Trailing 52-week public contribution activity totaling {data["total_contributions"]} public contributions with a peak of {max_val} in a single week.</desc>
  <defs>
    <linearGradient id="{grad_id}" x1="0" y1="58" x2="0" y2="154" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["area_top"]}" stop-opacity="0.22" />
      <stop offset="100%" stop-color="{t["area_top"]}" stop-opacity="0.01" />
    </linearGradient>
  </defs>
  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
  </style>
  <rect x="0.75" y="0.75" width="898.5" height="190.5" rx="12" fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="1.2" />
  <text x="24" y="32" class="sans" font-size="14.5" font-weight="700" fill="{t["ink"]}">Weekly Contribution Activity</text>
  <text x="876" y="31.5" text-anchor="end" class="mono" font-size="11" fill="{t["ink_muted"]}">{data["total_contributions"]} public  ·  Peak {max_val}/wk  ·  Trailing 52 weeks</text>
  <line x1="24" y1="45" x2="876" y2="45" stroke="{t["divider"]}" stroke-width="1" />
{chr(10).join(grid_svg)}
  <path d="{area_path}" fill="url(#{grad_id})" />
  <polyline points="{line_coords}" fill="none" stroke="{t["line_stroke"]}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
{chr(10).join(dot_svg)}
{chr(10).join(month_labels)}
</svg>
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    token = _resolve_token()
    data = fetch_github_data(USERNAME, token)

    outputs: list[tuple[str, str]] = []
    for theme_name, cfg in THEMES.items():
        sfx = cfg["suffix"]
        outputs.extend(
            [
                (f"stats{sfx}.svg", render_stats_svg(data, theme_name)),
                (f"languages{sfx}.svg", render_languages_svg(data, theme_name)),
                (f"activity{sfx}.svg", render_activity_svg(data, theme_name)),
            ]
        )

    for filename, svg_text in outputs:
        ET.fromstring(svg_text)
        target = OUT_DIR / filename
        target.write_text(svg_text, encoding="utf-8")
        print(f"Wrote {target.relative_to(REPO_ROOT)} ({len(svg_text)} bytes)")


if __name__ == "__main__":
    main()
