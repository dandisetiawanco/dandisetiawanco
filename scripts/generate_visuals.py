"""Original animated SVG asset generators for dark and light GitHub themes."""

from __future__ import annotations

import datetime as dt
import math
from pathlib import Path
from typing import Any

from theme_tokens import FONT_MONO, FONT_SANS, THEMES, esc, lang_color, truncate, validate_svg


def _accent_pair(t: dict[str, Any], name: str) -> tuple[str, str, str]:
    """Return (stroke/fill accent, high-contrast text accent, soft tint) for a domain."""
    mapping = {
        "emerald": (t["emerald"], t["emerald_text"], t["surface_tint_emerald"]),
        "cyan": (t["cyan"], t["cyan_text"], t["surface_tint_cyan"]),
        "violet": (t["violet"], t["violet_text"], t["surface_tint_violet"]),
        "amber": (t["amber"], t["amber_text"], t["surface_tint_amber"]),
    }
    return mapping.get(name, mapping["emerald"])


def render_hero(config: dict[str, Any], data: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    ident = config["identity"]
    stats = data.get("stats", {})
    updated = data.get("updated_date_utc", "")
    repo_count = stats.get("public_repos", 0)
    is_dark = theme_name == "dark"

    grid_lines: list[str] = []
    for gx in range(520, 920, 36):
        grid_lines.append(
            f'      <line x1="{gx}" y1="16" x2="{gx}" y2="332" stroke="{t["grid"]}" stroke-width="1" />'
        )
    for gy in range(36, 332, 36):
        grid_lines.append(
            f'      <line x1="504" y1="{gy}" x2="908" y2="{gy}" stroke="{t["grid"]}" stroke-width="1" />'
        )

    # Architectural crosshair ticks at key topology coordinates.
    ticks: list[str] = []
    for tx, ty in ((556, 72), (844, 72), (556, 288), (844, 288), (700, 180)):
        ticks.append(
            f'      <path d="M {tx - 5} {ty} L {tx + 5} {ty} M {tx} {ty - 5} L {tx} {ty + 5}" '
            f'stroke="{t["border_strong"]}" stroke-width="1" />'
        )

    plane_fill = "#162430" if is_dark else "#FFFFFF"
    plane_fill_2 = "#13212D" if is_dark else "#F8FAFC"
    hub_fill = "#13232D" if is_dark else "#FFFFFF"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 348" width="920" height="348" role="img" aria-labelledby="hero-t-{theme_name} hero-d-{theme_name}">
  <title id="hero-t-{theme_name}">{esc(ident["name"])}: {esc(ident["role"])}</title>
  <desc id="hero-d-{theme_name}">{esc(ident["statement"])}</desc>
  <defs>
    <linearGradient id="hero-bg-{theme_name}" x1="0" y1="0" x2="920" y2="348" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["canvas"]}" />
      <stop offset="100%" stop-color="{t["canvas_alt"]}" />
    </linearGradient>
    <linearGradient id="hero-rule-{theme_name}" x1="44" y1="0" x2="454" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["emerald"]}" />
      <stop offset="52%" stop-color="{t["cyan"]}" />
      <stop offset="100%" stop-color="{t["violet"]}" stop-opacity="0.45" />
    </linearGradient>
    <linearGradient id="hero-spine-{theme_name}" x1="0" y1="0" x2="0" y2="120" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["cyan"]}" stop-opacity="0" />
      <stop offset="50%" stop-color="{t["emerald"]}" stop-opacity="0.95" />
      <stop offset="100%" stop-color="{t["violet"]}" stop-opacity="0" />
    </linearGradient>
    <clipPath id="hero-clip-{theme_name}">
      <rect x="0.75" y="0.75" width="918.5" height="346.5" rx="16" />
    </clipPath>
    <clipPath id="hero-name-mask-{theme_name}">
      <rect x="40" y="64" width="440" height="66" />
    </clipPath>
    <clipPath id="hero-role-mask-{theme_name}">
      <rect x="40" y="130" width="440" height="34" />
    </clipPath>
  </defs>
  <style>
    .sans {{ font-family: {FONT_SANS}; }}
    .mono {{ font-family: {FONT_MONO}; }}
    .pkt {{ opacity: 0.92; }}
    @media (prefers-reduced-motion: no-preference) {{
      .reveal-name {{ animation: riseIn 0.75s cubic-bezier(0.16, 1, 0.3, 1) 0.05s both; }}
      .reveal-role {{ animation: riseIn 0.72s cubic-bezier(0.16, 1, 0.3, 1) 0.18s both; }}
      .reveal-copy {{ animation: fadeIn 0.8s ease-out 0.3s both; }}
      .rule-grow {{ transform-origin: 44px 173px; animation: drawX 0.9s cubic-bezier(0.16, 1, 0.3, 1) 0.25s both; }}
      .orbit-cw {{ transform-origin: 706px 176px; animation: spinCW 34s linear infinite; }}
      .orbit-ccw {{ transform-origin: 706px 176px; animation: spinCCW 22s linear infinite; }}
      .bus-e {{ stroke-dasharray: 9 7; animation: dashFwd 2.6s linear infinite; }}
      .bus-c {{ stroke-dasharray: 9 7; animation: dashFwd 2.2s linear infinite; }}
      .bus-v {{ stroke-dasharray: 9 7; animation: dashRev 2.8s linear infinite; }}
      .bus-a {{ stroke-dasharray: 9 7; animation: dashRev 3.1s linear infinite; }}
      .spine-sweep {{ animation: spineDown 7.5s cubic-bezier(0.4, 0, 0.2, 1) infinite; }}
      .float-hub {{ transform-origin: 706px 176px; animation: hubBreathe 8s ease-in-out infinite; }}
      .pkt-c {{ animation: moveC 4.4s cubic-bezier(0.4, 0, 0.2, 1) infinite; }}
      .pkt-v {{ animation: moveV 4.8s cubic-bezier(0.4, 0, 0.2, 1) 0.6s infinite; }}
      .pkt-e {{ animation: moveE 4.6s cubic-bezier(0.4, 0, 0.2, 1) 1.2s infinite; }}
      .pkt-a {{ animation: moveA 5.0s cubic-bezier(0.4, 0, 0.2, 1) 1.8s infinite; }}
      .dom-1 {{ animation: domFocus 12s ease-in-out 0s infinite; }}
      .dom-2 {{ animation: domFocus 12s ease-in-out 3s infinite; }}
      .dom-3 {{ animation: domFocus 12s ease-in-out 6s infinite; }}
      .dom-4 {{ animation: domFocus 12s ease-in-out 9s infinite; }}
    }}
    @keyframes riseIn {{
      from {{ opacity: 0; transform: translateY(28px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; }}
      to   {{ opacity: 1; }}
    }}
    @keyframes drawX {{
      from {{ transform: scaleX(0); opacity: 0; }}
      to   {{ transform: scaleX(1); opacity: 1; }}
    }}
    @keyframes spinCW {{
      from {{ transform: rotate(0deg); }}
      to   {{ transform: rotate(360deg); }}
    }}
    @keyframes spinCCW {{
      from {{ transform: rotate(360deg); }}
      to   {{ transform: rotate(0deg); }}
    }}
    @keyframes dashFwd {{
      from {{ stroke-dashoffset: 32; }}
      to   {{ stroke-dashoffset: 0; }}
    }}
    @keyframes dashRev {{
      from {{ stroke-dashoffset: 0; }}
      to   {{ stroke-dashoffset: 32; }}
    }}
    @keyframes spineDown {{
      0%        {{ transform: translateY(-120px); opacity: 0; }}
      15%, 78%  {{ opacity: 0.9; }}
      95%, 100% {{ transform: translateY(360px); opacity: 0; }}
    }}
    @keyframes hubBreathe {{
      0%, 100% {{ transform: translateY(0px); }}
      50%      {{ transform: translateY(-4px); }}
    }}
    @keyframes moveC {{
      0%   {{ transform: translate(0px, 0px); opacity: 0; }}
      12%  {{ opacity: 1; }}
      40%  {{ transform: translate(0px, 36px); opacity: 1; }}
      88%  {{ opacity: 1; }}
      100% {{ transform: translate(82px, 36px); opacity: 0; }}
    }}
    @keyframes moveV {{
      0%   {{ transform: translate(0px, 0px); opacity: 0; }}
      12%  {{ opacity: 1; }}
      40%  {{ transform: translate(0px, 36px); opacity: 1; }}
      88%  {{ opacity: 1; }}
      100% {{ transform: translate(-85px, 36px); opacity: 0; }}
    }}
    @keyframes moveE {{
      0%   {{ transform: translate(0px, 0px); opacity: 0; }}
      12%  {{ opacity: 1; }}
      40%  {{ transform: translate(0px, -36px); opacity: 1; }}
      88%  {{ opacity: 1; }}
      100% {{ transform: translate(82px, -36px); opacity: 0; }}
    }}
    @keyframes moveA {{
      0%   {{ transform: translate(0px, 0px); opacity: 0; }}
      12%  {{ opacity: 1; }}
      40%  {{ transform: translate(0px, -36px); opacity: 1; }}
      88%  {{ opacity: 1; }}
      100% {{ transform: translate(-85px, -36px); opacity: 0; }}
    }}
    @keyframes domFocus {{
      0%, 22%   {{ opacity: 1; }}
      30%, 100% {{ opacity: 0.58; }}
    }}
  </style>

  <g clip-path="url(#hero-clip-{theme_name})">
    <rect x="0" y="0" width="920" height="348" fill="url(#hero-bg-{theme_name})" />

    <!-- Top architectural 4-domain identity motif -->
    <rect x="44" y="0.75" width="32" height="3" fill="{t["emerald"]}" />
    <rect x="80" y="0.75" width="24" height="3" fill="{t["cyan"]}" />
    <rect x="108" y="0.75" width="20" height="3" fill="{t["violet"]}" />
    <rect x="132" y="0.75" width="16" height="3" fill="{t["amber"]}" />

    <!-- Architectural coordinate grid on right systems canvas -->
    <g aria-hidden="true" opacity="{0.65 if is_dark else 0.72}">
{chr(10).join(grid_lines)}
{chr(10).join(ticks)}
    </g>

    <!-- Editorial vertical partition with travelling vertical signal -->
    <line x1="504" y1="0" x2="504" y2="348" stroke="{t["hairline"]}" stroke-width="1" />
    <rect class="spine-sweep" x="503.25" y="0" width="1.5" height="120" fill="url(#hero-spine-{theme_name})" />

    <!-- Left editorial typography -->
    <text x="44" y="48" class="mono" font-size="10.2" font-weight="600" fill="{t["ink_muted"]}" letter-spacing="0.06em">BANDAR LAMPUNG  ·  {esc(ident["coordinates"])}</text>

    <g clip-path="url(#hero-name-mask-{theme_name})">
      <text x="44" y="114" class="sans reveal-name" font-size="50" font-weight="700" fill="{t["ink"]}" letter-spacing="-0.032em">{esc(ident["name"])}</text>
    </g>

    <g clip-path="url(#hero-role-mask-{theme_name})">
      <text x="44" y="152" class="sans reveal-role" font-size="19.5" font-weight="600" fill="{t["emerald_text"]}" letter-spacing="-0.01em">{esc(ident["role"])}</text>
    </g>

    <line x1="44" y1="173" x2="454" y2="173" stroke="{t["hairline"]}" stroke-width="1.2" />
    <line class="rule-grow" x1="44" y1="173" x2="454" y2="173" stroke="url(#hero-rule-{theme_name})" stroke-width="1.8" />

    <g class="reveal-copy">
      <text x="44" y="206" class="sans" font-size="14.5" font-weight="400" fill="{t["ink_sec"]}">Building intelligent systems, scalable applications,</text>
      <text x="44" y="228" class="sans" font-size="14.5" font-weight="400" fill="{t["ink_sec"]}">and software that solves real problems.</text>
    </g>

    <!-- Four semantic domain index markers matching right topology -->
    <g transform="translate(44, 272)">
      <g class="dom-1">
        <rect x="0" y="0" width="3" height="28" rx="1.5" fill="{t["cyan"]}" />
        <text x="11" y="12" class="mono" font-size="9.5" font-weight="600" fill="{t["cyan_text"]}">01</text>
        <text x="11" y="26" class="sans" font-size="12" font-weight="600" fill="{t["ink"]}">Full-Stack</text>
      </g>
      <g class="dom-2" transform="translate(106, 0)">
        <rect x="0" y="0" width="3" height="28" rx="1.5" fill="{t["violet"]}" />
        <text x="11" y="12" class="mono" font-size="9.5" font-weight="600" fill="{t["violet_text"]}">02</text>
        <text x="11" y="26" class="sans" font-size="12" font-weight="600" fill="{t["ink"]}">AI Agents</text>
      </g>
      <g class="dom-3" transform="translate(208, 0)">
        <rect x="0" y="0" width="3" height="28" rx="1.5" fill="{t["emerald"]}" />
        <text x="11" y="12" class="mono" font-size="9.5" font-weight="600" fill="{t["emerald_text"]}">03</text>
        <text x="11" y="26" class="sans" font-size="12" font-weight="600" fill="{t["ink"]}">Systems</text>
      </g>
      <g class="dom-4" transform="translate(304, 0)">
        <rect x="0" y="0" width="3" height="28" rx="1.5" fill="{t["amber"]}" />
        <text x="11" y="12" class="mono" font-size="9.5" font-weight="600" fill="{t["amber_text"]}">04</text>
        <text x="11" y="26" class="sans" font-size="12" font-weight="600" fill="{t["ink"]}">Data</text>
      </g>
    </g>

    <!-- Right custom distributed-systems architecture illustration -->
    <g aria-hidden="true">
      <!-- Concentric orchestration rings -->
      <circle cx="706" cy="176" r="106" fill="none" stroke="{t["hairline"]}" stroke-width="1" />
      <circle class="orbit-cw" cx="706" cy="176" r="88" fill="none" stroke="{t["border_strong"]}" stroke-width="1.15" stroke-dasharray="18 10 4 10" />
      <circle class="orbit-ccw" cx="706" cy="176" r="64" fill="none" stroke="{t["emerald"]}" stroke-width="1.35" stroke-dasharray="52 38 14 38" stroke-opacity="0.78" />

      <!-- Orthogonal data pathways linking four architectural domains to core -->
      <path d="M 582 122 L 582 158 L 664 158" fill="none" stroke="{t["cyan"]}" stroke-opacity="0.28" stroke-width="2" />
      <path class="bus-c" d="M 582 122 L 582 158 L 664 158" fill="none" stroke="{t["cyan"]}" stroke-width="1.6" />

      <path d="M 833 122 L 833 158 L 748 158" fill="none" stroke="{t["violet"]}" stroke-opacity="0.28" stroke-width="2" />
      <path class="bus-v" d="M 833 122 L 833 158 L 748 158" fill="none" stroke="{t["violet"]}" stroke-width="1.6" />

      <path d="M 582 230 L 582 194 L 664 194" fill="none" stroke="{t["emerald"]}" stroke-opacity="0.28" stroke-width="2" />
      <path class="bus-e" d="M 582 230 L 582 194 L 664 194" fill="none" stroke="{t["emerald"]}" stroke-width="1.6" />

      <path d="M 833 230 L 833 194 L 748 194" fill="none" stroke="{t["amber"]}" stroke-opacity="0.28" stroke-width="2" />
      <path class="bus-a" d="M 833 230 L 833 194 L 748 194" fill="none" stroke="{t["amber"]}" stroke-width="1.6" />

      <!-- Travelling signal packets anchored to node ports -->
      <circle class="pkt pkt-c" cx="582" cy="122" r="3.4" fill="{t["cyan"]}" />
      <circle class="pkt pkt-v" cx="833" cy="122" r="3.4" fill="{t["violet"]}" />
      <circle class="pkt pkt-e" cx="582" cy="230" r="3.4" fill="{t["emerald"]}" />
      <circle class="pkt pkt-a" cx="833" cy="230" r="3.4" fill="{t["amber"]}" />

      <!-- Node 01: Interface & Client (Top-Left) -->
      <g>
        <rect x="526" y="64" width="112" height="58" rx="9" fill="{plane_fill}" stroke="{t["cyan"]}" stroke-width="1.25" />
        <rect x="538" y="76" width="16" height="11" rx="2" fill="none" stroke="{t["cyan"]}" stroke-width="1.3" />
        <line x1="538" y1="80" x2="554" y2="80" stroke="{t["cyan"]}" stroke-width="1.1" />
        <text x="562" y="85" class="mono" font-size="9.5" font-weight="700" fill="{t["cyan_text"]}">CLIENT</text>
        <text x="538" y="106" class="sans" font-size="11" font-weight="600" fill="{t["ink"]}">React · Next.js</text>
      </g>

      <!-- Node 02: AI Agent Runtime (Top-Right) -->
      <g>
        <rect x="774" y="64" width="118" height="58" rx="9" fill="{plane_fill}" stroke="{t["violet"]}" stroke-width="1.25" />
        <circle cx="788" cy="80" r="2.4" fill="{t["violet"]}" />
        <circle cx="798" cy="80" r="2.4" fill="{t["violet"]}" />
        <circle cx="793" cy="88" r="2.4" fill="{t["violet"]}" />
        <path d="M 788 80 L 798 80 L 793 88 Z" fill="none" stroke="{t["violet"]}" stroke-width="1.1" />
        <text x="807" y="85" class="mono" font-size="9.5" font-weight="700" fill="{t["violet_text"]}">AGENTS</text>
        <text x="786" y="106" class="sans" font-size="11" font-weight="600" fill="{t["ink"]}">LangGraph · LLM</text>
      </g>

      <!-- Node 03: API & Native Systems (Bottom-Left) -->
      <g>
        <rect x="526" y="230" width="112" height="58" rx="9" fill="{plane_fill_2}" stroke="{t["emerald"]}" stroke-width="1.25" />
        <polygon points="545,241 552,245 552,253 545,257 538,253 538,245" fill="none" stroke="{t["emerald"]}" stroke-width="1.3" />
        <text x="560" y="252" class="mono" font-size="9.5" font-weight="700" fill="{t["emerald_text"]}">SERVICES</text>
        <text x="538" y="272" class="sans" font-size="11" font-weight="600" fill="{t["ink"]}">FastAPI · Rust</text>
      </g>

      <!-- Node 04: Data & Ledger (Bottom-Right) -->
      <g>
        <rect x="774" y="230" width="118" height="58" rx="9" fill="{plane_fill_2}" stroke="{t["amber"]}" stroke-width="1.25" />
        <ellipse cx="793" cy="244" rx="6.5" ry="2.6" fill="none" stroke="{t["amber"]}" stroke-width="1.3" />
        <path d="M 786.5 244 L 786.5 253 C 786.5 255 799.5 255 799.5 253 L 799.5 244" fill="none" stroke="{t["amber"]}" stroke-width="1.3" />
        <text x="807" y="252" class="mono" font-size="9.5" font-weight="700" fill="{t["amber_text"]}">STORAGE</text>
        <text x="786" y="272" class="sans" font-size="11" font-weight="600" fill="{t["ink"]}">Postgres · SQL</text>
      </g>

      <!-- Central Layered Architectural Core Hub -->
      <g class="float-hub">
        <polygon points="706,134 748,158 748,194 706,218 664,194 664,158" fill="{hub_fill}" stroke="{t["emerald"]}" stroke-width="1.6" />
        <polygon points="706,144 738,162 738,190 706,208 674,190 674,162" fill="{t["surface_tint_emerald"]}" stroke="{t["cyan"]}" stroke-opacity="0.55" stroke-width="1" />
        <text x="706" y="172" text-anchor="middle" class="mono" font-size="10.2" font-weight="700" fill="{t["emerald_text"]}">CORE</text>
        <text x="706" y="187" text-anchor="middle" class="mono" font-size="9.2" font-weight="600" fill="{t["ink"]}">SYSTEMS</text>
      </g>

      <text x="892" y="328" text-anchor="end" class="mono" font-size="9.8" fill="{t["ink_muted"]}">{repo_count} PUBLIC REPOS  ·  UPDATED {esc(updated)}</text>
    </g>
  </g>

  <rect x="0.75" y="0.75" width="918.5" height="346.5" rx="16" fill="none" stroke="{t["border"]}" stroke-width="1.2" />
</svg>
"""


def render_project_agentos(meta: dict[str, Any], live: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    acc, acc_txt, acc_tint = _accent_pair(t, "emerald")
    v_acc, v_txt, v_tint = _accent_pair(t, "violet")
    stars = int(live.get("stars") or 0)
    lic = live.get("license") or "Apache-2.0"
    badge_str = f"01 / {meta['domain_label']}  ·  {lic}" + (f"  ·  {stars} stars" if stars else "")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 310" width="920" height="310" role="img" aria-labelledby="p-aos-t-{theme_name} p-aos-d-{theme_name}">
  <title id="p-aos-t-{theme_name}">AgentOS: Local-First AI Desktop Agent Architecture</title>
  <desc id="p-aos-d-{theme_name}">{esc(meta["summary"])}</desc>
  <defs>
    <linearGradient id="aos-bg-{theme_name}" x1="0" y1="0" x2="920" y2="310" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["canvas"]}" />
      <stop offset="100%" stop-color="{t["canvas_alt"]}" />
    </linearGradient>
    <clipPath id="aos-clip-{theme_name}">
      <rect x="0.75" y="0.75" width="918.5" height="308.5" rx="14" />
    </clipPath>
  </defs>
  <style>
    .sans {{ font-family: {FONT_SANS}; }}
    .mono {{ font-family: {FONT_MONO}; }}
    .prog-bar {{ transform-origin: 416px 262px; transform: scaleX(1); }}
    @media (prefers-reduced-motion: no-preference) {{
      .flow-line {{ stroke-dasharray: 10 8; animation: flowRight 1.8s linear infinite; }}
      .node-1 {{ animation: focus1 10s ease-in-out infinite; }}
      .node-2 {{ animation: focus2 10s ease-in-out infinite; }}
      .node-3 {{ animation: focus3 10s ease-in-out infinite; }}
      .node-4 {{ animation: focus4 10s ease-in-out infinite; }}
      .prog-bar {{ animation: runFill 10s cubic-bezier(0.22, 1, 0.36, 1) infinite; }}
    }}
    @keyframes flowRight {{
      from {{ stroke-dashoffset: 36; }}
      to   {{ stroke-dashoffset: 0; }}
    }}
    @keyframes focus1 {{
      0%, 22%   {{ stroke: {v_acc}; fill: {v_tint}; }}
      28%, 100% {{ stroke: {t["border"]}; fill: {t["surface"]}; }}
    }}
    @keyframes focus2 {{
      0%, 23%   {{ stroke: {t["border"]}; fill: {t["surface"]}; }}
      26%, 47%  {{ stroke: {t["amber"]}; fill: {t["surface_tint_amber"]}; }}
      53%, 100% {{ stroke: {t["border"]}; fill: {t["surface"]}; }}
    }}
    @keyframes focus3 {{
      0%, 48%   {{ stroke: {t["border"]}; fill: {t["surface"]}; }}
      51%, 72%  {{ stroke: {acc}; fill: {acc_tint}; }}
      78%, 100% {{ stroke: {t["border"]}; fill: {t["surface"]}; }}
    }}
    @keyframes focus4 {{
      0%, 73%   {{ stroke: {t["border"]}; fill: {t["surface"]}; }}
      76%, 96%  {{ stroke: {t["cyan"]}; fill: {t["surface_tint_cyan"]}; }}
      100%      {{ stroke: {t["border"]}; fill: {t["surface"]}; }}
    }}
    @keyframes runFill {{
      0%, 20%  {{ transform: scaleX(0.22); }}
      48%      {{ transform: scaleX(0.54); }}
      74%      {{ transform: scaleX(0.84); }}
      90%, 96% {{ transform: scaleX(1); }}
      100%     {{ transform: scaleX(0.22); }}
    }}
  </style>
  <g clip-path="url(#aos-clip-{theme_name})">
    <rect x="0" y="0" width="920" height="310" fill="url(#aos-bg-{theme_name})" />
    <rect x="0" y="0" width="4" height="310" fill="{acc}" />

    <!-- Left editorial specification -->
    <text x="34" y="42" class="mono" font-size="10.2" font-weight="600" fill="{acc_txt}">{esc(badge_str)}</text>
    <text x="34" y="82" class="sans" font-size="32" font-weight="700" fill="{t["ink"]}" letter-spacing="-0.025em">AgentOS</text>
    <text x="34" y="114" class="sans" font-size="13.2" fill="{t["ink_sec"]}">Local-first desktop agent runtime turning user</text>
    <text x="34" y="134" class="sans" font-size="13.2" fill="{t["ink_sec"]}">instructions into typed execution plans, explicit</text>
    <text x="34" y="154" class="sans" font-size="13.2" fill="{t["ink_sec"]}">permission gates, and verifiable computer actions.</text>

    <line x1="34" y1="184" x2="362" y2="184" stroke="{t["hairline"]}" stroke-width="1" />
    <text x="34" y="206" class="mono" font-size="9.8" font-weight="600" fill="{t["ink_muted"]}">ARCHITECTURE STACK</text>
    <text x="34" y="228" class="mono" font-size="11" font-weight="600" fill="{t["ink"]}">Tauri 2  ·  Rust  ·  React  ·  TypeScript</text>
    <text x="34" y="248" class="mono" font-size="11" font-weight="600" fill="{acc_txt}">FastAPI  ·  LangGraph  ·  SQLite Audit</text>

    <text x="34" y="284" class="mono" font-size="10.2" fill="{t["ink_muted"]}">github.com/dandisetiawanco/AgentOs</text>

    <!-- Right animated DAG execution canvas -->
    <rect x="394" y="22" width="500" height="266" rx="11" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1.15" />
    <text x="416" y="48" class="mono" font-size="10" font-weight="700" fill="{t["ink_muted"]}">AGENT EXECUTION GRAPH</text>
    <text x="872" y="48" text-anchor="end" class="mono" font-size="10" font-weight="600" fill="{acc_txt}">LOCAL RUNTIME · 127.0.0.1</text>
    <line x1="416" y1="58" x2="872" y2="58" stroke="{t["hairline"]}" stroke-width="1" />

    <!-- Animated connecting conduits between DAG stages -->
    <path d="M 624 104 L 664 104 M 768 136 L 768 158 M 664 190 L 624 190" fill="none" stroke="{t["hairline"]}" stroke-width="2" />
    <path class="flow-line" d="M 624 104 L 664 104" fill="none" stroke="{v_acc}" stroke-width="1.8" />
    <path class="flow-line" d="M 768 136 L 768 158" fill="none" stroke="{t["amber"]}" stroke-width="1.8" />
    <path class="flow-line" d="M 664 190 L 624 190" fill="none" stroke="{acc}" stroke-width="1.8" />

    <!-- Stage 1: LangGraph Planner -->
    <rect class="node-1" x="416" y="72" width="208" height="64" rx="8" fill="{v_tint}" stroke="{v_acc}" stroke-width="1.25" />
    <text x="430" y="93" class="mono" font-size="9.5" font-weight="700" fill="{v_txt}">01 · PLAN GRAPH</text>
    <text x="430" y="111" class="sans" font-size="12" font-weight="600" fill="{t["ink"]}">Typed LangGraph Steps</text>
    <text x="430" y="126" class="mono" font-size="9.5" fill="{t["ink_muted"]}">Intent → DAG nodes</text>

    <!-- Stage 2: Permission Gate -->
    <rect class="node-2" x="664" y="72" width="208" height="64" rx="8" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1.25" />
    <text x="678" y="93" class="mono" font-size="9.5" font-weight="700" fill="{t["amber_text"]}">02 · APPROVAL GATE</text>
    <text x="678" y="111" class="sans" font-size="12" font-weight="600" fill="{t["ink"]}">Scoped Permission Check</text>
    <text x="678" y="126" class="mono" font-size="9.5" fill="{t["ink_muted"]}">Human confirmation required</text>

    <!-- Stage 3: Sandboxed Tool Runner -->
    <rect class="node-3" x="664" y="158" width="208" height="64" rx="8" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1.25" />
    <text x="678" y="179" class="mono" font-size="9.5" font-weight="700" fill="{acc_txt}">03 · TOOL SANDBOX</text>
    <text x="678" y="197" class="sans" font-size="12" font-weight="600" fill="{t["ink"]}">Authorized Execution</text>
    <text x="678" y="212" class="mono" font-size="9.5" fill="{t["ink_muted"]}">Rust IPC + Python workers</text>

    <!-- Stage 4: Verification & SQLite Audit -->
    <rect class="node-4" x="416" y="158" width="208" height="64" rx="8" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1.25" />
    <text x="430" y="179" class="mono" font-size="9.5" font-weight="700" fill="{t["cyan_text"]}">04 · VERIFY &amp; AUDIT</text>
    <text x="430" y="197" class="sans" font-size="12" font-weight="600" fill="{t["ink"]}">Exit Code &amp; Trace Log</text>
    <text x="430" y="212" class="mono" font-size="9.5" fill="{t["ink_muted"]}">Persisted to SQLite</text>

    <!-- Bottom execution progress rail -->
    <text x="416" y="248" class="mono" font-size="9.5" font-weight="600" fill="{t["ink_muted"]}">PIPELINE CYCLE</text>
    <text x="872" y="248" text-anchor="end" class="mono" font-size="9.5" font-weight="600" fill="{acc_txt}">Plan → Gate → Execute → Verify</text>
    <rect x="416" y="258" width="456" height="7" rx="3.5" fill="{t["surface_raised"]}" />
    <rect class="prog-bar" x="416" y="258" width="456" height="7" rx="3.5" fill="{acc}" />
  </g>
  <rect x="0.75" y="0.75" width="918.5" height="308.5" rx="14" fill="none" stroke="{t["border"]}" stroke-width="1.2" />
</svg>
"""


def render_project_omnidesk(meta: dict[str, Any], live: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    c_acc, c_txt, c_tint = _accent_pair(t, "cyan")
    e_acc, e_txt, e_tint = _accent_pair(t, "emerald")
    v_acc, v_txt, v_tint = _accent_pair(t, "violet")
    stars = int(live.get("stars") or 0)
    badge_str = f"02 / {meta['domain_label']}" + (f"  ·  {stars} star" if stars == 1 else (f"  ·  {stars} stars" if stars > 1 else ""))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 296" width="920" height="296" role="img" aria-labelledby="p-od-t-{theme_name} p-od-d-{theme_name}">
  <title id="p-od-t-{theme_name}">OmniDesk: Cross-Platform AI Desktop Orchestration</title>
  <desc id="p-od-d-{theme_name}">{esc(meta["summary"])}</desc>
  <defs>
    <linearGradient id="od-bg-{theme_name}" x1="0" y1="0" x2="920" y2="296" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["canvas_alt"]}" />
      <stop offset="100%" stop-color="{t["canvas"]}" />
    </linearGradient>
    <clipPath id="od-clip-{theme_name}">
      <rect x="0.75" y="0.75" width="918.5" height="294.5" rx="14" />
    </clipPath>
  </defs>
  <style>
    .sans {{ font-family: {FONT_SANS}; }}
    .mono {{ font-family: {FONT_MONO}; }}
    @media (prefers-reduced-motion: no-preference) {{
      .ipc-flow {{ stroke-dasharray: 8 7; animation: ipcDash 1.9s linear infinite; }}
      .os-1 {{ animation: osHi 7.5s ease-in-out 0s infinite; }}
      .os-2 {{ animation: osHi 7.5s ease-in-out 2.5s infinite; }}
      .os-3 {{ animation: osHi 7.5s ease-in-out 5.0s infinite; }}
      .ipc-pkt {{ animation: ipcGlide 3.4s cubic-bezier(0.4, 0, 0.2, 1) infinite; }}
    }}
    @keyframes ipcDash {{
      from {{ stroke-dashoffset: 30; }}
      to   {{ stroke-dashoffset: 0; }}
    }}
    @keyframes osHi {{
      0%, 28%   {{ stroke: {c_acc}; fill: {c_tint}; }}
      38%, 100% {{ stroke: {t["border"]}; fill: {t["surface"]}; }}
    }}
    @keyframes ipcGlide {{
      0%   {{ transform: translateX(0px); opacity: 0; }}
      12%  {{ opacity: 1; }}
      88%  {{ opacity: 1; }}
      100% {{ transform: translateX(416px); opacity: 0; }}
    }}
  </style>
  <g clip-path="url(#od-clip-{theme_name})">
    <rect x="0" y="0" width="920" height="296" fill="url(#od-bg-{theme_name})" />
    <rect x="916" y="0" width="4" height="296" fill="{c_acc}" />

    <!-- Left architectural orchestration topology (reversed composition from AgentOS) -->
    <rect x="26" y="22" width="504" height="252" rx="11" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1.15" />
    <text x="46" y="46" class="mono" font-size="10" font-weight="700" fill="{t["ink_muted"]}">HYBRID AI ROUTER &amp; OS ADAPTERS</text>
    <text x="510" y="46" text-anchor="end" class="mono" font-size="9.8" font-weight="600" fill="{c_txt}">TAURI 2 SIDECAR</text>

    <!-- Tier 1: Dual AI Providers -->
    <rect x="46" y="60" width="218" height="48" rx="8" fill="{e_tint}" stroke="{e_acc}" stroke-width="1.2" />
    <text x="60" y="80" class="mono" font-size="9.5" font-weight="700" fill="{e_txt}">LOCAL PROVIDER</text>
    <text x="60" y="97" class="sans" font-size="11.8" font-weight="600" fill="{t["ink"]}">Ollama On-Device Models</text>

    <rect x="292" y="60" width="218" height="48" rx="8" fill="{v_tint}" stroke="{v_acc}" stroke-width="1.2" />
    <text x="306" y="80" class="mono" font-size="9.5" font-weight="700" fill="{v_txt}">CLOUD PROVIDER</text>
    <text x="306" y="97" class="sans" font-size="11.8" font-weight="600" fill="{t["ink"]}">External LLM Adapters</text>

    <!-- Downward conduits to Loopback IPC -->
    <line class="ipc-flow" x1="155" y1="108" x2="155" y2="136" stroke="{e_acc}" stroke-width="1.7" />
    <line class="ipc-flow" x1="401" y1="108" x2="401" y2="136" stroke="{v_acc}" stroke-width="1.7" />

    <!-- Tier 2: Authenticated Loopback IPC Bus -->
    <rect x="46" y="136" width="464" height="44" rx="8" fill="{t["surface_raised"]}" stroke="{c_acc}" stroke-width="1.35" />
    <text x="62" y="155" class="mono" font-size="10.2" font-weight="700" fill="{c_txt}">AUTHENTICATED LOOPBACK IPC  ·  127.0.0.1</text>
    <text x="62" y="170" class="sans" font-size="10.5" fill="{t["ink_sec"]}">Rust native host bridge  ·  Python operator engine</text>
    <circle class="ipc-pkt" cx="62" cy="136" r="3.4" fill="{c_acc}" />

    <!-- Downward conduits to 3 OS adapters -->
    <line class="ipc-flow" x1="118" y1="180" x2="118" y2="206" stroke="{c_acc}" stroke-width="1.6" />
    <line class="ipc-flow" x1="278" y1="180" x2="278" y2="206" stroke="{c_acc}" stroke-width="1.6" />
    <line class="ipc-flow" x1="438" y1="180" x2="438" y2="206" stroke="{c_acc}" stroke-width="1.6" />

    <!-- Tier 3: Cross-platform adapters -->
    <rect class="os-1" x="46" y="206" width="144" height="50" rx="8" fill="{c_tint}" stroke="{c_acc}" stroke-width="1.2" />
    <text x="118" y="227" text-anchor="middle" class="sans" font-size="12.5" font-weight="700" fill="{t["ink"]}">macOS</text>
    <text x="118" y="244" text-anchor="middle" class="mono" font-size="9.2" fill="{t["ink_muted"]}">Native Adapter</text>

    <rect class="os-2" x="206" y="206" width="144" height="50" rx="8" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1.2" />
    <text x="278" y="227" text-anchor="middle" class="sans" font-size="12.5" font-weight="700" fill="{t["ink"]}">Linux</text>
    <text x="278" y="244" text-anchor="middle" class="mono" font-size="9.2" fill="{t["ink_muted"]}">Native Adapter</text>

    <rect class="os-3" x="366" y="206" width="144" height="50" rx="8" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1.2" />
    <text x="438" y="227" text-anchor="middle" class="sans" font-size="12.5" font-weight="700" fill="{t["ink"]}">Windows</text>
    <text x="438" y="244" text-anchor="middle" class="mono" font-size="9.2" fill="{t["ink_muted"]}">Native Adapter</text>

    <!-- Right editorial specification -->
    <text x="558" y="46" class="mono" font-size="10.2" font-weight="600" fill="{c_txt}">{esc(badge_str)}</text>
    <text x="558" y="84" class="sans" font-size="31" font-weight="700" fill="{t["ink"]}" letter-spacing="-0.025em">OmniDesk</text>
    <text x="558" y="116" class="sans" font-size="13.2" fill="{t["ink_sec"]}">Cross-platform AI desktop agent turning natural</text>
    <text x="558" y="136" class="sans" font-size="13.2" fill="{t["ink_sec"]}">commands and user demonstrations into verified</text>
    <text x="558" y="156" class="sans" font-size="13.2" fill="{t["ink_sec"]}">workflows across macOS, Linux, and Windows.</text>

    <line x1="558" y1="184" x2="886" y2="184" stroke="{t["hairline"]}" stroke-width="1" />
    <text x="558" y="206" class="mono" font-size="9.8" font-weight="600" fill="{t["ink_muted"]}">CORE TECHNOLOGIES</text>
    <text x="558" y="228" class="mono" font-size="11" font-weight="600" fill="{t["ink"]}">Rust  ·  Tauri 2  ·  Python  ·  React 19</text>
    <text x="558" y="248" class="mono" font-size="11" font-weight="600" fill="{c_txt}">Ollama  ·  Cloud LLMs  ·  Sidecar IPC</text>

    <text x="558" y="274" class="mono" font-size="10.2" fill="{t["ink_muted"]}">github.com/dandisetiawanco/Omnidesk</text>
  </g>
  <rect x="0.75" y="0.75" width="918.5" height="294.5" rx="14" fill="none" stroke="{t["border"]}" stroke-width="1.2" />
</svg>
"""


def render_project_ledger(meta: dict[str, Any], live: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    a_acc, a_txt, a_tint = _accent_pair(t, "amber")
    e_acc, e_txt, e_tint = _accent_pair(t, "emerald")
    pushed = (live.get("pushed_at") or "")[:10] or "Active"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 320" width="448" height="320" role="img" aria-labelledby="p-ldg-t-{theme_name} p-ldg-d-{theme_name}">
  <title id="p-ldg-t-{theme_name}">Ledger: Double-Entry Financial Architecture</title>
  <desc id="p-ldg-d-{theme_name}">{esc(meta["summary"])}</desc>
  <defs>
    <linearGradient id="ldg-bg-{theme_name}" x1="0" y1="0" x2="448" y2="320" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["canvas"]}" />
      <stop offset="100%" stop-color="{t["canvas_alt"]}" />
    </linearGradient>
    <clipPath id="ldg-clip-{theme_name}">
      <rect x="0.75" y="0.75" width="446.5" height="318.5" rx="14" />
    </clipPath>
  </defs>
  <style>
    .sans {{ font-family: {FONT_SANS}; }}
    .mono {{ font-family: {FONT_MONO}; }}
    .eq-dr {{ transform-origin: 40px 158px; }}
    .eq-cr {{ transform-origin: 408px 158px; }}
    @media (prefers-reduced-motion: no-preference) {{
      .tx-flow {{ stroke-dasharray: 6 6; animation: txDash 2.0s linear infinite; }}
      .tx-row-1 {{ animation: rowPulse 6s ease-in-out 0s infinite; }}
      .tx-row-2 {{ animation: rowPulse 6s ease-in-out 3s infinite; }}
      .eq-beam {{ animation: eqSweep 4.8s ease-in-out infinite; }}
    }}
    @keyframes txDash {{
      from {{ stroke-dashoffset: 24; }}
      to   {{ stroke-dashoffset: 0; }}
    }}
    @keyframes rowPulse {{
      0%, 42%   {{ opacity: 1; }}
      52%, 100% {{ opacity: 0.62; }}
    }}
    @keyframes eqSweep {{
      0%, 100% {{ opacity: 0.72; }}
      50%      {{ opacity: 1; }}
    }}
  </style>
  <g clip-path="url(#ldg-clip-{theme_name})">
    <rect x="0" y="0" width="448" height="320" fill="url(#ldg-bg-{theme_name})" />
    <rect x="0" y="0" width="448" height="3.5" fill="{a_acc}" />

    <!-- Top visual: Double-entry ledger & ACID reconciliation diagram -->
    <rect x="20" y="20" width="408" height="162" rx="10" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1.1" />
    <text x="34" y="41" class="mono" font-size="9.5" font-weight="700" fill="{a_txt}">DOUBLE-ENTRY ENGINE</text>
    <text x="414" y="41" text-anchor="end" class="mono" font-size="9.2" fill="{t["ink_muted"]}">ACID · POSTGRESQL</text>
    <line x1="34" y1="50" x2="414" y2="50" stroke="{t["hairline"]}" stroke-width="1" />

    <!-- Debit journal block -->
    <rect class="tx-row-1" x="34" y="62" width="144" height="54" rx="7" fill="{a_tint}" stroke="{a_acc}" stroke-width="1.15" />
    <text x="44" y="79" class="mono" font-size="9.2" font-weight="700" fill="{a_txt}">DEBIT LEDGER</text>
    <text x="44" y="95" class="sans" font-size="11" font-weight="600" fill="{t["ink"]}">1100 · Cash &amp; Bank</text>
    <text x="44" y="109" class="mono" font-size="9.2" fill="{t["ink_muted"]}">Invoicing · AR</text>

    <!-- Center ACID verifier node -->
    <line class="tx-flow" x1="178" y1="89" x2="202" y2="89" stroke="{a_acc}" stroke-width="1.6" />
    <line class="tx-flow" x1="246" y1="89" x2="270" y2="89" stroke="{e_acc}" stroke-width="1.6" />
    <rect x="202" y="68" width="44" height="42" rx="7" fill="{t["surface_raised"]}" stroke="{t["border_strong"]}" stroke-width="1.2" />
    <text x="224" y="87" text-anchor="middle" class="mono" font-size="9.5" font-weight="700" fill="{t["ink"]}">TX</text>
    <text x="224" y="101" text-anchor="middle" class="mono" font-size="8.5" fill="{e_txt}">DR=CR</text>

    <!-- Credit journal block -->
    <rect class="tx-row-2" x="270" y="62" width="144" height="54" rx="7" fill="{e_tint}" stroke="{e_acc}" stroke-width="1.15" />
    <text x="280" y="79" class="mono" font-size="9.2" font-weight="700" fill="{e_txt}">CREDIT LEDGER</text>
    <text x="280" y="95" class="sans" font-size="11" font-weight="600" fill="{t["ink"]}">4100 · Revenue</text>
    <text x="280" y="109" class="mono" font-size="9.2" fill="{t["ink_muted"]}">Reconciled Journal</text>

    <!-- Trial balance equilibrium bar -->
    <text x="34" y="142" class="mono" font-size="9.2" font-weight="600" fill="{t["ink_muted"]}">TRIAL BALANCE INVARIANT</text>
    <text x="414" y="142" text-anchor="end" class="mono" font-size="9.2" font-weight="600" fill="{e_txt}">BALANCED · ZERO DRIFT</text>
    <rect x="34" y="151" width="380" height="8" rx="4" fill="{t["surface_raised"]}" />
    <rect class="eq-beam" x="34" y="151" width="188" height="8" rx="4" fill="{a_acc}" />
    <rect class="eq-beam" x="226" y="151" width="188" height="8" rx="4" fill="{e_acc}" />
    <rect x="222" y="148" width="4" height="14" rx="1.5" fill="{t["ink"]}" />

    <!-- Bottom editorial specification -->
    <text x="22" y="208" class="mono" font-size="9.8" font-weight="600" fill="{a_txt}">03 / {esc(meta["domain_label"])}</text>
    <text x="426" y="208" text-anchor="end" class="mono" font-size="9.8" fill="{t["ink_muted"]}">{esc(pushed)}</text>
    <text x="22" y="236" class="sans" font-size="22" font-weight="700" fill="{t["ink"]}" letter-spacing="-0.02em">Ledger</text>
    <text x="22" y="260" class="sans" font-size="12.2" fill="{t["ink_sec"]}">Double-entry bookkeeping, bank reconciliation, and</text>
    <text x="22" y="277" class="sans" font-size="12.2" fill="{t["ink_sec"]}">modular enterprise financial reporting.</text>
    <line x1="22" y1="291" x2="426" y2="291" stroke="{t["hairline"]}" stroke-width="1" />
    <text x="22" y="308" class="mono" font-size="10.2" font-weight="600" fill="{a_txt}">Java 21 · Spring Boot · Next.js · PostgreSQL</text>
  </g>
  <rect x="0.75" y="0.75" width="446.5" height="318.5" rx="14" fill="none" stroke="{t["border"]}" stroke-width="1.2" />
</svg>
"""


def render_project_talentos(meta: dict[str, Any], live: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    v_acc, v_txt, v_tint = _accent_pair(t, "violet")
    c_acc, c_txt, c_tint = _accent_pair(t, "cyan")
    pushed = (live.get("pushed_at") or "")[:10] or "Active"

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 320" width="448" height="320" role="img" aria-labelledby="p-tos-t-{theme_name} p-tos-d-{theme_name}">
  <title id="p-tos-t-{theme_name}">TalentOS: Recruitment Operating System Architecture</title>
  <desc id="p-tos-d-{theme_name}">{esc(meta["summary"])}</desc>
  <defs>
    <linearGradient id="tos-bg-{theme_name}" x1="0" y1="0" x2="448" y2="320" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["canvas"]}" />
      <stop offset="100%" stop-color="{t["canvas_alt"]}" />
    </linearGradient>
    <clipPath id="tos-clip-{theme_name}">
      <rect x="0.75" y="0.75" width="446.5" height="318.5" rx="14" />
    </clipPath>
  </defs>
  <style>
    .sans {{ font-family: {FONT_SANS}; }}
    .mono {{ font-family: {FONT_MONO}; }}
    @media (prefers-reduced-motion: no-preference) {{
      .scan-bar {{ animation: docScan 4.6s ease-in-out infinite; }}
      .pipe-flow {{ stroke-dasharray: 6 5; animation: pipeDash 1.9s linear infinite; }}
      .stg-1 {{ animation: stgHi 6.6s ease-in-out 0s infinite; }}
      .stg-2 {{ animation: stgHi 6.6s ease-in-out 2.2s infinite; }}
      .stg-3 {{ animation: stgHi 6.6s ease-in-out 4.4s infinite; }}
    }}
    @keyframes docScan {{
      0%, 100% {{ transform: translateY(0px); }}
      50%      {{ transform: translateY(46px); }}
    }}
    @keyframes pipeDash {{
      from {{ stroke-dashoffset: 22; }}
      to   {{ stroke-dashoffset: 0; }}
    }}
    @keyframes stgHi {{
      0%, 28%   {{ stroke: {c_acc}; fill: {c_tint}; }}
      38%, 100% {{ stroke: {t["border"]}; fill: {t["surface_raised"]}; }}
    }}
  </style>
  <g clip-path="url(#tos-clip-{theme_name})">
    <rect x="0" y="0" width="448" height="320" fill="url(#tos-bg-{theme_name})" />
    <rect x="0" y="0" width="448" height="3.5" fill="{v_acc}" />

    <!-- Top visual: Evidence-first resume parser & hiring pipeline -->
    <rect x="20" y="20" width="408" height="162" rx="10" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1.1" />
    <text x="34" y="41" class="mono" font-size="9.5" font-weight="700" fill="{v_txt}">RESUME EVIDENCE EXTRACTION</text>
    <text x="414" y="41" text-anchor="end" class="mono" font-size="9.2" fill="{t["ink_muted"]}">FASTAPI · NEXT.JS</text>
    <line x1="34" y1="50" x2="414" y2="50" stroke="{t["hairline"]}" stroke-width="1" />

    <!-- Left parsed document representation -->
    <rect x="34" y="62" width="110" height="66" rx="7" fill="{v_tint}" stroke="{v_acc}" stroke-width="1.15" />
    <rect x="44" y="73" width="54" height="5" rx="2" fill="{v_acc}" fill-opacity="0.85" />
    <rect x="44" y="85" width="88" height="4" rx="2" fill="{t["ink_muted"]}" fill-opacity="0.55" />
    <rect x="44" y="95" width="76" height="4" rx="2" fill="{t["ink_muted"]}" fill-opacity="0.55" />
    <rect x="44" y="105" width="82" height="4" rx="2" fill="{t["ink_muted"]}" fill-opacity="0.45" />
    <rect x="44" y="115" width="60" height="4" rx="2" fill="{c_acc}" fill-opacity="0.7" />
    <rect class="scan-bar" x="37" y="70" width="104" height="2" rx="1" fill="{v_acc}" />

    <!-- Conduit to structured signals -->
    <line class="pipe-flow" x1="144" y1="95" x2="178" y2="95" stroke="{v_acc}" stroke-width="1.6" />

    <!-- Right structured candidate evaluation cards -->
    <rect x="178" y="62" width="236" height="66" rx="7" fill="{t["surface_raised"]}" stroke="{t["border"]}" stroke-width="1.1" />
    <text x="190" y="79" class="mono" font-size="9.2" font-weight="700" fill="{c_txt}">STRUCTURED SIGNALS</text>
    <text x="190" y="98" class="sans" font-size="11" font-weight="600" fill="{t["ink"]}">Skills · Tenure · Role Match</text>
    <text x="190" y="115" class="mono" font-size="9.2" fill="{t["ink_muted"]}">Org-isolated recruiter review</text>

    <!-- Bottom 3-stage human-led hiring pipeline -->
    <rect class="stg-1" x="34" y="140" width="118" height="28" rx="6" fill="{c_tint}" stroke="{c_acc}" stroke-width="1.15" />
    <text x="93" y="158" text-anchor="middle" class="mono" font-size="9.8" font-weight="600" fill="{t["ink"]}">01 Screen</text>

    <line class="pipe-flow" x1="152" y1="154" x2="165" y2="154" stroke="{c_acc}" stroke-width="1.5" />

    <rect class="stg-2" x="165" y="140" width="118" height="28" rx="6" fill="{t["surface_raised"]}" stroke="{t["border"]}" stroke-width="1.15" />
    <text x="224" y="158" text-anchor="middle" class="mono" font-size="9.8" font-weight="600" fill="{t["ink"]}">02 Interview</text>

    <line class="pipe-flow" x1="283" y1="154" x2="296" y2="154" stroke="{c_acc}" stroke-width="1.5" />

    <rect class="stg-3" x="296" y="140" width="118" height="28" rx="6" fill="{t["surface_raised"]}" stroke="{t["border"]}" stroke-width="1.15" />
    <text x="355" y="158" text-anchor="middle" class="mono" font-size="9.8" font-weight="600" fill="{t["ink"]}">03 Decision</text>

    <!-- Bottom editorial specification -->
    <text x="22" y="208" class="mono" font-size="9.8" font-weight="600" fill="{v_txt}">04 / {esc(meta["domain_label"])}</text>
    <text x="426" y="208" text-anchor="end" class="mono" font-size="9.8" fill="{t["ink_muted"]}">{esc(pushed)}</text>
    <text x="22" y="236" class="sans" font-size="22" font-weight="700" fill="{t["ink"]}" letter-spacing="-0.02em">TalentOS</text>
    <text x="22" y="260" class="sans" font-size="12.2" fill="{t["ink_sec"]}">Evidence-first resume extraction, candidate portals,</text>
    <text x="22" y="277" class="sans" font-size="12.2" fill="{t["ink_sec"]}">and human-led hiring pipelines.</text>
    <line x1="22" y1="291" x2="426" y2="291" stroke="{t["hairline"]}" stroke-width="1" />
    <text x="22" y="308" class="mono" font-size="10.2" font-weight="600" fill="{v_txt}">Next.js · TypeScript · FastAPI · PostgreSQL</text>
  </g>
  <rect x="0.75" y="0.75" width="446.5" height="318.5" rx="14" fill="none" stroke="{t["border"]}" stroke-width="1.2" />
</svg>
"""


def render_project_infraos(meta: dict[str, Any], live: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    c_acc, c_txt, c_tint = _accent_pair(t, "cyan")
    e_acc, e_txt, e_tint = _accent_pair(t, "emerald")
    a_acc, a_txt, _ = _accent_pair(t, "amber")
    pushed = (live.get("pushed_at") or "")[:10] or "Active"

    wave_path = (
        "M 412 88 L 448 88 L 464 62 L 480 96 L 496 74 L 520 88 "
        "L 562 88 L 578 56 L 594 94 L 612 72 L 636 88 "
        "L 684 88 L 702 64 L 718 92 L 736 76 L 764 88 "
        "L 812 88 L 828 60 L 844 92 L 866 88"
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 210" width="920" height="210" role="img" aria-labelledby="p-inf-t-{theme_name} p-inf-d-{theme_name}">
  <title id="p-inf-t-{theme_name}">InfraOS: Infrastructure Operations &amp; Observability Platform</title>
  <desc id="p-inf-d-{theme_name}">{esc(meta["summary"])}</desc>
  <defs>
    <linearGradient id="inf-bg-{theme_name}" x1="0" y1="0" x2="920" y2="210" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["canvas"]}" />
      <stop offset="100%" stop-color="{t["canvas_alt"]}" />
    </linearGradient>
    <clipPath id="inf-clip-{theme_name}">
      <rect x="0.75" y="0.75" width="918.5" height="208.5" rx="14" />
    </clipPath>
  </defs>
  <style>
    .sans {{ font-family: {FONT_SANS}; }}
    .mono {{ font-family: {FONT_MONO}; }}
    .wave-hi {{ opacity: 0; }}
    @media (prefers-reduced-motion: no-preference) {{
      .wave-hi {{ opacity: 1; stroke-dasharray: 84 520; animation: waveTrace 4.8s linear infinite; }}
      .roll-line {{ stroke-dasharray: 8 6; animation: rollMove 2.0s linear infinite; }}
    }}
    @keyframes waveTrace {{
      0%   {{ stroke-dashoffset: 604; }}
      100% {{ stroke-dashoffset: 0; }}
    }}
    @keyframes rollMove {{
      from {{ stroke-dashoffset: 28; }}
      to   {{ stroke-dashoffset: 0; }}
    }}
  </style>
  <g clip-path="url(#inf-clip-{theme_name})">
    <rect x="0" y="0" width="920" height="210" fill="url(#inf-bg-{theme_name})" />
    <rect x="0" y="0" width="4" height="210" fill="{c_acc}" />

    <!-- Left compact horizontal editorial info -->
    <text x="32" y="38" class="mono" font-size="10" font-weight="600" fill="{c_txt}">05 / {esc(meta["domain_label"])}</text>
    <text x="32" y="72" class="sans" font-size="26" font-weight="700" fill="{t["ink"]}" letter-spacing="-0.02em">InfraOS</text>
    <text x="32" y="100" class="sans" font-size="12.5" fill="{t["ink_sec"]}">Go control plane unifying host telemetry, Prometheus</text>
    <text x="32" y="118" class="sans" font-size="12.5" fill="{t["ink_sec"]}">observability, Terraform modules, and rollout control.</text>
    <line x1="32" y1="140" x2="360" y2="140" stroke="{t["hairline"]}" stroke-width="1" />
    <text x="32" y="162" class="mono" font-size="10.5" font-weight="600" fill="{c_txt}">Go · Next.js · Prometheus · Terraform · Docker</text>
    <text x="32" y="184" class="mono" font-size="9.8" fill="{t["ink_muted"]}">dandisetiawanco/InfraOS  ·  {esc(pushed)}</text>

    <!-- Right telemetry & deployment panel -->
    <rect x="392" y="20" width="502" height="170" rx="10" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1.1" />
    <text x="412" y="42" class="mono" font-size="9.5" font-weight="700" fill="{t["ink_muted"]}">SERVICE TELEMETRY WAVEFORM</text>
    <text x="874" y="42" text-anchor="end" class="mono" font-size="9.5" font-weight="600" fill="{e_txt}">GO WORKER · PROMETHEUS</text>

    <!-- Waveform baseline + animated pulse -->
    <line x1="412" y1="88" x2="874" y2="88" stroke="{t["hairline"]}" stroke-width="1" />
    <path d="{wave_path}" fill="none" stroke="{c_acc}" stroke-opacity="0.32" stroke-width="1.8" stroke-linejoin="round" />
    <path class="wave-hi" pathLength="604" d="{wave_path}" fill="none" stroke="{c_acc}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />

    <!-- Deployment rollout pipeline -->
    <line x1="412" y1="116" x2="874" y2="116" stroke="{t["hairline"]}" stroke-width="1" />
    <line class="roll-line" x1="470" y1="152" x2="816" y2="152" stroke="{e_acc}" stroke-width="1.7" />

    <rect x="412" y="134" width="128" height="36" rx="7" fill="{c_tint}" stroke="{c_acc}" stroke-width="1.15" />
    <text x="476" y="156" text-anchor="middle" class="mono" font-size="10.2" font-weight="600" fill="{t["ink"]}">Go Telemetry</text>

    <rect x="578" y="134" width="130" height="36" rx="7" fill="{t["surface_raised"]}" stroke="{a_acc}" stroke-width="1.15" />
    <text x="643" y="156" text-anchor="middle" class="mono" font-size="10.2" font-weight="600" fill="{a_txt}">Terraform HCL</text>

    <rect x="746" y="134" width="128" height="36" rx="7" fill="{e_tint}" stroke="{e_acc}" stroke-width="1.15" />
    <text x="810" y="156" text-anchor="middle" class="mono" font-size="10.2" font-weight="600" fill="{e_txt}">Safe Rollout</text>
  </g>
  <rect x="0.75" y="0.75" width="918.5" height="208.5" rx="14" fill="none" stroke="{t["border"]}" stroke-width="1.2" />
</svg>
"""


def render_recent_pulse(data: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    recent = data.get("recent_feed", [])[:5]
    updated = data.get("generated_at_utc", "")

    nodes_svg: list[str] = []
    if recent:
        n = len(recent)
        left_x, right_x = 84.0, 836.0
        for idx, repo in enumerate(recent):
            nx = left_x if n == 1 else left_x + (idx / (n - 1)) * (right_x - left_x)
            col = lang_color(repo.get("language") or "Multi", t, idx)
            pushed = (repo.get("pushed_at") or "")[5:10] or "recent"
            r_name = truncate(repo["name"], 15)
            lang = truncate(repo.get("language") or "Multi", 12)
            delay = idx * 1.1
            nodes_svg.append(
                f'  <g>\n'
                f'    <circle class="nd-{idx}" cx="{nx:.1f}" cy="74" r="7" fill="{t["surface"]}" stroke="{col}" stroke-width="2.2" />\n'
                f'    <circle cx="{nx:.1f}" cy="74" r="2.8" fill="{col}" />\n'
                f'    <text x="{nx:.1f}" y="54" text-anchor="middle" class="sans" font-size="12.2" font-weight="700" fill="{t["ink"]}">{esc(r_name)}</text>\n'
                f'    <text x="{nx:.1f}" y="102" text-anchor="middle" class="mono" font-size="9.8" font-weight="600" fill="{t["ink_sec"]}">{esc(lang)}</text>\n'
                f'    <text x="{nx:.1f}" y="117" text-anchor="middle" class="mono" font-size="9.2" fill="{t["ink_muted"]}">{esc(pushed)}</text>\n'
                f'  </g>'
            )
            _ = delay

    node_css = "\n".join(
        f"      .nd-{i} {{ animation: nodePing 6.5s ease-in-out {i * 1.1:.1f}s infinite; transform-origin: {(84.0 if len(recent) <= 1 else 84.0 + (i / (len(recent) - 1)) * 752.0):.1f}px 74px; }}"
        for i in range(len(recent))
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 138" width="920" height="138" role="img" aria-labelledby="rp-t-{theme_name} rp-d-{theme_name}">
  <title id="rp-t-{theme_name}">Recently Shipped Repository Activity Pulse</title>
  <desc id="rp-d-{theme_name}">Live chronological delivery pulse across the {len(recent)} most recently updated public repositories.</desc>
  <defs>
    <linearGradient id="rp-bg-{theme_name}" x1="0" y1="0" x2="920" y2="138" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["canvas"]}" />
      <stop offset="100%" stop-color="{t["canvas_alt"]}" />
    </linearGradient>
    <linearGradient id="rp-beam-{theme_name}" x1="0" y1="0" x2="180" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["emerald"]}" stop-opacity="0" />
      <stop offset="50%" stop-color="{t["cyan"]}" stop-opacity="0.95" />
      <stop offset="100%" stop-color="{t["emerald"]}" stop-opacity="0" />
    </linearGradient>
    <clipPath id="rp-rail-{theme_name}">
      <rect x="64" y="70" width="792" height="8" />
    </clipPath>
  </defs>
  <style>
    .sans {{ font-family: {FONT_SANS}; }}
    .mono {{ font-family: {FONT_MONO}; }}
    .rail-beam {{ opacity: 0; }}
    @media (prefers-reduced-motion: no-preference) {{
      .rail-beam {{ animation: railSweep 6.5s cubic-bezier(0.4, 0, 0.2, 1) infinite; }}
{node_css}
    }}
    @keyframes railSweep {{
      0%        {{ transform: translateX(-180px); opacity: 0; }}
      14%, 82%  {{ opacity: 1; }}
      96%, 100% {{ transform: translateX(820px); opacity: 0; }}
    }}
    @keyframes nodePing {{
      0%, 16%   {{ transform: scale(1.24); }}
      28%, 100% {{ transform: scale(1); }}
    }}
  </style>
  <rect x="0.75" y="0.75" width="918.5" height="136.5" rx="12" fill="url(#rp-bg-{theme_name})" stroke="{t["border"]}" stroke-width="1.15" />
  <text x="24" y="26" class="mono" font-size="9.8" font-weight="700" fill="{t["emerald_text"]}">LIVE DELIVERY TIMELINE  ·  NEWEST TO EARLIER</text>
  <text x="896" y="26" text-anchor="end" class="mono" font-size="9.5" fill="{t["ink_muted"]}">AUTO-SYNCED {esc(updated)}</text>

  <line x1="64" y1="74" x2="856" y2="74" stroke="{t["border"]}" stroke-width="2" stroke-linecap="round" />
  <g clip-path="url(#rp-rail-{theme_name})">
    <rect class="rail-beam" x="64" y="72.5" width="180" height="3" fill="url(#rp-beam-{theme_name})" />
  </g>

{chr(10).join(nodes_svg)}
</svg>
"""


def render_ecosystem(config: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    eco = config["ecosystem"]
    layers = eco["layers"]
    backbone = eco["backbone"]

    layer_blocks: list[str] = []
    conduit_lines: list[str] = []
    y_positions = [58, 144, 230, 316]

    for idx, layer in enumerate(layers):
        ly = y_positions[idx]
        acc, acc_txt, acc_tint = _accent_pair(t, layer["accent"])
        items = layer["items"]

        # Layer container
        layer_blocks.append(
            f'  <g>\n'
            f'    <rect x="26" y="{ly}" width="644" height="70" rx="10" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1.1" />\n'
            f'    <rect x="26" y="{ly}" width="4" height="70" rx="2" fill="{acc}" />\n'
            f'    <text x="44" y="{ly + 21}" class="mono" font-size="9.8" font-weight="700" fill="{acc_txt}">0{idx + 1} · {esc(layer["title"].upper())}</text>'
        )

        # Render verified technology nodes cleanly spaced inside the stratum.
        count = len(items)
        avail_w = 608.0
        gap = 8.0
        cell_w = (avail_w - gap * (count - 1)) / max(1, count)
        for j, tech in enumerate(items):
            cx = 44.0 + j * (cell_w + gap)
            hi_cls = f"l{idx}-hi" if j < 3 else ""
            layer_blocks.append(
                f'    <rect class="{hi_cls}" x="{cx:.1f}" y="{ly + 31}" width="{cell_w:.1f}" height="28" rx="6" fill="{acc_tint if j == 0 else t["surface_raised"]}" stroke="{acc if j == 0 else t["hairline"]}" stroke-width="1" />\n'
                f'    <text x="{cx + cell_w / 2.0:.1f}" y="{ly + 49}" text-anchor="middle" class="sans" font-size="11.2" font-weight="600" fill="{t["ink"]}">{esc(tech)}</text>'
            )
        layer_blocks.append("  </g>")

        # Vertical inter-layer conduits between strata.
        if idx < len(layers) - 1:
            ny = y_positions[idx + 1]
            for vx in (156, 348, 540):
                conduit_lines.append(
                    f'  <line class="v-flow" x1="{vx}" y1="{ly + 70}" x2="{vx}" y2="{ny}" stroke="{acc}" stroke-width="1.6" />'
                )

        # Horizontal deployment conduit from right Systems Backbone into this stratum.
        mid_y = ly + 35
        conduit_lines.append(
            f'  <line class="h-flow" x1="670" y1="{mid_y}" x2="708" y2="{mid_y}" stroke="{acc}" stroke-width="1.6" />\n'
            f'  <circle class="junc-{idx}" cx="670" cy="{mid_y}" r="3.2" fill="{acc}" />\n'
            f'  <circle cx="708" cy="{mid_y}" r="3.2" fill="{t["emerald"]}" />'
        )

    # Right vertical Systems & Delivery backbone spanning all 4 layers.
    bb_items_svg: list[str] = []
    bb_items = backbone["items"]
    for bi, b_tech in enumerate(bb_items):
        by = 104 + bi * 45
        bb_items_svg.append(
            f'    <rect x="724" y="{by}" width="154" height="34" rx="7" fill="{t["surface_tint_emerald"] if bi in (0, 1, 4) else t["surface_raised"]}" stroke="{t["emerald"] if bi in (0, 1, 4) else t["hairline"]}" stroke-width="1" />\n'
            f'    <text x="801" y="{by + 21}" text-anchor="middle" class="sans" font-size="11.5" font-weight="600" fill="{t["ink"]}">{esc(b_tech)}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 412" width="920" height="412" role="img" aria-labelledby="eco-t-{theme_name} eco-d-{theme_name}">
  <title id="eco-t-{theme_name}">Engineering Ecosystem Architecture</title>
  <desc id="eco-d-{theme_name}">Animated five-layer engineering architecture connecting interface, application APIs, AI agent orchestration, data persistence, and systems delivery.</desc>
  <defs>
    <linearGradient id="eco-bg-{theme_name}" x1="0" y1="0" x2="920" y2="412" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["canvas"]}" />
      <stop offset="100%" stop-color="{t["canvas_alt"]}" />
    </linearGradient>
  </defs>
  <style>
    .sans {{ font-family: {FONT_SANS}; }}
    .mono {{ font-family: {FONT_MONO}; }}
    @media (prefers-reduced-motion: no-preference) {{
      .v-flow {{ stroke-dasharray: 5 5; animation: vMove 1.8s linear infinite; }}
      .h-flow {{ stroke-dasharray: 5 5; animation: hMove 2.1s linear infinite; }}
      .junc-0 {{ animation: jPulse 8s ease-in-out 0s infinite; }}
      .junc-1 {{ animation: jPulse 8s ease-in-out 2s infinite; }}
      .junc-2 {{ animation: jPulse 8s ease-in-out 4s infinite; }}
      .junc-3 {{ animation: jPulse 8s ease-in-out 6s infinite; }}
    }}
    @keyframes vMove {{
      from {{ stroke-dashoffset: 20; }}
      to   {{ stroke-dashoffset: 0; }}
    }}
    @keyframes hMove {{
      from {{ stroke-dashoffset: 0; }}
      to   {{ stroke-dashoffset: 20; }}
    }}
    @keyframes jPulse {{
      0%, 24%   {{ opacity: 1; }}
      34%, 100% {{ opacity: 0.4; }}
    }}
  </style>
  <rect x="0.75" y="0.75" width="918.5" height="410.5" rx="14" fill="url(#eco-bg-{theme_name})" stroke="{t["border"]}" stroke-width="1.2" />
  <text x="26" y="34" class="sans" font-size="15" font-weight="700" fill="{t["ink"]}">System Layer Architecture</text>
  <text x="894" y="34" text-anchor="end" class="mono" font-size="10" fill="{t["ink_muted"]}">INTERFACE  →  SERVICES  →  AI AGENTS  →  DATA</text>
  <line x1="26" y1="45" x2="894" y2="45" stroke="{t["hairline"]}" stroke-width="1" />

{chr(10).join(conduit_lines)}
{chr(10).join(layer_blocks)}

  <!-- Right Systems & Delivery Backbone -->
  <g>
    <rect x="708" y="58" width="186" height="328" rx="10" fill="{t["surface"]}" stroke="{t["emerald"]}" stroke-width="1.2" />
    <text x="724" y="81" class="mono" font-size="9.8" font-weight="700" fill="{t["emerald_text"]}">05 · SYSTEMS &amp; OPS</text>
    <line x1="724" y1="91" x2="878" y2="91" stroke="{t["hairline"]}" stroke-width="1" />
{chr(10).join(bb_items_svg)}
  </g>
</svg>
"""


def render_ai_pipeline(theme_name: str) -> str:
    t = THEMES[theme_name]
    stages = [
        ("01", "Intent Parse", "Schema & context", "cyan"),
        ("02", "Typed Plan", "LangGraph DAG", "violet"),
        ("03", "Approval Gate", "Scoped consent", "amber"),
        ("04", "Sandboxed Run", "Loopback IPC", "emerald"),
        ("05", "Audit Verify", "Exit & SQLite log", "emerald"),
    ]
    blocks: list[str] = []
    conduits: list[str] = []
    stage_w = 152.0
    gap = 24.0
    start_x = 32.0

    for i, (num, title, sub, acc_key) in enumerate(stages):
        x = start_x + i * (stage_w + gap)
        acc, acc_txt, acc_tint = _accent_pair(t, acc_key)
        blocks.append(
            f'  <g>\n'
            f'    <rect class="st-{i}" x="{x:.1f}" y="58" width="{stage_w:.1f}" height="82" rx="9" fill="{t["surface"]}" stroke="{acc}" stroke-width="1.2" />\n'
            f'    <rect x="{x + 12:.1f}" y="70" width="24" height="3" rx="1.5" fill="{acc}" />\n'
            f'    <text x="{x + 12:.1f}" y="90" class="mono" font-size="9.5" font-weight="700" fill="{acc_txt}">{num}</text>\n'
            f'    <text x="{x + 12:.1f}" y="110" class="sans" font-size="13.2" font-weight="700" fill="{t["ink"]}">{esc(title)}</text>\n'
            f'    <text x="{x + 12:.1f}" y="127" class="mono" font-size="9.6" fill="{t["ink_muted"]}">{esc(sub)}</text>\n'
            f'  </g>'
        )
        if i < len(stages) - 1:
            x1 = x + stage_w
            x2 = x1 + gap
            conduits.append(
                f'  <line class="ai-flow" x1="{x1:.1f}" y1="99" x2="{x2:.1f}" y2="99" stroke="{acc}" stroke-width="1.8" />'
            )

    st_css = "\n".join(
        f"      .st-{i} {{ animation: stPulse 10s ease-in-out {i * 2.0:.1f}s infinite; }}"
        for i in range(len(stages))
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 220" width="920" height="220" role="img" aria-labelledby="ai-t-{theme_name} ai-d-{theme_name}">
  <title id="ai-t-{theme_name}">Deterministic Human-in-the-Loop AI Engineering Loop</title>
  <desc id="ai-d-{theme_name}">Five-stage agent execution architecture: Intent Parse, Typed Plan, Approval Gate, Sandboxed Run, and Audit Verify with verification feedback.</desc>
  <defs>
    <linearGradient id="ai-bg-{theme_name}" x1="0" y1="0" x2="920" y2="220" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["canvas"]}" />
      <stop offset="100%" stop-color="{t["canvas_alt"]}" />
    </linearGradient>
  </defs>
  <style>
    .sans {{ font-family: {FONT_SANS}; }}
    .mono {{ font-family: {FONT_MONO}; }}
    @media (prefers-reduced-motion: no-preference) {{
      .ai-flow {{ stroke-dasharray: 6 5; animation: aiDash 1.6s linear infinite; }}
      .fb-loop {{ stroke-dasharray: 8 6; animation: fbDash 3.2s linear infinite; }}
{st_css}
    }}
    @keyframes aiDash {{
      from {{ stroke-dashoffset: 22; }}
      to   {{ stroke-dashoffset: 0; }}
    }}
    @keyframes fbDash {{
      from {{ stroke-dashoffset: 0; }}
      to   {{ stroke-dashoffset: 28; }}
    }}
    @keyframes stPulse {{
      0%, 18%   {{ stroke-width: 2.0; }}
      26%, 100% {{ stroke-width: 1.15; }}
    }}
  </style>
  <rect x="0.75" y="0.75" width="918.5" height="218.5" rx="14" fill="url(#ai-bg-{theme_name})" stroke="{t["border"]}" stroke-width="1.2" />
  <text x="32" y="34" class="sans" font-size="14.5" font-weight="700" fill="{t["ink"]}">Deterministic Agent Execution Pattern</text>
  <text x="888" y="34" text-anchor="end" class="mono" font-size="9.8" fill="{t["violet_text"]}">APPLIED IN AGENTOS · OMNIDESK · TALENTOS</text>
  <line x1="32" y1="45" x2="888" y2="45" stroke="{t["hairline"]}" stroke-width="1" />

{chr(10).join(conduits)}
{chr(10).join(blocks)}

  <!-- Verification feedback arc looping back from Verify (stage 5) to Typed Plan (stage 2) -->
  <path d="M 812 140 L 812 178 C 812 184 806 188 800 188 L 296 188 C 290 188 284 184 284 178 L 284 140" fill="none" stroke="{t["violet"]}" stroke-opacity="0.3" stroke-width="1.5" />
  <path class="fb-loop" d="M 812 140 L 812 178 C 812 184 806 188 800 188 L 296 188 C 290 188 284 184 284 178 L 284 140" fill="none" stroke="{t["violet"]}" stroke-width="1.5" />
  <rect x="444" y="177" width="208" height="22" rx="5" fill="{t["surface"]}" stroke="{t["border"]}" stroke-width="1" />
  <text x="548" y="191.5" text-anchor="middle" class="mono" font-size="9.4" font-weight="600" fill="{t["violet_text"]}">VERIFICATION FEEDBACK LOOP</text>
</svg>
"""


def render_analytics_overview(data: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    stats = data.get("stats", {})
    langs = data.get("languages", [])[:6]
    updated = data.get("updated_date_utc", "")

    total_pct = sum(item["pct"] for item in langs) or 100.0

    # Assign distinct ordered palette colors so every chart segment is visually separable.
    palette = t["lang_palette"]
    bar_x = 392.0
    avail_w = 496.0
    gap = 2.5
    usable_w = avail_w - gap * max(0, len(langs) - 1)
    bar_segs: list[str] = []
    for i, item in enumerate(langs):
        seg_w = max(5.0, (item["pct"] / total_pct) * usable_w)
        col = palette[i % len(palette)]
        bar_segs.append(
            f'    <rect x="{bar_x:.1f}" y="66" width="{seg_w:.1f}" height="10" fill="{col}" />'
        )
        bar_x += seg_w + gap

    # Accurate radial donut chart segments centered at (474, 176), r=52.
    cx, cy, radius = 474.0, 176.0, 52.0
    circumference = 2.0 * math.pi * radius
    donut_arcs: list[str] = []
    offset_acc = 0.0
    for i, item in enumerate(langs):
        frac = item["pct"] / total_pct
        seg_len = max(2.0, frac * circumference - 2.5)
        col = palette[i % len(palette)]
        donut_arcs.append(
            f'    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" fill="none" stroke="{col}" '
            f'stroke-width="13" stroke-dasharray="{seg_len:.2f} {circumference:.2f}" '
            f'stroke-dashoffset="{-offset_acc:.2f}" transform="rotate(-90 {cx:.1f} {cy:.1f})" />'
        )
        offset_acc += frac * circumference

    # Tabular language legend to the right of donut.
    legend_rows: list[str] = []
    for i, item in enumerate(langs):
        ry = 116 + i * 24
        col = palette[i % len(palette)]
        legend_rows.append(
            f'  <g>\n'
            f'    <rect x="572" y="{ry - 9}" width="9" height="9" rx="2" fill="{col}" />\n'
            f'    <text x="589" y="{ry}" class="sans" font-size="12.5" font-weight="600" fill="{t["ink"]}">{esc(item["name"])}</text>\n'
            f'    <text x="888" y="{ry}" text-anchor="end" class="mono" font-size="11.5" font-weight="600" fill="{t["ink_sec"]}">{item["pct"]:.1f}%</text>\n'
            f'    <line x1="572" y1="{ry + 8}" x2="888" y2="{ry + 8}" stroke="{t["hairline"]}" stroke-width="0.8" />\n'
            f'  </g>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 278" width="920" height="278" role="img" aria-labelledby="ov-t-{theme_name} ov-d-{theme_name}">
  <title id="ov-t-{theme_name}">Public Engineering Overview and Language Distribution</title>
  <desc id="ov-d-{theme_name}">Verified public GitHub statistics ({stats.get("total_contributions", 0)} public contributions across {stats.get("public_repos", 0)} public repositories) and byte-weighted language distribution.</desc>
  <defs>
    <linearGradient id="ov-bg-{theme_name}" x1="0" y1="0" x2="920" y2="278" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["canvas"]}" />
      <stop offset="100%" stop-color="{t["canvas_alt"]}" />
    </linearGradient>
    <linearGradient id="ov-sheen-{theme_name}" x1="0" y1="0" x2="120" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0" />
      <stop offset="50%" stop-color="#FFFFFF" stop-opacity="0.35" />
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0" />
    </linearGradient>
    <clipPath id="ov-bar-clip-{theme_name}">
      <rect x="392" y="66" width="496" height="10" rx="5" />
    </clipPath>
  </defs>
  <style>
    .sans {{ font-family: {FONT_SANS}; }}
    .mono {{ font-family: {FONT_MONO}; }}
    .sheen {{ opacity: 0; }}
    @media (prefers-reduced-motion: no-preference) {{
      .sheen {{ animation: sheenRun 6.8s cubic-bezier(0.4, 0, 0.2, 1) infinite; }}
      .donut-spin {{ transform-origin: 474px 176px; animation: donutEase 1.1s cubic-bezier(0.16, 1, 0.3, 1) both; }}
    }}
    @keyframes sheenRun {{
      0%        {{ transform: translateX(-110px); opacity: 0; }}
      18%, 78%  {{ opacity: 1; }}
      94%, 100% {{ transform: translateX(520px); opacity: 0; }}
    }}
    @keyframes donutEase {{
      from {{ transform: rotate(-28deg); opacity: 0.4; }}
      to   {{ transform: rotate(0deg); opacity: 1; }}
    }}
  </style>
  <rect x="0.75" y="0.75" width="918.5" height="276.5" rx="14" fill="url(#ov-bg-{theme_name})" stroke="{t["border"]}" stroke-width="1.2" />

  <!-- Left editorial KPI ledger -->
  <text x="30" y="34" class="sans" font-size="14.5" font-weight="700" fill="{t["ink"]}">Public Engineering Scope</text>
  <text x="30" y="51" class="mono" font-size="9.5" fill="{t["ink_muted"]}">TRAILING 52 WEEKS  ·  SYNC {esc(updated)}</text>

  <text x="30" y="112" class="mono" font-size="44" font-weight="700" fill="{t["emerald_text"]}" letter-spacing="-0.03em">{stats.get("total_contributions", 0)}</text>
  <text x="30" y="132" class="sans" font-size="12.5" font-weight="600" fill="{t["ink_sec"]}">Public Contributions</text>

  <line x1="30" y1="150" x2="346" y2="150" stroke="{t["hairline"]}" stroke-width="1" />

  <text x="30" y="176" class="mono" font-size="20" font-weight="700" fill="{t["ink"]}">{stats.get("public_repos", 0)}</text>
  <text x="30" y="193" class="sans" font-size="11" fill="{t["ink_muted"]}">Public Repositories</text>

  <text x="196" y="176" class="mono" font-size="20" font-weight="700" fill="{t["cyan_text"]}">{stats.get("public_commits", 0)}</text>
  <text x="196" y="193" class="sans" font-size="11" fill="{t["ink_muted"]}">Public Commits</text>

  <line x1="30" y1="208" x2="346" y2="208" stroke="{t["hairline"]}" stroke-width="1" />

  <text x="30" y="234" class="mono" font-size="20" font-weight="700" fill="{t["amber_text"]}">{stats.get("total_stars", 0)}</text>
  <text x="30" y="251" class="sans" font-size="11" fill="{t["ink_muted"]}">Stars Earned</text>

  <text x="196" y="234" class="mono" font-size="20" font-weight="700" fill="{t["violet_text"]}">{stats.get("active_days", 0)}d / {stats.get("longest_streak", 0)}d</text>
  <text x="196" y="251" class="sans" font-size="11" fill="{t["ink_muted"]}">Active Days / Peak Streak</text>

  <!-- Vertical separator -->
  <line x1="366" y1="22" x2="366" y2="256" stroke="{t["hairline"]}" stroke-width="1" />

  <!-- Right language spectrum & radial ring -->
  <text x="392" y="34" class="sans" font-size="14.5" font-weight="700" fill="{t["ink"]}">Language Distribution</text>
  <text x="888" y="34" text-anchor="end" class="mono" font-size="9.5" fill="{t["ink_muted"]}">OWNED NON-FORK PUBLIC REPOS (BY BYTES)</text>

  <rect x="392" y="66" width="496" height="10" rx="5" fill="{t["surface_raised"]}" />
  <g clip-path="url(#ov-bar-clip-{theme_name})">
{chr(10).join(bar_segs)}
    <rect class="sheen" x="392" y="66" width="120" height="10" fill="url(#ov-sheen-{theme_name})" />
  </g>

  <g class="donut-spin">
    <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" fill="none" stroke="{t["surface_raised"]}" stroke-width="13" />
{chr(10).join(donut_arcs)}
  </g>
  <text x="{cx:.1f}" y="{cy - 2:.1f}" text-anchor="middle" class="mono" font-size="20" font-weight="700" fill="{t["ink"]}">{len(langs)}</text>
  <text x="{cx:.1f}" y="{cy + 14:.1f}" text-anchor="middle" class="mono" font-size="9.2" fill="{t["ink_muted"]}">LANGUAGES</text>

{chr(10).join(legend_rows)}
</svg>
"""


def _smooth_spline(pts: list[tuple[float, float]], base_y: float) -> tuple[str, str]:
    if not pts:
        return "", ""
    if len(pts) == 1:
        x, y = pts[0]
        return f"M {x:.1f} {y:.1f}", f"M {x:.1f} {base_y:.1f} L {x:.1f} {y:.1f} Z"
    segs = [f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"]
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        cx1 = x0 + (x1 - x0) * 0.42
        cx2 = x1 - (x1 - x0) * 0.42
        segs.append(f"C {cx1:.1f} {y0:.1f}, {cx2:.1f} {y1:.1f}, {x1:.1f} {y1:.1f}")
    curve = " ".join(segs)
    area = (
        f"M {pts[0][0]:.1f} {base_y:.1f} L {pts[0][0]:.1f} {pts[0][1]:.1f} "
        + " ".join(segs[1:])
        + f" L {pts[-1][0]:.1f} {base_y:.1f} Z"
    )
    return curve, area


def render_analytics_velocity(data: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    weekly = data.get("weekly_totals", [])
    repo_commits = data.get("repo_commits", [])[:6]
    max_wk = max((int(w["count"]) for w in weekly), default=1)
    max_scale = max(4, ((max_wk + 3) // 4) * 4)

    chart_x, chart_y, chart_w, chart_h = 46.0, 68.0, 514.0, 152.0
    n = max(1, len(weekly) - 1)
    pts: list[tuple[float, float, int, str]] = []
    for i, w in enumerate(weekly):
        px = chart_x + (i / n) * chart_w
        py = chart_y + chart_h - (int(w["count"]) / max_scale) * chart_h
        pts.append((px, py, int(w["count"]), w["first_day"]))

    curve, area = _smooth_spline([(x, y) for x, y, _, _ in pts], chart_y + chart_h)

    grid_svg: list[str] = []
    for frac in (0.0, 0.5, 1.0):
        gy = chart_y + chart_h - frac * chart_h
        gval = int(round(frac * max_scale))
        grid_svg.append(
            f'  <line x1="{chart_x:.0f}" y1="{gy:.1f}" x2="{chart_x + chart_w:.0f}" y2="{gy:.1f}" stroke="{t["hairline"]}" stroke-width="1" />\n'
            f'  <text x="{chart_x - 8:.0f}" y="{gy + 3.5:.1f}" text-anchor="end" class="mono" font-size="9.5" fill="{t["ink_muted"]}">{gval}</text>'
        )

    # Proportional weekly vertical impulse bars under spline.
    bars_svg: list[str] = []
    for px, py, cnt, _ in pts:
        if cnt > 0:
            bh = max(3.0, (chart_y + chart_h) - py)
            bars_svg.append(
                f'  <rect x="{px - 2.6:.1f}" y="{py:.1f}" width="5.2" height="{bh:.1f}" rx="2" fill="{t["cyan"]}" fill-opacity="0.28" />'
            )

    month_svg: list[str] = []
    seen_m: set[str] = set()
    last_x = -99.0
    for px, _, _, first_day in pts:
        ym = first_day[:7]
        if ym not in seen_m:
            seen_m.add(ym)
            lbl = dt.date.fromisoformat(first_day).strftime("%b")
            if px - last_x >= 44.0 and px <= chart_x + chart_w - 16:
                month_svg.append(
                    f'  <text x="{px:.1f}" y="242" class="mono" font-size="9.5" fill="{t["ink_muted"]}">{lbl}</text>'
                )
                last_x = px

    # Right panel: Public repository commit distribution (excludes profile refresh repo).
    max_rc = max((int(r["commits"]) for r in repo_commits), default=1)
    rc_colors = [t["emerald"], t["cyan"], t["violet"], t["amber"], t["emerald"], t["cyan"]]
    rc_svg: list[str] = []
    for idx, rc in enumerate(repo_commits):
        ry = 78 + idx * 32
        bar_max_w = 276.0
        fill_w = max(8.0, (int(rc["commits"]) / max_rc) * bar_max_w)
        col = rc_colors[idx % len(rc_colors)]
        rc_svg.append(
            f'  <g>\n'
            f'    <text x="606" y="{ry}" class="sans" font-size="12" font-weight="600" fill="{t["ink"]}">{esc(truncate(rc["repo"], 20))}</text>\n'
            f'    <text x="884" y="{ry}" text-anchor="end" class="mono" font-size="11" font-weight="600" fill="{t["ink_sec"]}">{rc["commits"]} commits</text>\n'
            f'    <rect x="606" y="{ry + 7}" width="{bar_max_w:.0f}" height="7" rx="3.5" fill="{t["surface_raised"]}" />\n'
            f'    <rect class="rc-bar" x="606" y="{ry + 7}" width="{fill_w:.1f}" height="7" rx="3.5" fill="{col}" />\n'
            f'  </g>'
        )

    if not rc_svg:
        rc_svg.append(
            f'  <text x="606" y="130" class="sans" font-size="12" fill="{t["ink_muted"]}">Public commit distribution updates on authenticated sync.</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 282" width="920" height="282" role="img" aria-labelledby="vel-t-{theme_name} vel-d-{theme_name}">
  <title id="vel-t-{theme_name}">Weekly Development Velocity and Repository Commit Focus</title>
  <desc id="vel-d-{theme_name}">Trailing 52-week public contribution curve peaking at {max_wk} per week alongside public commit counts across owned product repositories.</desc>
  <defs>
    <linearGradient id="vel-bg-{theme_name}" x1="0" y1="0" x2="920" y2="282" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["canvas"]}" />
      <stop offset="100%" stop-color="{t["canvas_alt"]}" />
    </linearGradient>
    <linearGradient id="vel-area-{theme_name}" x1="0" y1="68" x2="0" y2="220" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["emerald"]}" stop-opacity="0.28" />
      <stop offset="100%" stop-color="{t["emerald"]}" stop-opacity="0.01" />
    </linearGradient>
  </defs>
  <style>
    .sans {{ font-family: {FONT_SANS}; }}
    .mono {{ font-family: {FONT_MONO}; }}
    .vel-pulse {{ opacity: 0; }}
    .rc-bar {{ transform-origin: 606px 0px; }}
    @media (prefers-reduced-motion: no-preference) {{
      .vel-pulse {{ opacity: 1; stroke-dasharray: 96 904; animation: traceCurve 6.2s cubic-bezier(0.4, 0, 0.2, 1) infinite; }}
      .rc-bar {{ animation: growBar 0.9s cubic-bezier(0.16, 1, 0.3, 1) both; }}
    }}
    @keyframes traceCurve {{
      0%   {{ stroke-dashoffset: 1000; opacity: 0; }}
      12%  {{ opacity: 1; }}
      88%  {{ opacity: 1; }}
      100% {{ stroke-dashoffset: 0; opacity: 0; }}
    }}
    @keyframes growBar {{
      from {{ transform: scaleX(0); }}
      to   {{ transform: scaleX(1); }}
    }}
  </style>
  <rect x="0.75" y="0.75" width="918.5" height="280.5" rx="14" fill="url(#vel-bg-{theme_name})" stroke="{t["border"]}" stroke-width="1.2" />

  <text x="30" y="34" class="sans" font-size="14.5" font-weight="700" fill="{t["ink"]}">Weekly Contribution Velocity</text>
  <text x="560" y="34" text-anchor="end" class="mono" font-size="9.8" fill="{t["emerald_text"]}">PEAK {max_wk}/WK  ·  52 WEEKS</text>
  <line x1="30" y1="46" x2="560" y2="46" stroke="{t["hairline"]}" stroke-width="1" />

{chr(10).join(grid_svg)}
{chr(10).join(bars_svg)}
  <path d="{area}" fill="url(#vel-area-{theme_name})" />
  <path d="{curve}" fill="none" stroke="{t["emerald"]}" stroke-width="2" stroke-linecap="round" />
  <path class="vel-pulse" pathLength="1000" d="{curve}" fill="none" stroke="{t["cyan"]}" stroke-width="2.6" stroke-linecap="round" />
{chr(10).join(month_svg)}

  <line x1="584" y1="22" x2="584" y2="260" stroke="{t["hairline"]}" stroke-width="1" />

  <text x="606" y="34" class="sans" font-size="14.5" font-weight="700" fill="{t["ink"]}">Repository Commit Focus</text>
  <text x="884" y="34" text-anchor="end" class="mono" font-size="9.5" fill="{t["ink_muted"]}">PUBLIC PRODUCT REPOS</text>
  <line x1="606" y1="46" x2="884" y2="46" stroke="{t["hairline"]}" stroke-width="1" />
{chr(10).join(rc_svg)}
</svg>
"""


def render_heatmap(data: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    days = data.get("calendar_days", [])
    stats = data.get("stats", {})
    updated = data.get("updated_date_utc", "")

    # Group real calendar days into Sunday-starting columns matching GitHub's grid.
    columns: list[list[dict[str, Any] | None]] = []
    cur_col: list[dict[str, Any] | None] = [None] * 7
    has_any = False
    for item in days:
        d_obj = dt.date.fromisoformat(item["date"])
        # Python weekday(): Mon=0..Sat=5, Sun=6 -> Sunday row index 0.
        row_idx = (d_obj.weekday() + 1) % 7
        if row_idx == 0 and has_any:
            columns.append(cur_col)
            cur_col = [None] * 7
        cur_col[row_idx] = item
        has_any = True
    if has_any:
        columns.append(cur_col)

    columns = columns[-53:]
    max_day = max((int(d["count"]) for d in days), default=1) or 1

    cell = 12.4
    gap = 3.1
    step = cell + gap
    grid_x = 58.0
    grid_y = 74.0

    cells_svg: list[str] = []
    active_clip: list[str] = []
    month_svg: list[str] = []
    seen_ym: set[str] = set()
    last_mx = -100.0

    for col_i, col_days in enumerate(columns):
        cx = grid_x + col_i * step
        first_valid = next((d for d in col_days if d is not None), None)
        if first_valid:
            ym = first_valid["date"][:7]
            if ym not in seen_ym:
                seen_ym.add(ym)
                lbl = dt.date.fromisoformat(first_valid["date"]).strftime("%b")
                if cx - last_mx >= 40.0 and cx <= 868.0:
                    month_svg.append(
                        f'  <text x="{cx:.1f}" y="62" class="mono" font-size="9.5" fill="{t["ink_muted"]}">{lbl}</text>'
                    )
                    last_mx = cx

        for row_i, day_item in enumerate(col_days):
            if day_item is None:
                continue
            cy = grid_y + row_i * step
            cnt = int(day_item["count"])
            if cnt == 0:
                fill = t["heat_0"]
            elif cnt <= max(1, max_day * 0.2):
                fill = t["heat_1"]
            elif cnt <= max(2, max_day * 0.45):
                fill = t["heat_2"]
            elif cnt <= max(4, max_day * 0.75):
                fill = t["heat_3"]
            else:
                fill = t["heat_4"]

            cells_svg.append(
                f'    <rect x="{cx:.1f}" y="{cy:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="2.5" fill="{fill}" />'
            )
            if cnt > 0:
                active_clip.append(
                    f'      <rect x="{cx:.1f}" y="{cy:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="2.5" />'
                )

    weekday_labels = [
        (1, "Mon"),
        (3, "Wed"),
        (5, "Fri"),
    ]
    wd_svg = [
        f'  <text x="48" y="{grid_y + r * step + 9.5:.1f}" text-anchor="end" class="mono" font-size="9.2" fill="{t["ink_muted"]}">{lbl}</text>'
        for r, lbl in weekday_labels
    ]

    legend_colors = [t["heat_0"], t["heat_1"], t["heat_2"], t["heat_3"], t["heat_4"]]
    legend_svg = [
        f'  <rect x="{774 + i * 16}" y="198" width="11" height="11" rx="2.2" fill="{c}" />'
        for i, c in enumerate(legend_colors)
    ]

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 232" width="920" height="232" role="img" aria-labelledby="hm-t-{theme_name} hm-d-{theme_name}">
  <title id="hm-t-{theme_name}">Annual Public Contribution Heatmap</title>
  <desc id="hm-d-{theme_name}">52-week public GitHub contribution calendar showing {stats.get("total_contributions", 0)} public contributions across {stats.get("active_days", 0)} active days, peaking at {stats.get("peak_day", 0)} in a single day.</desc>
  <defs>
    <linearGradient id="hm-bg-{theme_name}" x1="0" y1="0" x2="920" y2="232" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["canvas"]}" />
      <stop offset="100%" stop-color="{t["canvas_alt"]}" />
    </linearGradient>
    <linearGradient id="hm-scan-{theme_name}" x1="0" y1="0" x2="140" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0" />
      <stop offset="50%" stop-color="#FFFFFF" stop-opacity="0.42" />
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0" />
    </linearGradient>
    <clipPath id="hm-active-{theme_name}">
{chr(10).join(active_clip) if active_clip else '      <rect x="0" y="0" width="0" height="0" />'}
    </clipPath>
  </defs>
  <style>
    .sans {{ font-family: {FONT_SANS}; }}
    .mono {{ font-family: {FONT_MONO}; }}
    .hm-wave {{ opacity: 0; }}
    @media (prefers-reduced-motion: no-preference) {{
      .hm-wave {{ animation: hmPass 7.5s cubic-bezier(0.4, 0, 0.2, 1) infinite; }}
    }}
    @keyframes hmPass {{
      0%        {{ transform: translateX(-140px); opacity: 0; }}
      14%, 82%  {{ opacity: 0.95; }}
      96%, 100% {{ transform: translateX(880px); opacity: 0; }}
    }}
  </style>
  <rect x="0.75" y="0.75" width="918.5" height="230.5" rx="14" fill="url(#hm-bg-{theme_name})" stroke="{t["border"]}" stroke-width="1.2" />

  <text x="28" y="32" class="sans" font-size="14.5" font-weight="700" fill="{t["ink"]}">Annual Contribution Heatmap</text>
  <text x="892" y="32" text-anchor="end" class="mono" font-size="9.8" fill="{t["emerald_text"]}">{stats.get("total_contributions", 0)} PUBLIC CONTRIBUTIONS  ·  PEAK {stats.get("peak_day", 0)}/DAY  ·  {stats.get("active_days", 0)} ACTIVE DAYS</text>
  <line x1="28" y1="44" x2="892" y2="44" stroke="{t["hairline"]}" stroke-width="1" />

{chr(10).join(month_svg)}
{chr(10).join(wd_svg)}

  <g aria-hidden="true">
{chr(10).join(cells_svg)}
  </g>
  <g clip-path="url(#hm-active-{theme_name})" aria-hidden="true">
    <rect class="hm-wave" x="58" y="70" width="140" height="114" fill="url(#hm-scan-{theme_name})" />
  </g>

  <text x="28" y="208" class="mono" font-size="9.4" fill="{t["ink_muted"]}">PUBLIC GITHUB CALENDAR  ·  UPDATED {esc(updated)} UTC</text>
  <text x="766" y="207.5" text-anchor="end" class="mono" font-size="9.2" fill="{t["ink_muted"]}">Less</text>
{chr(10).join(legend_svg)}
  <text x="860" y="207.5" class="mono" font-size="9.2" fill="{t["ink_muted"]}">More</text>
</svg>
"""


def render_footer(config: dict[str, Any], theme_name: str) -> str:
    t = THEMES[theme_name]
    ident = config["identity"]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 920 74" width="920" height="74" role="img" aria-labelledby="ft-t-{theme_name} ft-d-{theme_name}">
  <title id="ft-t-{theme_name}">{esc(ident["name"])}: Full-Stack Engineering, AI Systems, Software Architecture</title>
  <desc id="ft-d-{theme_name}">Minimal animated architectural closing signature.</desc>
  <defs>
    <linearGradient id="ft-line-{theme_name}" x1="0" y1="0" x2="920" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["border"]}" stop-opacity="0.2" />
      <stop offset="50%" stop-color="{t["border_strong"]}" stop-opacity="1" />
      <stop offset="100%" stop-color="{t["border"]}" stop-opacity="0.2" />
    </linearGradient>
    <linearGradient id="ft-beam-{theme_name}" x1="0" y1="0" x2="200" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0%" stop-color="{t["emerald"]}" stop-opacity="0" />
      <stop offset="50%" stop-color="{t["cyan"]}" stop-opacity="0.95" />
      <stop offset="100%" stop-color="{t["violet"]}" stop-opacity="0" />
    </linearGradient>
    <clipPath id="ft-clip-{theme_name}">
      <rect x="0" y="8" width="920" height="6" />
    </clipPath>
  </defs>
  <style>
    .sans {{ font-family: {FONT_SANS}; }}
    .mono {{ font-family: {FONT_MONO}; }}
    .ft-sweep {{ opacity: 0; }}
    @media (prefers-reduced-motion: no-preference) {{
      .ft-sweep {{ animation: ftPass 8.5s cubic-bezier(0.4, 0, 0.2, 1) infinite; }}
    }}
    @keyframes ftPass {{
      0%        {{ transform: translateX(-200px); opacity: 0; }}
      15%, 78%  {{ opacity: 0.95; }}
      95%, 100% {{ transform: translateX(940px); opacity: 0; }}
    }}
  </style>

  <line x1="0" y1="11" x2="920" y2="11" stroke="url(#ft-line-{theme_name})" stroke-width="1" />
  <g clip-path="url(#ft-clip-{theme_name})">
    <rect class="ft-sweep" x="0" y="10" width="200" height="2" fill="url(#ft-beam-{theme_name})" />
  </g>

  <!-- Centered 4-domain motif echoing hero -->
  <rect x="424" y="9.5" width="18" height="3" rx="1" fill="{t["emerald"]}" />
  <rect x="445" y="9.5" width="16" height="3" rx="1" fill="{t["cyan"]}" />
  <rect x="464" y="9.5" width="14" height="3" rx="1" fill="{t["violet"]}" />
  <rect x="481" y="9.5" width="12" height="3" rx="1" fill="{t["amber"]}" />

  <text x="16" y="48" class="sans" font-size="13.5" font-weight="700" fill="{t["ink"]}" letter-spacing="-0.01em">{esc(ident["name"])}</text>
  <text x="460" y="48" text-anchor="middle" class="mono" font-size="10.8" font-weight="600" fill="{t["emerald_text"]}">Full-Stack Engineering  ·  AI Systems  ·  Architecture</text>
  <text x="904" y="48" text-anchor="end" class="mono" font-size="10.5" fill="{t["ink_muted"]}">{esc(ident["coordinates"])}</text>
</svg>
"""


def generate_all_visuals(repo_root: Path, config: dict[str, Any], data: dict[str, Any]) -> list[Path]:
    """Render, XML-validate, and write the complete dark and light SVG suite."""
    assets_dir = repo_root / "assets"
    repo_map = {r["name"].lower(): r for r in data.get("repos", [])}
    featured_by_slug = {p["slug"]: p for p in config.get("featured_projects", [])}

    render_plan: list[tuple[Path, str]] = []
    for theme_name in ("dark", "light"):
        sfx = THEMES[theme_name]["suffix"]
        render_plan.append((assets_dir / "hero" / f"hero-{sfx}.svg", render_hero(config, data, theme_name)))

        for slug, renderer in (
            ("agentos", render_project_agentos),
            ("omnidesk", render_project_omnidesk),
            ("ledger", render_project_ledger),
            ("talentos", render_project_talentos),
            ("infraos", render_project_infraos),
        ):
            meta = featured_by_slug[slug]
            live = repo_map.get(meta["repo"].lower(), {})
            render_plan.append((assets_dir / "projects" / f"{slug}-{sfx}.svg", renderer(meta, live, theme_name)))

        render_plan.append(
            (assets_dir / "ecosystem" / f"stack-architecture-{sfx}.svg", render_ecosystem(config, theme_name))
        )
        render_plan.append(
            (assets_dir / "ecosystem" / f"ai-pipeline-{sfx}.svg", render_ai_pipeline(theme_name))
        )
        render_plan.append(
            (assets_dir / "analytics" / f"overview-{sfx}.svg", render_analytics_overview(data, theme_name))
        )
        render_plan.append(
            (assets_dir / "analytics" / f"velocity-{sfx}.svg", render_analytics_velocity(data, theme_name))
        )
        render_plan.append(
            (assets_dir / "analytics" / f"recent-pulse-{sfx}.svg", render_recent_pulse(data, theme_name))
        )
        render_plan.append(
            (assets_dir / "analytics" / f"heatmap-{sfx}.svg", render_heatmap(data, theme_name))
        )
        render_plan.append(
            (assets_dir / "footer" / f"signature-{sfx}.svg", render_footer(config, theme_name))
        )

    written: list[Path] = []
    for target, svg_text in render_plan:
        validate_svg(svg_text)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(svg_text, encoding="utf-8")
        written.append(target)
    return written
