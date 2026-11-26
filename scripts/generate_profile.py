#!/usr/bin/env python3
"""Main profile orchestrator: fetch public GitHub data, render SVGs, and update README."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_visuals import generate_all_visuals
from github_api import fetch_profile_dataset
from update_readme import update_readme

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "profile.json"
DATA_PATH = REPO_ROOT / "data" / "profile.json"
README_PATH = REPO_ROOT / "README.md"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh GitHub profile data, SVGs, and README.")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip GitHub API calls and render from existing data/profile.json.",
    )
    parser.add_argument(
        "--allow-fallback",
        action="store_true",
        help="Fall back to existing data/profile.json if live API refresh fails.",
    )
    args = parser.parse_args(argv)

    config = _load_json(CONFIG_PATH)

    dataset: dict[str, Any]
    if args.offline:
        if not DATA_PATH.exists():
            raise RuntimeError(f"Offline mode requested but {DATA_PATH} does not exist.")
        dataset = _load_json(DATA_PATH)
        print(f"Loaded cached dataset from {DATA_PATH.relative_to(REPO_ROOT)}")
    else:
        try:
            dataset = fetch_profile_dataset(config)
            DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
            DATA_PATH.write_text(json.dumps(dataset, indent=2) + "\n", encoding="utf-8")
            print(
                f"Fetched live GitHub dataset ({dataset['stats']['public_repos']} public repos, "
                f"{dataset['stats']['total_contributions']} contributions, source={dataset['token_source']})"
            )
        except Exception as exc:
            if args.allow_fallback and DATA_PATH.exists():
                print(f"Warning: live GitHub fetch failed ({exc}); using cached {DATA_PATH.name}.", file=sys.stderr)
                dataset = _load_json(DATA_PATH)
            else:
                raise

    written_svgs = generate_all_visuals(REPO_ROOT, config, dataset)
    print(f"Generated and XML-validated {len(written_svgs)} SVG assets.")

    changed = update_readme(README_PATH, config, dataset)
    print(f"README.md {'updated' if changed else 'already up to date'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
