"""WCAG AA verified color tokens, domain palettes, and SVG utility helpers."""

from __future__ import annotations

import html
import xml.etree.ElementTree as ET
from typing import Any

FONT_SANS = '-apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif'
FONT_MONO = 'ui-monospace, "SF Mono", Menlo, Consolas, monospace'

# Every foreground/background text pair below is verified >= 4.5:1 WCAG AA.
THEMES: dict[str, dict[str, Any]] = {
    "dark": {
        "suffix": "dark",
        "canvas": "#101820",
        "canvas_alt": "#0C131A",
        "surface": "#16212C",
        "surface_raised": "#1B2836",
        "surface_tint_emerald": "#112924",
        "surface_tint_cyan": "#102731",
        "surface_tint_violet": "#1E1B33",
        "surface_tint_amber": "#2A2215",
        "border": "#263646",
        "border_strong": "#33485C",
        "hairline": "#1E2C3A",
        "grid": "#1B2836",
        "ink": "#F8FAFC",
        "ink_sec": "#CBD5E1",
        "ink_muted": "#94A3B8",
        "emerald": "#10B981",
        "emerald_text": "#34D399",
        "emerald_soft": "#163D33",
        "cyan": "#22D3EE",
        "cyan_text": "#22D3EE",
        "cyan_soft": "#133B46",
        "violet": "#8B5CF6",
        "violet_text": "#C4B5FD",
        "violet_soft": "#2A224B",
        "amber": "#F59E0B",
        "amber_text": "#FBBF24",
        "amber_soft": "#3D2E14",
        "heat_0": "#17232F",
        "heat_1": "#0E4A3A",
        "heat_2": "#059669",
        "heat_3": "#10B981",
        "heat_4": "#22D3EE",
        "lang_palette": [
            "#22D3EE",
            "#8B5CF6",
            "#F59E0B",
            "#10B981",
            "#38BDF8",
            "#94A3B8",
            "#A78BFA",
        ],
    },
    "light": {
        "suffix": "light",
        "canvas": "#F8FAFC",
        "canvas_alt": "#F1F5F9",
        "surface": "#FFFFFF",
        "surface_raised": "#F1F5F9",
        "surface_tint_emerald": "#ECFDF5",
        "surface_tint_cyan": "#ECFEFF",
        "surface_tint_violet": "#F5F3FF",
        "surface_tint_amber": "#FFFBEB",
        "border": "#CBD5E1",
        "border_strong": "#94A3B8",
        "hairline": "#E2E8F0",
        "grid": "#E2E8F0",
        "ink": "#0F172A",
        "ink_sec": "#334155",
        "ink_muted": "#475569",
        "emerald": "#059669",
        "emerald_text": "#047857",
        "emerald_soft": "#D1FAE5",
        "cyan": "#0891B2",
        "cyan_text": "#0E7490",
        "cyan_soft": "#CFFAFE",
        "violet": "#7C3AED",
        "violet_text": "#6D28D9",
        "violet_soft": "#EDE9FE",
        "amber": "#D97706",
        "amber_text": "#B45309",
        "amber_soft": "#FEF3C7",
        "heat_0": "#E2E8F0",
        "heat_1": "#A7F3D0",
        "heat_2": "#34D399",
        "heat_3": "#059669",
        "heat_4": "#0891B2",
        "lang_palette": [
            "#0891B2",
            "#7C3AED",
            "#D97706",
            "#059669",
            "#0284C7",
            "#475569",
            "#6D28D9",
        ],
    },
}

LANGUAGE_ACCENT_KEY: dict[str, str] = {
    "TypeScript": "cyan",
    "JavaScript": "amber",
    "Python": "violet",
    "Java": "amber",
    "Go": "cyan",
    "Rust": "amber",
    "PHP": "violet",
    "Blade": "emerald",
    "CSS": "cyan",
    "HTML": "emerald",
    "Shell": "emerald",
    "HCL": "violet",
}


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def truncate(text: str, max_len: int) -> str:
    clean = " ".join(str(text or "").split())
    if len(clean) <= max_len:
        return clean
    return clean[: max_len - 3].rstrip() + "..."


def lang_color(lang: str, theme: dict[str, Any], fallback_idx: int = 0) -> str:
    key = LANGUAGE_ACCENT_KEY.get(lang)
    if key and key in theme:
        return theme[key]
    palette = theme["lang_palette"]
    return palette[fallback_idx % len(palette)]


def validate_svg(svg_text: str) -> None:
    ET.fromstring(svg_text)
