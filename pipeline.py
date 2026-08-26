"""Scrape the FantasyPros half-PPR ranking and build data/unified.csv.

Usage: python pipeline.py
"""
import runpy
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


def main() -> None:
    print("\n=== fantasypros_scrape.py ===")
    try:
        runpy.run_path(str(SCRIPTS_DIR / "fantasypros_scrape.py"), run_name="__main__")
    except Exception as exc:
        print(f"FAILED: fantasypros_scrape.py: {exc}", file=sys.stderr)
        raise

    print("\n=== unify.py ===")
    import unify

    unify.run()


if __name__ == "__main__":
    main()
