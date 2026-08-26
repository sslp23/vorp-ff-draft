"""Scrape FantasyPros' half-PPR overall draft rankings into data/fantasypros.csv.

The rankings page (a client-rendered cheat sheet) embeds its full player list
as a `var ecrData = {...};` JSON blob inside a <script> tag on the raw HTML,
so no headless browser is needed -- just pull the page and lift that object
out. `rank_ecr` is already a single overall rank spanning every position
(QB/RB/WR/TE/K/DST), so unlike vor_fpl_draft this is one source with a
ready-made unified rank -- no cross-source percentile blending required.
"""
import json
import re
from pathlib import Path

import pandas as pd
import requests

URL = "https://www.fantasypros.com/nfl/rankings/half-point-ppr-cheatsheets.php"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "fantasypros.csv"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def _extract_ecr_data(html: str) -> dict:
    marker = "var ecrData = "
    start = html.find(marker)
    if start == -1:
        raise RuntimeError("Could not find ecrData on FantasyPros rankings page")
    start += len(marker)

    # Brace-match from the opening `{` rather than regexing up to the first
    # `};`, since string fields (player names, urls) could in principle
    # contain either character.
    depth = 0
    in_string = False
    escape = False
    end = None
    for i, ch in enumerate(html[start:], start=start):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        raise RuntimeError("Could not find end of ecrData JSON object")

    return json.loads(html[start:end])


def scrape() -> pd.DataFrame:
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = _extract_ecr_data(resp.text)

    players = data.get("players")
    if not players:
        raise RuntimeError("ecrData had no players")

    rows = []
    for p in players:
        rows.append(
            {
                "rank": p["rank_ecr"],
                "player": p["player_name"],
                "team": p["player_team_id"],
                "position": p["player_position_id"],
                "pos_rank": p.get("pos_rank"),
                "tier": p.get("tier"),
                "bye_week": p.get("player_bye_week"),
                "owned_avg": p.get("player_owned_avg"),
                "rank_min": p.get("rank_min"),
                "rank_max": p.get("rank_max"),
                "rank_ave": p.get("rank_ave"),
                "rank_std": p.get("rank_std"),
            }
        )

    df = pd.DataFrame(rows).sort_values("rank").reset_index(drop=True)
    return df


def main() -> None:
    df = scrape()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(df)} players to {OUT_PATH}")


if __name__ == "__main__":
    main()
