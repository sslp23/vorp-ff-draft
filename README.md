# vor_ff_draft

NFL fantasy football counterpart to
[vor_fpl_draft](../vor_fpl_draft): pulls a public draft ranking, and uses it
to power a live VORP (Value Over Replacement Player) draft-board dashboard.

## Source

| Source | How it's fetched | Pool size |
|---|---|---|
| [FantasyPros half-PPR overall cheat sheet](https://www.fantasypros.com/nfl/rankings/half-point-ppr-cheatsheets.php) | Scraped directly: the page embeds its full player list as a `var ecrData = {...}` JSON blob in a `<script>` tag | ~930, spanning QB/RB/WR/TE/K/DST |

Unlike vor_fpl_draft, this is a single source whose `rank_ecr` is already one
overall rank spanning every position, so there's no cross-source rank
blending to do -- `scripts/unify.py` just reshapes it into the same column
layout (`unified_rank`, `sources_count`, etc.) `vorp_engine.py` and `app.py`
expect, mirroring how vor_fpl_draft's `unify_sleeper.py` wraps its one
Sleeper-format source.

## Project layout

```
data/
  fantasypros.csv               raw scraped ranking, normalized columns
  unified.csv                   reshaped ranking (vorp_engine/app input)
scripts/
  fantasypros_scrape.py         scrapes the FantasyPros cheat sheet page
  unify.py                      reshapes fantasypros.csv into unified.csv
pipeline.py                     runs the scraper, then unify.py
vorp_engine.py                  value/VORP math (position-agnostic of Streamlit)
app.py                          Streamlit live draft board
```

## Running it

Requires `pandas`, `requests`, `streamlit` (see `requirements.txt`).

```
python pipeline.py
streamlit run app.py
```

`pipeline.py` regenerates `data/fantasypros.csv` and `data/unified.csv`.
Re-run it whenever you want fresher rankings (FantasyPros updates its
consensus ranks continuously through the offseason/season).

## VORP model

Same shape as vor_fpl_draft's: `unified_rank` is turned into a 0-100 `value`
via exponential decay (top picks are worth much more than mid-pack ones, not
linearly), and replacement level per position is the value of the last
player who'd actually get drafted there league-wide, given `num_teams` and
roster composition.

The NFL wrinkle is FLEX: a standard roster also has FLEX spot(s) that pull
extra RB/WR/TE off the board before a position's replacement level is
reached. `vorp_engine.replacement_levels` accounts for this by distributing
`flex_spots` across RB/WR/TE in proportion to each position's own roster
spot count, then adding that to the position's drafted count before reading
off the replacement-level value. Superflex/2QB leagues (where QB is also
FLEX-eligible) aren't modelled -- `FLEX_ELIGIBLE` in `vorp_engine.py` would
need `QB` added for that.
