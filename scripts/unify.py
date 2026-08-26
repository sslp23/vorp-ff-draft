"""Turn data/fantasypros.csv into data/unified.csv.

Just one source (FantasyPros half-PPR overall cheat sheet), and its
`rank_ecr` already spans every position, so there's no cross-source matching
to do -- this just reshapes it into the column layout vorp_engine.py and
app.py expect (unified_rank, sources_count, etc.), the same way
vor_fpl_draft's unify_sleeper.py wraps its single Sleeper source. Structured
this way so a second source could be folded in later via percentile
averaging, the way vor_fpl_draft's unify.py combines multiple FPL sources.
"""
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
IN_PATH = DATA_DIR / "fantasypros.csv"
OUT_PATH = DATA_DIR / "unified.csv"


def run() -> pd.DataFrame:
    if not IN_PATH.exists():
        raise FileNotFoundError(f"Missing {IN_PATH}. Run scripts/fantasypros_scrape.py first.")

    df = pd.read_csv(IN_PATH).sort_values("rank").reset_index(drop=True)
    max_rank = df["rank"].max()

    unified = pd.DataFrame(
        {
            "unified_rank": df["rank"],
            "player": df["player"],
            "team": df["team"].astype(str).str.upper().str.strip(),
            "position": df["position"],
            "fantasypros_rank": df["rank"],
            "sources_count": 1,
            "unified_score": df["rank"] / max_rank,
            "pos_rank": df["pos_rank"],
            "tier": df["tier"],
            "bye_week": df["bye_week"],
            "owned_avg": df["owned_avg"],
            "rank_min": df["rank_min"],
            "rank_max": df["rank_max"],
            "rank_ave": df["rank_ave"],
            "rank_std": df["rank_std"],
        }
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    unified.to_csv(OUT_PATH, index=False)
    print(f"Unified: {len(unified)} players -> {OUT_PATH}")
    return unified


if __name__ == "__main__":
    run()
