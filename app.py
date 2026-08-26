"""Live VORP draft board for the FantasyPros half-PPR NFL ranking.

Run with: streamlit run app.py
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from vorp_engine import DEFAULT_DECAY, POSITIONS, compute_vorp

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_PATH = DATA_DIR / "unified.csv"
DRAFT_STATE_PATH = DATA_DIR / "draft_state.json"

st.set_page_config(page_title="NFL Fantasy Draft VORP Board", layout="wide")


@st.cache_data
def load_unified(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def load_drafted() -> list:
    if DRAFT_STATE_PATH.exists():
        return json.loads(DRAFT_STATE_PATH.read_text())
    return []


def save_drafted(drafted: list) -> None:
    DRAFT_STATE_PATH.write_text(json.dumps(drafted, indent=2))


if "drafted" not in st.session_state:
    st.session_state.drafted = load_drafted()

st.title("NFL Fantasy Draft VORP Board — FantasyPros Half-PPR")

if not DATA_PATH.exists():
    st.error(f"{DATA_PATH.name} not found. Run pipeline.py first.")
    st.stop()

with st.sidebar:
    st.header("League settings")
    num_teams = st.number_input("Number of teams", min_value=2, max_value=20, value=12)
    st.caption("Roster spots per position (full roster incl. bench, defines replacement level)")
    roster_spots = {
        "QB": st.number_input("QB spots", min_value=0, max_value=6, value=2, help="1 starter + 1 backup"),
        "RB": st.number_input("RB spots", min_value=0, max_value=10, value=4, help="2 starters + bench"),
        "WR": st.number_input("WR spots", min_value=0, max_value=10, value=5, help="2 starters + bench"),
        "TE": st.number_input("TE spots", min_value=0, max_value=6, value=1, help="1 starter, no bench TE"),
        "K": st.number_input("K spots", min_value=0, max_value=3, value=1),
        "DST": st.number_input("DST spots", min_value=0, max_value=3, value=1),
    }
    flex_spots = st.number_input(
        "FLEX spots (per team, RB/WR/TE)",
        min_value=0,
        max_value=5,
        value=1,
        help="Extra RB/WR/TE slots that aren't a dedicated position. Pulls the "
        "replacement level for those positions deeper, split proportionally "
        "to their roster spot counts.",
    )

    decay = st.slider(
        "Value curve steepness",
        min_value=20.0,
        max_value=300.0,
        value=DEFAULT_DECAY,
        help="Lower = top-ranked players are worth much more than everyone else. "
        "Higher = value spreads out more evenly across rank.",
    )

    st.header("Draft control")
    if st.session_state.drafted:
        st.caption(f"Last pick (#{len(st.session_state.drafted)}): {st.session_state.drafted[-1]}")
    if st.session_state.drafted and st.button("Undo last pick"):
        st.session_state.drafted.pop()
        save_drafted(st.session_state.drafted)
        st.rerun()

    if st.button("Reset draft"):
        st.session_state.drafted = []
        save_drafted(st.session_state.drafted)
        st.rerun()

raw = load_unified(str(DATA_PATH))
board = compute_vorp(raw, num_teams, roster_spots, decay, flex_spots)

available = board[~board["player"].isin(st.session_state.drafted)].sort_values("vorp", ascending=False)
drafted_df = board[board["player"].isin(st.session_state.drafted)]

if st.session_state.drafted:
    last_row = board[board["player"] == st.session_state.drafted[-1]]
    if not last_row.empty:
        lr = last_row.iloc[0]
        st.info(
            f"Last pick (#{len(st.session_state.drafted)}): **{lr['player']}** "
            f"({lr['team']}, {lr['position']}) — VORP {lr['vorp']:.1f}"
        )

if available.empty:
    st.subheader("No players left to draft.")
else:
    top = available.iloc[0]
    st.subheader(
        f"Suggested next pick: **{top['player']}** ({top['team']}, {top['position']}) "
        f"— VORP {top['vorp']:.1f}"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        pick = st.selectbox(
            "Player Name",
            options=available["player"].tolist(),
            index=0,
            placeholder="Search a player to draft...",
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("Draft player", type="primary"):
            st.session_state.drafted.append(pick)
            save_drafted(st.session_state.drafted)
            st.rerun()

st.divider()

fcol1, fcol2 = st.columns([2, 2])
with fcol1:
    search = st.text_input("Filter board by name")
with fcol2:
    pos_filter = st.multiselect("Position", POSITIONS, default=POSITIONS)

view = available[available["position"].isin(pos_filter)]
if search:
    view = view[view["player"].str.contains(search, case=False, na=False)]

st.subheader(f"Available players ({len(view)})")
st.dataframe(
    view[["unified_rank", "player", "team", "position", "pos_rank", "tier", "bye_week", "value", "replacement_value", "vorp"]]
    .rename(
        columns={
            "unified_rank": "Rank",
            "player": "Player",
            "team": "Team",
            "position": "Pos",
            "pos_rank": "Pos Rank",
            "tier": "Tier",
            "bye_week": "Bye",
            "value": "Value",
            "replacement_value": "Replacement",
            "vorp": "VORP",
        }
    )
    .round({"Value": 1, "Replacement": 1, "VORP": 1}),
    use_container_width=True,
    hide_index=True,
)

with st.expander(f"Drafted players ({len(drafted_df)})"):
    st.dataframe(
        drafted_df[["player", "team", "position", "vorp"]].rename(
            columns={"player": "Player", "team": "Team", "position": "Pos", "vorp": "VORP (at draft)"}
        ),
        use_container_width=True,
        hide_index=True,
    )
