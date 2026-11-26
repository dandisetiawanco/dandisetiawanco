"""Idempotent marker-based README updater preserving all curated prose."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Any


def _replace_managed_block(content: str, marker_key: str, replacement: str) -> str:
    start_tag = f"<!-- DYNAMIC:{marker_key}:START -->"
    end_tag = f"<!-- DYNAMIC:{marker_key}:END -->"
    pattern = re.compile(
        re.escape(start_tag) + r".*?" + re.escape(end_tag),
        flags=re.DOTALL,
    )
    if not pattern.search(content):
        raise ValueError(f"Missing managed README markers for {marker_key}")
    new_block = f"{start_tag}\n{replacement.strip()}\n{end_tag}"
    return pattern.sub(lambda _: new_block, content, count=1)


def _fmt_date(iso_ts: str) -> str:
    if not iso_ts or len(iso_ts) < 10:
        return "n/a"
    return iso_ts[:10]


def _clean_text(text: str) -> str:
    """Normalize whitespace and replace em dashes cleanly per anti-slop R-02."""
    clean = re.sub(r"\s*\u2014\s*", ": ", str(text or ""))
    clean = re.sub(r"\s+--\s+", ", ", clean).replace("|", "/")
    return " ".join(clean.split())


def _truncate_words(text: str, max_len: int) -> str:
    clean = _clean_text(text)
    if len(clean) <= max_len:
        return clean
    clipped = clean[: max_len - 3]
    if " " in clipped:
        clipped = clipped.rsplit(" ", 1)[0]
    return clipped.rstrip(" ,;:-") + "..."


def _esc_html(text: str) -> str:
    return html.escape(_clean_text(text), quote=True)


def _build_featured_block(config: dict[str, Any], data: dict[str, Any]) -> str:
    repo_map = {r["name"].lower(): r for r in data.get("repos", [])}
    featured = config.get("featured_projects", [])

    def repo_meta_html(item: dict[str, Any]) -> str:
        live = repo_map.get(item["repo"].lower(), {})
        url = live.get("url") or f"https://github.com/{config['username']}/{item['repo']}"
        stars = int(live.get("stars") or 0)
        pushed = _fmt_date(live.get("pushed_at", ""))
        lic = live.get("license") or ""
        parts = [f'<a href="{url}"><strong>{_esc_html(item["display_name"])}</strong></a>']
        if item.get("status"):
            parts.append(_esc_html(item["status"]))
        if lic and lic != "NOASSERTION":
            parts.append(_esc_html(lic))
        if stars > 0:
            parts.append(f"{stars} {'star' if stars == 1 else 'stars'}")
        if live.get("homepage"):
            parts.append(f'<a href="{live["homepage"]}">Live Demo</a>')
        if pushed != "n/a":
            parts.append(f"Updated {pushed}")
        stack_inline = " ".join(f"<code>{_esc_html(s)}</code>" for s in item["stack"])
        return (
            f"{' · '.join(parts)}<br />\n"
            f"  {_esc_html(item['summary'])}<br />\n"
            f"  {stack_inline}"
        )

    def picture_link(item: dict[str, Any], width: str, height: str) -> str:
        live = repo_map.get(item["repo"].lower(), {})
        url = live.get("url") or f"https://github.com/{config['username']}/{item['repo']}"
        slug = item["slug"]
        alt = _esc_html(f"{item['display_name']}: {item['summary']}")
        return (
            f'<a href="{url}">'
            f"<picture>"
            f'<source media="(prefers-color-scheme: dark)" srcset="./assets/projects/{slug}-dark.svg" />'
            f'<source media="(prefers-color-scheme: light)" srcset="./assets/projects/{slug}-light.svg" />'
            f'<img alt="{alt}" src="./assets/projects/{slug}-dark.svg" width="{width}" height="{height}" />'
            f"</picture>"
            f"</a>"
        )

    by_slug = {p["slug"]: p for p in featured}
    lines: list[str] = []

    if "agentos" in by_slug:
        item = by_slug["agentos"]
        lines.append(f'<div align="center">\n  {picture_link(item, "920", "310")}\n</div>\n')
        lines.append(f"<p>\n  {repo_meta_html(item)}\n</p>\n")

    if "omnidesk" in by_slug:
        item = by_slug["omnidesk"]
        lines.append(f'<div align="center">\n  {picture_link(item, "920", "296")}\n</div>\n')
        lines.append(f"<p>\n  {repo_meta_html(item)}\n</p>\n")

    if "ledger" in by_slug and "talentos" in by_slug:
        left = by_slug["ledger"]
        right = by_slug["talentos"]
        lines.append(
            "<table>\n"
            "  <tr>\n"
            f'    <td valign="top" width="50%">\n'
            f'      {picture_link(left, "448", "320")}<br /><br />\n'
            f"      {repo_meta_html(left)}\n"
            "    </td>\n"
            f'    <td valign="top" width="50%">\n'
            f'      {picture_link(right, "448", "320")}<br /><br />\n'
            f"      {repo_meta_html(right)}\n"
            "    </td>\n"
            "  </tr>\n"
            "</table>\n"
        )

    if "infraos" in by_slug:
        item = by_slug["infraos"]
        lines.append(f'<div align="center">\n  {picture_link(item, "920", "210")}\n</div>\n')
        lines.append(f"<p>\n  {repo_meta_html(item)}\n</p>\n")

    supporting_rows: list[str] = []
    for sp in config.get("supporting_projects", []):
        live = repo_map.get(sp["repo"].lower())
        if not live:
            continue
        url = live["url"]
        live_demo = f' · <a href="{live["homepage"]}">Live</a>' if live.get("homepage") else ""
        stack_tags = " ".join(f"<code>{_esc_html(t)}</code>" for t in sp["stack"])
        supporting_rows.append(
            f'    <a href="{url}"><strong>{_esc_html(sp["display_name"])}</strong></a>{live_demo}: '
            f'{_esc_html(sp["summary"])} · {stack_tags}'
        )

    if supporting_rows:
        lines.append(
            "<details>\n"
            "  <summary><strong>Additional Verified Public Repositories</strong></summary>\n\n"
            "  <p>\n"
            + "<br />\n".join(supporting_rows)
            + "\n  </p>\n"
            "</details>"
        )

    return "\n".join(lines)


def _build_recently_shipped_block(config: dict[str, Any], data: dict[str, Any]) -> str:
    recent = data.get("recent_feed", [])
    releases = data.get("latest_releases", [])

    parts: list[str] = [
        '<div align="center">',
        "  <picture>",
        '    <source media="(prefers-color-scheme: dark)" srcset="./assets/analytics/recent-pulse-dark.svg" />',
        '    <source media="(prefers-color-scheme: light)" srcset="./assets/analytics/recent-pulse-light.svg" />',
        '    <img alt="Live public repository activity timeline across recently updated repositories" src="./assets/analytics/recent-pulse-dark.svg" width="920" height="138" />',
        "  </picture>",
        "</div>",
        "",
    ]

    if not recent:
        parts.append("_No recent public development activity recorded in this sync window._")
        return "\n".join(parts)

    parts.append("| Repository | Summary | Language | Latest Activity | Updated |")
    parts.append("| :--- | :--- | :--- | :--- | :--- |")

    curated_desc = {
        p["repo"].lower(): p["summary"]
        for p in config.get("featured_projects", []) + config.get("supporting_projects", [])
    }

    for repo in recent:
        name = repo["name"]
        url = repo["url"]
        raw_desc = (repo.get("description") or "").strip()
        if not raw_desc or raw_desc.isupper():
            raw_desc = curated_desc.get(name.lower()) or raw_desc.title() or "Public engineering repository."
        desc = _truncate_words(raw_desc, 96)
        lang = repo.get("language") or "Multi"

        commit = (repo.get("recent_commits") or [None])[0]
        release = repo.get("latest_release")
        if release and release.get("tag"):
            activity = f'[Release `{release["tag"]}`]({release["url"]})'
        elif commit:
            msg = _truncate_words(commit["message"], 52)
            activity = f'[`{commit["sha"]}`]({commit["url"]}) {msg}'
        else:
            activity = "Public repository update"

        updated = _fmt_date(repo.get("pushed_at") or repo.get("updated_at") or "")
        star_note = f" ({repo['stars']} {'star' if repo['stars'] == 1 else 'stars'})" if repo.get("stars", 0) > 0 else ""
        parts.append(f"| [**{name}**]({url}){star_note} | {desc} | `{lang}` | {activity} | `{updated}` |")

    if releases:
        rel_items = [
            f'[**{r["repo"]} {r["tag"]}**]({r["url"]}) (`{_fmt_date(r["published_at"])}`)'
            for r in releases[:3]
        ]
        parts.append("")
        parts.append(f"Latest public releases: {' · '.join(rel_items)}")

    return "\n".join(parts)


def _build_analytics_footer_block(data: dict[str, Any]) -> str:
    stats = data.get("stats", {})
    updated = _esc_html(data.get("generated_at_utc") or data.get("updated_date_utc") or "pending")
    return (
        f"<sub>Scope: public GitHub data across {stats.get('public_repos', 0)} owned non-fork repositories "
        f"({stats.get('total_contributions', 0)} trailing 52-week public contributions, "
        f"{stats.get('public_commits', 0)} public commits, {stats.get('total_stars', 0)} stars). "
        f"Private repository data is excluded. Last verified sync: <code>{updated}</code>.</sub>"
    )


def update_readme(readme_path: Path, config: dict[str, Any], data: dict[str, Any]) -> bool:
    """Update managed dynamic blocks in README.md and return True if content changed."""
    original = readme_path.read_text(encoding="utf-8")
    updated = original
    updated = _replace_managed_block(updated, "FEATURED_PROJECTS", _build_featured_block(config, data))
    updated = _replace_managed_block(updated, "RECENTLY_SHIPPED", _build_recently_shipped_block(config, data))
    updated = _replace_managed_block(updated, "ANALYTICS_FOOTER", _build_analytics_footer_block(data))

    if updated != original:
        readme_path.write_text(updated, encoding="utf-8")
        return True
    return False
