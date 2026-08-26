"""Valuation and VORP calculation on top of data/unified.csv.

Value is derived purely from the unified ranking -- unified_rank, which for
this project is just FantasyPros' overall ECR (Expert Consensus Rank) --
rather than points, since a single overall rank spanning every position is
exactly the kind of consistent, cross-position value basis vor_fpl_draft's
vorp_engine.py argues for.

Kept separate from app.py so the math can be tested/reused without Streamlit.
"""
import numpy as np
import pandas as pd

POSITIONS = ["QB", "RB", "WR", "TE", "K", "DST"]

# Positions that can also fill a league's FLEX spot(s). Standard redraft
# leagues flex RB/WR/TE; superflex/2QB leagues would add QB, but that's a
# league-settings variant we're not modelling here.
FLEX_ELIGIBLE = ["RB", "WR", "TE"]

# Rank e-folding scale for rank_value's decay curve: bigger = flatter (ranks
# matter less relative to each other), smaller = steeper (top picks worth
# much more than everyone else). NFL cheat sheets run deeper (900+ players)
# than FPL's, so the curve is scaled up accordingly.
DEFAULT_DECAY = 90.0


def rank_value(df: pd.DataFrame, decay: float = DEFAULT_DECAY) -> pd.Series:
    """Turn unified_rank into a 0-100 value via exponential decay rather than
    a linear percentile.

    A linear rank-to-value mapping badly understates how much better elite
    players are than merely-very-good ones -- e.g. the #1 overall player
    and the #12 overall player end up just a few points apart on a 0-100
    scale, a gap easily swamped by differences in positional replacement
    level. Real fantasy value isn't linear in rank: the gap between #1 and
    #12 is normally much bigger than the gap between #50 and #61.
    Exponential decay keeps the top of the board sharply differentiated
    while flattening out near replacement level, which matches that shape.
    """
    if "unified_rank" not in df:
        raise KeyError("unified_rank column missing from unified.csv")
    return (100 * np.exp(-(df["unified_rank"] - 1) / decay)).rename("value")


def replacement_levels(
    df: pd.DataFrame, num_teams: int, roster_spots: dict, flex_spots: int = 0
) -> dict:
    """Value of the Nth-best player at each position (N = num_teams *
    roster_spots at that position, bumped for a share of the league's FLEX
    spots) -- the baseline for VORP: the value of the last player who'll
    actually get drafted onto a squad at that position, across the whole
    league.

    roster_spots is full-roster composition (starters + bench), not just
    starting-lineup counts -- draft leagues roster the whole squad, so that's
    what should define replacement level.

    flex_spots (per team) don't belong to one position, but they do pull
    extra RB/WR/TE off the board before replacement level is reached. Those
    extra slots are distributed across FLEX_ELIGIBLE positions in proportion
    to each position's own roster_spots share, then added to that position's
    drafted count.
    """
    flex_pool_spots = sum(roster_spots.get(pos, 0) for pos in FLEX_ELIGIBLE)
    levels = {}
    for pos in POSITIONS:
        pool = df.loc[df["position"] == pos, "value"].sort_values(ascending=False).reset_index(drop=True)
        n = num_teams * roster_spots.get(pos, 0)
        if pos in FLEX_ELIGIBLE and flex_pool_spots > 0:
            share = roster_spots.get(pos, 0) / flex_pool_spots
            n += round(num_teams * flex_spots * share)
        if len(pool) == 0:
            levels[pos] = 0.0
        else:
            idx = min(max(n - 1, 0), len(pool) - 1)
            levels[pos] = float(pool.iloc[idx])
    return levels


def compute_vorp(
    df: pd.DataFrame,
    num_teams: int,
    roster_spots: dict,
    decay: float = DEFAULT_DECAY,
    flex_spots: int = 0,
) -> pd.DataFrame:
    df = df.copy()
    df["value"] = rank_value(df, decay)
    levels = replacement_levels(df, num_teams, roster_spots, flex_spots)
    df["replacement_value"] = df["position"].map(levels)
    df["vorp"] = df["value"] - df["replacement_value"]
    return df
