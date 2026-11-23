#!/usr/bin/env python3
"""Generate repository-hosted dark and light GitHub analytics and animated snake SVGs.

Uses only the Python 3 standard library and real GitHub GraphQL/REST API data.
Authentication reads GITHUB_TOKEN from the environment (provided automatically in
GitHub Actions) with an optional local git-credential fallback during local runs.
Never logs or writes credentials.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import os
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
        "bg": "#0F1F2A",
        "bg_alt": "#0A151D",
        "card_inner": "#0C1821",
        "border": "#1F3E4B",
        "divider": "#1B3541",
        "ink": "#F0F7F4",
        "ink_sec": "#B2CEC6",
        "ink_muted": "#8CB3A9",
        "accent": "#34D399",
        "accent_alt": "#5EEAD4",
        "area_top": "#10B981",
        "grid_line": "#18303B",
        "levels": {
            "NONE": "#152632",
            "FIRST_QUARTILE": "#0F4D3F",
            "SECOND_QUARTILE": "#0D7A5F",
            "THIRD_QUARTILE": "#10B981",
            "FOURTH_QUARTILE": "#34D399",
        },
        "snake": ["#5EEAD4", "#34D399", "#10B981", "#059669", "#047857"],
        "lang_colors": ["#34D399", "#2EA8B8", "#83BCA8", "#5EEAD4", "#10B981", "#78A3B2"],
    },
    "light": {
        "suffix": "-light",
        "bg": "#FFFFFF",
        "bg_alt": "#F7FAF9",
        "card_inner": "#F7FAF9",
        "border": "#D6E5E1",
        "divider": "#E2EFEA",
        "ink": "#173344",
        "ink_sec": "#435C63",
        "ink_muted": "#4A656C",
        "accent": "#046C4E",
        "accent_alt": "#166270",
        "area_top": "#059669",
        "grid_line": "#E5F0EC",
        "levels": {
            "NONE": "#E7F1EE",
            "FIRST_QUARTILE": "#A7DFC8",
            "SECOND_QUARTILE": "#52B794",
            "THIRD_QUARTILE": "#108A65",
            "FOURTH_QUARTILE": "#065F46",
        },
        "snake": ["#064E3B", "#057A55", "#10B981", "#34D399", "#83BCA8"],
        "lang_colors": ["#057A55", "#1B6F7E", "#10B981", "#2996A8", "#5C9E8C", "#64848F"],
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


def fetch_github_data(username: str, token: str) -> dict[str, Any]:
    query = """
    query($login: String!) {
      user(login: $login) {
        login
        followers { totalCount }
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
          totalCount
          nodes {
            name
            stargazerCount
            forkCount
          }
        }
        contributionsCollection {
          totalCommitContributions
          totalIssueContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
          restrictedContributionsCount
          contributionCalendar {
            totalContributions
            weeks {
              firstDay
              contributionDays {
                date
                weekday
                contributionCount
                contributionLevel
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
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    all_days = [d for w in weeks for d in w["contributionDays"]]

    longest_streak = 0
    cur_run = 0
    for day in all_days:
        if day["contributionCount"] > 0:
            cur_run += 1
            if cur_run > longest_streak:
                longest_streak = cur_run
        else:
            cur_run = 0

    rev = list(reversed(all_days))
    start_idx = 1 if (rev and rev[0]["contributionCount"] == 0) else 0
    current_streak = 0
    for day in rev[start_idx:]:
        if day["contributionCount"] > 0:
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

    weekly_totals = []
    for week in weeks:
        total = sum(int(d["contributionCount"]) for d in week["contributionDays"])
        weekly_totals.append({"first_day": week["firstDay"], "count": total})

    return {
        "updated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        "public_repos": int(user["repositories"]["totalCount"]),
        "total_stars": sum(int(n["stargazerCount"]) for n in user["repositories"]["nodes"]),
        "total_contributions": int(cal["totalContributions"]),
        "commits": int(user["contributionsCollection"]["totalCommitContributions"]),
        "active_days": sum(1 for d in all_days if d["contributionCount"] > 0),
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "top_langs": top_langs,
        "weeks": weeks,
        "weekly_totals": weekly_totals,
    }


def render_stats_svg(data: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    metrics = [
        ("Annual Contributions", str(data["total_contributions"]), "Last 12 months"),
        ("Public Repositories", str(data["public_repos"]), "Owned open-source"),
        ("Commits Recorded", str(data["commits"]), "Annual commit count"),
        ("Active Days", str(data["active_days"]), "Days with activity"),
        ("Current Streak", f"{data['current_streak']}d", "Consecutive days"),
        ("Longest Streak", f"{data['longest_streak']}d", "Past 12 months"),
    ]

    cells = []
    for idx, (label, value, sub) in enumerate(metrics):
        col = idx % 3
        row = idx // 3
        x = 20 + col * 136
        y = 58 + row * 68
        val_fill = t["accent"] if idx in (0, 4) else t["ink"]
        cells.append(
            f'  <rect x="{x}" y="{y}" width="128" height="58" rx="8" fill="{t["card_inner"]}" stroke="{t["divider"]}" stroke-width="1" />\n'
            f'  <text x="{x + 12}" y="{y + 24}" class="mono" font-size="18" font-weight="700" fill="{val_fill}">{html.escape(value)}</text>\n'
            f'  <text x="{x + 12}" y="{y + 42}" class="sans" font-size="11" font-weight="500" fill="{t["ink_sec"]}">{html.escape(label)}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 204" width="440" height="204" role="img" aria-labelledby="stats-t-{theme_name} stats-d-{theme_name}">
  <title id="stats-t-{theme_name}">GitHub Statistics for {USERNAME}</title>
  <desc id="stats-d-{theme_name}">Real GitHub metrics: {data['total_contributions']} contributions, {data['public_repos']} repositories, {data['commits']} commits, {data['current_streak']} day current streak.</desc>
  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
  </style>
  <rect x="1" y="1" width="438" height="202" rx="12" fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="1.2" />
  <text x="20" y="33" class="sans" font-size="15" font-weight="700" fill="{t["ink"]}">GitHub Statistics</text>
  <text x="420" y="32" text-anchor="end" class="mono" font-size="11" fill="{t["ink_muted"]}">Updated {data["updated_utc"]}</text>
  <line x1="20" y1="45" x2="420" y2="45" stroke="{t["divider"]}" stroke-width="1" />
{chr(10).join(cells)}
</svg>
"""


def render_languages_svg(data: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    langs = data["top_langs"]
    total_pct = sum(item["pct"] for item in langs) or 100.0

    bar_x = 20.0
    bar_w = 400.0
    bar_parts = []
    for idx, item in enumerate(langs):
        seg_w = max(4.0, (item["pct"] / total_pct) * bar_w)
        color = t["lang_colors"][idx % len(t["lang_colors"])]
        bar_parts.append(
            f'    <rect x="{bar_x:.1f}" y="60" width="{seg_w:.1f}" height="10" fill="{color}" />'
        )
        bar_x += seg_w

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
  <title id="langs-t-{theme_name}">Most-Used Programming Languages for {USERNAME}</title>
  <desc id="langs-d-{theme_name}">Language breakdown computed across owned public GitHub repositories.</desc>
  <defs>
    <clipPath id="{clip_id}">
      <rect x="20" y="60" width="400" height="10" rx="5" />
    </clipPath>
  </defs>
  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
  </style>
  <rect x="1" y="1" width="438" height="202" rx="12" fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="1.2" />
  <text x="20" y="33" class="sans" font-size="15" font-weight="700" fill="{t["ink"]}">Most-Used Languages</text>
  <text x="420" y="32" text-anchor="end" class="mono" font-size="11" fill="{t["ink_muted"]}">Public repositories</text>
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
                f'  <circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="{t["accent"]}" stroke="{t["bg"]}" stroke-width="1.2" />'
            )

    grad_id = f"act-grad-{theme_name}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 192" width="900" height="192" role="img" aria-labelledby="act-t-{theme_name} act-d-{theme_name}">
  <title id="act-t-{theme_name}">Weekly GitHub Contribution Activity for {USERNAME}</title>
  <desc id="act-d-{theme_name}">52-week contribution cadence showing {data["total_contributions"]} total contributions with peak {max_val} in a single week.</desc>
  <defs>
    <linearGradient id="{grad_id}" x1="0" y1="58" x2="0" y2="154" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["area_top"]}" stop-opacity="0.28" />
      <stop offset="100%" stop-color="{t["area_top"]}" stop-opacity="0.01" />
    </linearGradient>
  </defs>
  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
  </style>
  <rect x="1" y="1" width="898" height="190" rx="12" fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="1.2" />
  <text x="24" y="33" class="sans" font-size="15" font-weight="700" fill="{t["ink"]}">Weekly Contribution Activity</text>
  <text x="876" y="32" text-anchor="end" class="mono" font-size="11.5" fill="{t["ink_muted"]}">{data["total_contributions"]} total  ·  Peak {max_val}/week  ·  Last 52 weeks</text>
  <line x1="24" y1="45" x2="876" y2="45" stroke="{t["divider"]}" stroke-width="1" />
{chr(10).join(grid_svg)}
  <path d="{area_path}" fill="url(#{grad_id})" />
  <polyline points="{line_coords}" fill="none" stroke="{t["accent"]}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />
{chr(10).join(dot_svg)}
{chr(10).join(month_labels)}
</svg>
"""


def _build_snake_path(weeks: list[dict[str, Any]]) -> tuple[list[tuple[int, int]], dict[tuple[int, int], int]]:
    """Compute an orthogonal grid path visiting every real active contribution cell."""
    num_cols = len(weeks)
    active_cells: list[tuple[int, int]] = []
    for c, week in enumerate(weeks):
        for day in week["contributionDays"]:
            if int(day["contributionCount"]) > 0:
                active_cells.append((c, int(day["weekday"])))

    # Sort primarily left-to-right; greedy nearest-neighbor keeps path compact and natural
    remaining = set(active_cells)
    path: list[tuple[int, int]] = [(0, 3)]
    visited_at: dict[tuple[int, int], int] = {}

    def walk_to(target: tuple[int, int]) -> None:
        cx, cy = path[-1]
        tx, ty = target
        while cx != tx:
            cx += 1 if tx > cx else -1
            path.append((cx, cy))
            if (cx, cy) in remaining:
                remaining.remove((cx, cy))
                visited_at[(cx, cy)] = len(path) - 1
        while cy != ty:
            cy += 1 if ty > cy else -1
            path.append((cx, cy))
            if (cx, cy) in remaining:
                remaining.remove((cx, cy))
                visited_at[(cx, cy)] = len(path) - 1

    # Start by sweeping gently from left margin into the first active region
    while remaining:
        cx, cy = path[-1]
        nxt = min(remaining, key=lambda p: (abs(p[0] - cx) * 1.4 + abs(p[1] - cy), p[0], p[1]))
        walk_to(nxt)

    # Exit cleanly along the right edge so the loop feels seamless
    walk_to((num_cols - 1, 3))
    return path, visited_at


def render_snake_svg(data: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    weeks = data["weeks"]
    num_cols = len(weeks)
    pitch = 15.6
    cell = 11.6
    grid_w = num_cols * pitch - (pitch - cell)
    origin_x = (900.0 - grid_w) / 2.0
    origin_y = 58.0

    path, visited_at = _build_snake_path(weeks)
    total_steps = max(1, len(path) - 1)
    duration = 14.0

    # Keyframes for 5 snake segments (head + 4 trailing body pieces)
    kf_defs = []
    base_rules = []
    anim_rules = []
    seg_rects = []
    seg_sizes = [12.0, 11.0, 10.0, 8.8, 7.6]
    for s_idx, color in enumerate(t["snake"]):
        sz = seg_sizes[s_idx]
        pad = (cell - sz) / 2.0
        frames = []
        for step_idx in range(len(path)):
            p_idx = max(0, step_idx - s_idx)
            gx, gy = path[p_idx]
            tx = origin_x + gx * pitch + pad
            ty = origin_y + gy * pitch + pad
            pct = (step_idx / total_steps) * 96.0
            frames.append(f"{pct:.2f}%{{transform:translate({tx:.1f}px,{ty:.1f}px)}}")
        last_gx, last_gy = path[-1]
        lx = origin_x + last_gx * pitch + pad
        ly = origin_y + last_gy * pitch + pad
        frames.append(f"100%{{transform:translate({lx:.1f}px,{ly:.1f}px)}}")
        kf_name = f"snk-{theme_name}-{s_idx}"
        kf_defs.append(f"@keyframes {kf_name}{{{''.join(frames)}}}")
        r_gx, r_gy = path[max(0, len(path) - 1 - s_idx)]
        rx0 = origin_x + r_gx * pitch + pad
        ry0 = origin_y + r_gy * pitch + pad
        base_rules.append(f".seg-{s_idx}{{transform:translate({rx0:.1f}px,{ry0:.1f}px);}}")
        anim_rules.append(
            f".seg-{s_idx}{{animation:{kf_name} {duration:.1f}s linear infinite;}}"
        )
        seg_rects.append(
            f'    <rect class="seg-{s_idx}" x="0" y="0" width="{sz:.1f}" height="{sz:.1f}" rx="3" fill="{color}" />'
        )

    # Render real 52x7 grid cells and animate eaten active cells
    cell_svgs = []
    eat_idx = 0
    for c, week in enumerate(weeks):
        for day in week["contributionDays"]:
            r = int(day["weekday"])
            lvl = day["contributionLevel"]
            fill_color = t["levels"].get(lvl, t["levels"]["NONE"])
            cx = origin_x + c * pitch
            cy = origin_y + r * pitch
            pos = (c, r)
            if pos in visited_at:
                step_i = visited_at[pos]
                hit_pct = (step_i / total_steps) * 96.0
                pre_pct = max(0.0, hit_pct - 0.6)
                cls = f"eat-{eat_idx}"
                kf = f"ekf-{theme_name}-{eat_idx}"
                eat_idx += 1
                kf_defs.append(
                    f"@keyframes {kf}{{0%,{pre_pct:.2f}%{{fill:{fill_color}}}{hit_pct:.2f}%,96.5%{{fill:{t['levels']['NONE']}}}100%{{fill:{fill_color}}}}}"
                )
                anim_rules.append(f".{cls}{{animation:{kf} {duration:.1f}s linear infinite;}}")
                cell_svgs.append(
                    f'    <rect class="{cls}" x="{cx:.1f}" y="{cy:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="2.5" fill="{fill_color}" />'
                )
            else:
                cell_svgs.append(
                    f'    <rect x="{cx:.1f}" y="{cy:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="2.5" fill="{fill_color}" />'
                )

    # Legend swatches
    legend_levels = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
    legend_svg = []
    lx = 772.0
    for lvl in legend_levels:
        legend_svg.append(
            f'  <rect x="{lx:.0f}" y="22" width="11" height="11" rx="2.5" fill="{t["levels"][lvl]}" />'
        )
        lx += 14.5

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 186" width="900" height="186" role="img" aria-labelledby="snk-t-{theme_name} snk-d-{theme_name}">
  <title id="snk-t-{theme_name}">Animated Contribution Graph for {USERNAME}</title>
  <desc id="snk-d-{theme_name}">Real 52-week GitHub contribution grid with an animated emerald snake traversing active contribution days.</desc>
  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
    {chr(10).join(base_rules)}
    {chr(10).join(kf_defs)}
    @media (prefers-reduced-motion: no-preference) {{
      {chr(10).join(anim_rules)}
    }}
    @media (prefers-reduced-motion: reduce) {{
      .snake-layer {{ opacity: 0.25; }}
    }}
  </style>
  <rect x="1" y="1" width="898" height="184" rx="12" fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="1.2" />
  <text x="24" y="32" class="sans" font-size="14.5" font-weight="700" fill="{t["ink"]}">Contribution Graph</text>
  <text x="172" y="32" class="mono" font-size="11.5" fill="{t["ink_muted"]}">{data["total_contributions"]} contributions  ·  {data["active_days"]} active days</text>
  <text x="764" y="31" text-anchor="end" class="mono" font-size="10.5" fill="{t["ink_muted"]}">Less</text>
{chr(10).join(legend_svg)}
  <text x="850" y="31" class="mono" font-size="10.5" fill="{t["ink_muted"]}">More</text>
  <line x1="24" y1="44" x2="876" y2="44" stroke="{t["divider"]}" stroke-width="1" />

  <g aria-hidden="true">
{chr(10).join(cell_svgs)}
  </g>
  <g class="snake-layer" aria-hidden="true">
{chr(10).join(reversed(seg_rects))}
  </g>
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
                (f"snake{sfx}.svg", render_snake_svg(data, theme_name)),
            ]
        )

    for filename, svg_text in outputs:
        ET.fromstring(svg_text)  # Validate well-formed XML before writing
        target = OUT_DIR / filename
        target.write_text(svg_text, encoding="utf-8")
        print(f"Wrote {target.relative_to(REPO_ROOT)} ({len(svg_text)} bytes)")


if __name__ == "__main__":
    main()
