#!/usr/bin/env python3
"""Generate repository-hosted animated GitHub analytics & contribution ribbon SVGs.

Uses only the Python 3 standard library and real GitHub public profile, GraphQL,
and REST API data. All metrics strictly reflect public GitHub activity so local
runs and GitHub Actions runs report identical counts matching github.com/<username>.
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
        "bg": "#0B0F14",
        "bg_end": "#0E1715",
        "card_inner": "#111820",
        "card_active": "#12241F",
        "border": "#23342E",
        "border_active": "#2D5E4E",
        "divider": "#1B2825",
        "ink": "#F8FAFC",
        "ink_sec": "#CBD5E1",
        "ink_muted": "#94A3B8",
        "accent_text": "#34D399",
        "line_stroke": "#10B981",
        "pulse_stroke": "#6EE7B7",
        "dot_fill": "#34D399",
        "area_top": "#10B981",
        "grid_line": "#172224",
        "ribbon_idle": "#1C2B28",
        "ribbon_low": "#059669",
        "ribbon_high": "#34D399",
        "lang_colors": ["#34D399", "#10B981", "#6EE7B7", "#059669", "#94A3B8", "#4E6860"],
    },
    "light": {
        "suffix": "-light",
        "bg": "#FFFFFF",
        "bg_end": "#F6FAF8",
        "card_inner": "#F8FBFA",
        "card_active": "#ECFDF5",
        "border": "#CBD8D3",
        "border_active": "#6EE7B7",
        "divider": "#DCE6E2",
        "ink": "#0F1715",
        "ink_sec": "#2E3A36",
        "ink_muted": "#566560",
        "accent_text": "#047857",
        "line_stroke": "#059669",
        "pulse_stroke": "#10B981",
        "dot_fill": "#047857",
        "area_top": "#059669",
        "grid_line": "#E5EFEA",
        "ribbon_idle": "#DCE8E3",
        "ribbon_low": "#10B981",
        "ribbon_high": "#047857",
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
    anim_css = []
    for idx, (label, value) in enumerate(metrics):
        col = idx % 3
        row = idx // 3
        x = 20 + col * 136
        y = 58 + row * 70
        delay = idx * 1.4
        val_fill = t["accent_text"] if idx in (0, 4) else t["ink"]
        anim_css.append(
            f".mc-{idx} {{ animation: statCycle 8.4s ease-in-out {delay:.1f}s infinite; }}"
        )
        accent_line = (
            f'    <rect class="k-bar" x="{x + 12}" y="{y + 52}" width="32" height="2" rx="1" fill="{t["line_stroke"]}" />\n'
            if idx in (0, 4)
            else ""
        )
        cells.append(
            f"  <g>\n"
            f'    <rect class="mc-{idx}" x="{x}" y="{y}" width="128" height="60" rx="8" fill="{t["card_inner"]}" stroke="{t["divider"]}" stroke-width="1" />\n'
            f'    <text x="{x + 12}" y="{y + 25}" class="mono" font-size="18.5" font-weight="700" fill="{val_fill}">{html.escape(value)}</text>\n'
            f'    <text x="{x + 12}" y="{y + 43}" class="sans" font-size="10.8" font-weight="500" fill="{t["ink_sec"]}">{html.escape(label)}</text>\n'
            f"{accent_line}"
            f"  </g>"
        )

    grad_id = f"st-bg-{theme_name}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 212" width="440" height="212" role="img" aria-labelledby="stats-t-{theme_name} stats-d-{theme_name}">
  <title id="stats-t-{theme_name}">GitHub Statistics for {USERNAME} (Public Scope)</title>
  <desc id="stats-d-{theme_name}">Public GitHub metrics over the trailing 12 months: {data['total_contributions']} public contributions, {data['public_repos']} public repositories, {data['public_commits']} public commits.</desc>
  <defs>
    <linearGradient id="{grad_id}" x1="0" y1="0" x2="440" y2="212" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["bg"]}" />
      <stop offset="100%" stop-color="{t["bg_end"]}" />
    </linearGradient>
  </defs>
  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
    @media (prefers-reduced-motion: no-preference) {{
      {chr(10).join("      " + r for r in anim_css)}
      .k-bar {{ animation: barPulse 4.2s ease-in-out infinite; }}
    }}
    @keyframes statCycle {{
      0%, 16%  {{ stroke: {t["border_active"]}; fill: {t["card_active"]}; }}
      24%, 100%{{ stroke: {t["divider"]}; fill: {t["card_inner"]}; }}
    }}
    @keyframes barPulse {{
      0%, 100% {{ opacity: 0.75; width: 24px; }}
      50%      {{ opacity: 1; width: 46px; }}
    }}
  </style>
  <rect x="0.75" y="0.75" width="438.5" height="210.5" rx="12" fill="url(#{grad_id})" stroke="{t["border"]}" stroke-width="1.2" />
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
    sw_css = []
    for idx, item in enumerate(langs):
        col = idx % 2
        row = idx // 2
        x = 20 + col * 210
        y = 106 + row * 33
        delay = idx * 1.1
        color = t["lang_colors"][idx % len(t["lang_colors"])]
        sw_css.append(
            f".sw-{idx} {{ animation: swPulse 6.6s ease-in-out {delay:.1f}s infinite; transform-origin: {x + 5}px {y - 5}px; }}"
        )
        legend_parts.append(
            f"  <g>\n"
            f'    <rect class="sw-{idx}" x="{x}" y="{y - 10}" width="10" height="10" rx="2.5" fill="{color}" />\n'
            f'    <text x="{x + 18}" y="{y}" class="sans" font-size="13" font-weight="600" fill="{t["ink"]}">{html.escape(item["name"])}</text>\n'
            f'    <text x="{x + 186}" y="{y}" text-anchor="end" class="mono" font-size="12" fill="{t["ink_sec"]}">{item["pct"]:.1f}%</text>\n'
            f"  </g>"
        )

    clip_id = f"lang-bar-{theme_name}"
    grad_id = f"lg-bg-{theme_name}"
    sheen_id = f"lg-sheen-{theme_name}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 212" width="440" height="212" role="img" aria-labelledby="langs-t-{theme_name} langs-d-{theme_name}">
  <title id="langs-t-{theme_name}">Most-Used Languages for {USERNAME}</title>
  <desc id="langs-d-{theme_name}">Programming language distribution across owned non-fork public GitHub repositories.</desc>
  <defs>
    <linearGradient id="{grad_id}" x1="0" y1="0" x2="440" y2="212" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["bg"]}" />
      <stop offset="100%" stop-color="{t["bg_end"]}" />
    </linearGradient>
    <linearGradient id="{sheen_id}" x1="0" y1="0" x2="110" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0" />
      <stop offset="50%" stop-color="#FFFFFF" stop-opacity="0.34" />
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0" />
    </linearGradient>
    <clipPath id="{clip_id}">
      <rect x="20" y="60" width="400" height="10" rx="5" />
    </clipPath>
  </defs>
  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
    .bar-sheen {{ opacity: 0; }}
    @media (prefers-reduced-motion: no-preference) {{
      .bar-sheen {{ animation: sheenPass 6.6s cubic-bezier(0.4, 0, 0.2, 1) infinite; }}
      {chr(10).join("      " + r for r in sw_css)}
    }}
    @keyframes sheenPass {{
      0%        {{ transform: translateX(-90px); opacity: 0; }}
      15%, 75%  {{ opacity: 1; }}
      92%, 100% {{ transform: translateX(440px); opacity: 0; }}
    }}
    @keyframes swPulse {{
      0%, 16%  {{ transform: scale(1.22); }}
      26%, 100%{{ transform: scale(1); }}
    }}
  </style>
  <rect x="0.75" y="0.75" width="438.5" height="210.5" rx="12" fill="url(#{grad_id})" stroke="{t["border"]}" stroke-width="1.2" />
  <text x="20" y="32" class="sans" font-size="14.5" font-weight="700" fill="{t["ink"]}">Most-Used Languages</text>
  <text x="420" y="31.5" text-anchor="end" class="mono" font-size="10.8" fill="{t["ink_muted"]}">Owned public repos</text>
  <line x1="20" y1="45" x2="420" y2="45" stroke="{t["divider"]}" stroke-width="1" />
  <rect x="20" y="60" width="400" height="10" rx="5" fill="{t["card_inner"]}" />
  <g clip-path="url(#{clip_id})">
{chr(10).join(bar_parts)}
    <rect class="bar-sheen" x="20" y="60" width="110" height="10" fill="url(#{sheen_id})" />
  </g>
{chr(10).join(legend_parts)}
</svg>
"""


