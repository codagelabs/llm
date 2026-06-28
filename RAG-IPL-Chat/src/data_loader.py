"""
Data loading utilities: discover match JSON files and assign logical IDs.
"""

import glob
import json
import os
from src.config import DATASET_DIRS
from src.utils import get_season_year, get_sort_key


def discover_dataset_dir(base_dir: str = ".") -> str:
    """Find the first available dataset directory."""
    for d in DATASET_DIRS:
        full = os.path.join(base_dir, d)
        if os.path.exists(full) and glob.glob(os.path.join(full, "*.json")):
            return full
    raise FileNotFoundError(
        f"No dataset directory found. Tried: {DATASET_DIRS}. "
        "Please place IPL JSON files in one of these directories."
    )


def load_all_matches(dataset_dir: str) -> list[tuple[str, dict]]:
    """
    Load and chronologically sort all match JSON files from *dataset_dir*.

    Returns a list of (filepath, data) tuples sorted by date → match_number → filename.
    """
    json_files = glob.glob(os.path.join(dataset_dir, "*.json"))
    all_matches: list[tuple[str, dict]] = []

    for filepath in json_files:
        with open(filepath, "r") as fh:
            try:
                data = json.load(fh)
                all_matches.append((filepath, data))
            except json.JSONDecodeError as exc:
                print(f"  [WARN] Skipping {filepath}: {exc}")

    all_matches.sort(key=get_sort_key)
    return all_matches


def build_match_id_map(all_matches: list[tuple[str, dict]]) -> dict[str, str]:
    """
    Assign logical match IDs like ``IPL_2008_001``.

    Returns a dict: filepath -> match_id, preserving chronological order
    within each season.
    """
    season_matches: dict[str, list[tuple[str, dict]]] = {}
    for filepath, data in all_matches:
        season = data.get("info", {}).get("season")
        year = get_season_year(season)
        season_matches.setdefault(year, []).append((filepath, data))

    filepath_to_id: dict[str, str] = {}
    for year, matches in season_matches.items():
        for idx, (filepath, _) in enumerate(matches):
            filepath_to_id[filepath] = f"IPL_{year}_{idx + 1:03d}"

    return filepath_to_id