def _smooth_spline_path(pts: list[tuple[float, float]], baseline_y: float) -> tuple[str, str]:
    if not pts:
        return "", ""
    if len(pts) == 1:
        x, y = pts[0]
        return f"M {x:.1f} {y:.1f}", f"M {x:.1f} {baseline_y:.1f} L {x:.1f} {y:.1f} Z"

    segs = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        cx1 = x0 + (x1 - x0) * 0.42
        cx2 = x1 - (x1 - x0) * 0.42
        segs.append(f"C {cx1:.1f} {y0:.1f}, {cx2:.1f} {y1:.1f}, {x1:.1f} {y1:.1f}")
    curve = " ".join(segs)
    area = (
        f"M {pts[0][0]:.1f} {baseline_y:.1f} L {pts[0][0]:.1f} {pts[0][1]:.1f} "
        + " ".join(segs[1:])
        + f" L {pts[-1][0]:.1f} {baseline_y:.1f} Z"
    )
    return curve, area


def render_activity_svg(data: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    weekly = data["weekly_totals"]
    max_val = max((w["count"] for w in weekly), default=1)
    max_scale = max(4, ((max_val + 3) // 4) * 4)

    chart_x, chart_y, chart_w, chart_h = 48.0, 58.0, 824.0, 92.0
    n = max(1, len(weekly) - 1)

    points: list[tuple[float, float, int, str]] = []
    for i, item in enumerate(weekly):
        px = chart_x + (i / n) * chart_w
        py = chart_y + chart_h - (item["count"] / max_scale) * chart_h
        points.append((px, py, item["count"], item["first_day"]))

    curve_path, area_path = _smooth_spline_path([(x, y) for x, y, _, _ in points], chart_y + chart_h)

    grid_svg = []
    for frac in (0.0, 0.5, 1.0):
        gy = chart_y + chart_h - frac * chart_h
        gval = int(round(frac * max_scale))
        grid_svg.append(
            f'  <line x1="{chart_x:.0f}" y1="{gy:.1f}" x2="{chart_x + chart_w:.0f}" y2="{gy:.1f}" stroke="{t["grid_line"]}" stroke-width="1" />\n'
            f'  <text x="{chart_x - 10:.0f}" y="{gy + 3.5:.1f}" text-anchor="end" class="mono" font-size="10" fill="{t["ink_muted"]}">{gval}</text>'
        )

    dot_svg = []
    dot_css = []
    d_idx = 0
    for idx, (px, py, cnt, _) in enumerate(points):
        if cnt > 0:
            delay = (idx / n) * 5.2
            dot_css.append(
                f".pt-{d_idx} {{ animation: dotBeacon 6s ease-in-out {delay:.2f}s infinite; transform-origin: {px:.1f}px {py:.1f}px; }}"
            )
            dot_svg.append(
                f'  <circle class="pt-{d_idx}" cx="{px:.1f}" cy="{py:.1f}" r="3.4" fill="{t["dot_fill"]}" stroke="{t["bg"]}" stroke-width="1.3" />'
            )
            d_idx += 1

    ribbon_cy = 232.0
    ribbon_bars = []
    active_clip_rects = []
    bar_w = 5.4
    for idx, (px, _, cnt, _) in enumerate(points):
        bx = px - bar_w / 2.0
        if cnt > 0:
            norm = cnt / max(1, max_val)
            half_h = 5.0 + norm * 17.0
            by = ribbon_cy - half_h
            bh = half_h * 2.0
            fill = t["ribbon_high"] if norm >= 0.45 else t["ribbon_low"]
            opacity = 0.58 + 0.42 * norm
            ribbon_bars.append(
                f'    <rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" rx="2.5" fill="{fill}" fill-opacity="{opacity:.2f}" />'
            )
            active_clip_rects.append(
                f'      <rect x="{bx:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" rx="2.5" />'
            )
        else:
            ribbon_bars.append(
                f'    <rect x="{bx:.1f}" y="{ribbon_cy - 2.5:.1f}" width="{bar_w:.1f}" height="5" rx="2" fill="{t["ribbon_idle"]}" />'
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
                    f'  <text x="{px:.1f}" y="274" class="mono" font-size="10" fill="{t["ink_muted"]}">{label}</text>'
                )
                last_label_x = px

    bg_id = f"act-bg-{theme_name}"
    grad_id = f"act-grad-{theme_name}"
    wave_id = f"rib-wave-{theme_name}"
    rclip_id = f"rib-clip-{theme_name}"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 292" width="900" height="292" role="img" aria-labelledby="act-t-{theme_name} act-d-{theme_name}">
  <title id="act-t-{theme_name}">Weekly Public Contribution Activity and Impulse Ribbon for {USERNAME}</title>
  <desc id="act-d-{theme_name}">Animated 52-week public contribution curve and chronological impulse data ribbon totaling {data["total_contributions"]} public contributions with peak {max_val} per week.</desc>
  <defs>
    <linearGradient id="{bg_id}" x1="0" y1="0" x2="900" y2="292" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["bg"]}" />
      <stop offset="100%" stop-color="{t["bg_end"]}" />
    </linearGradient>
    <linearGradient id="{grad_id}" x1="0" y1="58" x2="0" y2="150" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["area_top"]}" stop-opacity="0.26" />
      <stop offset="100%" stop-color="{t["area_top"]}" stop-opacity="0.01" />
    </linearGradient>
    <linearGradient id="{wave_id}" x1="0" y1="0" x2="180" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0" />
      <stop offset="50%" stop-color="#6EE7B7" stop-opacity="0.95" />
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0" />
    </linearGradient>
    <clipPath id="{rclip_id}">
{chr(10).join(active_clip_rects)}
    </clipPath>
  </defs>
  <style>
    .sans {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif; }}
    .mono {{ font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
    .curve-pulse, .rib-scan {{ opacity: 0; }}
    @media (prefers-reduced-motion: no-preference) {{
      .curve-pulse {{
        opacity: 1;
        stroke-dasharray: 110 890;
        animation: traceSpline 6s cubic-bezier(0.4, 0, 0.2, 1) infinite;
      }}
      .rib-scan {{
        animation: scanRibbon 6s cubic-bezier(0.4, 0, 0.2, 1) infinite;
      }}
      {chr(10).join("      " + r for r in dot_css)}
    }}
    @keyframes traceSpline {{
      0%   {{ stroke-dashoffset: 1000; opacity: 0; }}
      10%  {{ opacity: 1; }}
      88%  {{ opacity: 1; }}
      100% {{ stroke-dashoffset: 0; opacity: 0; }}
    }}
    @keyframes dotBeacon {{
      0%, 14%  {{ transform: scale(1.38); }}
      26%, 100%{{ transform: scale(1); }}
    }}
    @keyframes scanRibbon {{
      0%        {{ transform: translateX(-160px); opacity: 0; }}
      12%, 82%  {{ opacity: 0.9; }}
      96%, 100% {{ transform: translateX(880px); opacity: 0; }}
    }}
  </style>

  <rect x="0.75" y="0.75" width="898.5" height="290.5" rx="12" fill="url(#{bg_id})" stroke="{t["border"]}" stroke-width="1.2" />
  <text x="24" y="32" class="sans" font-size="14.5" font-weight="700" fill="{t["ink"]}">Weekly Contribution Activity</text>
  <text x="876" y="31.5" text-anchor="end" class="mono" font-size="10.8" fill="{t["ink_muted"]}">{data["total_contributions"]} public  ·  Peak {max_val}/wk  ·  Trailing 52 weeks</text>
  <line x1="24" y1="45" x2="876" y2="45" stroke="{t["divider"]}" stroke-width="1" />

{chr(10).join(grid_svg)}
  <path d="{area_path}" fill="url(#{grad_id})" />
  <path d="{curve_path}" fill="none" stroke="{t["line_stroke"]}" stroke-width="2" stroke-linecap="round" />
  <path class="curve-pulse" pathLength="1000" d="{curve_path}" fill="none" stroke="{t["pulse_stroke"]}" stroke-width="2.6" stroke-linecap="round" />
{chr(10).join(dot_svg)}

  <line x1="24" y1="172" x2="876" y2="172" stroke="{t["divider"]}" stroke-width="1" />
  <text x="24" y="192" class="mono" font-size="10" font-weight="600" fill="{t["accent_text"]}">CONTRIBUTION IMPULSE RIBBON</text>
  <text x="876" y="192" text-anchor="end" class="mono" font-size="10" fill="{t["ink_muted"]}">52-week amplitude spectrum · {data["active_days"]} active days</text>

  <line x1="{chart_x:.0f}" y1="{ribbon_cy:.1f}" x2="{chart_x + chart_w:.0f}" y2="{ribbon_cy:.1f}" stroke="{t["grid_line"]}" stroke-width="1" />
  <g aria-hidden="true">
{chr(10).join(ribbon_bars)}
  </g>
  <g clip-path="url(#{rclip_id})" aria-hidden="true">
    <rect class="rib-scan" x="30" y="204" width="180" height="56" fill="url(#{wave_id})" />
  </g>

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
