"""
Stub DB access layer for the Live Status dashboard.

Matches the interface agreed in TEAM_PLAN.md #4.1 (owned by Rangeetha, not yet built):
get_connection(), insert_reading(record), fetch_all() -> pd.DataFrame.

fetch_since(last_ts) is a PROPOSED ADDITION to that interface, not yet agreed with the
team. The dashboard's live-polling loop needs a way to ask for "rows newer than X"
without re-fetching the whole table every 1-2 seconds; fetch_all() alone can't do that
efficiently. Once Rangeetha's real module exists, the intended real implementation is:

    SELECT * FROM robot_readings WHERE reading_time > %s ORDER BY reading_time

Everything below is a stub backed by the local CSV so the dashboard can be built and
demoed before the real Neon connection lands. Swap the bodies of these four functions
for real psycopg2/SQLAlchemy calls (using DATABASE_URL from .env) later; nothing else
in src/web-ui/ needs to change.
"""

from pathlib import Path

import pandas as pd

_CSV_PATH = Path(__file__).resolve().parents[2] / "data" / "RMBR4-2_export_test.csv"
_AXIS_COLUMNS = [f"axis_{i}" for i in range(1, 9)]

_full_df: pd.DataFrame | None = None
_cursor = 0


def _load_full_df() -> pd.DataFrame:
    global _full_df
    if _full_df is None:
        raw = pd.read_csv(_CSV_PATH)
        renamed = raw.rename(
            columns={
                "Trait": "trait",
                "Time": "reading_time",
                **{f"Axis #{i}": f"axis_{i}" for i in range(1, 9)},
            }
        )
        _full_df = renamed[["trait", *_AXIS_COLUMNS, "reading_time"]].copy()
        _full_df["reading_time"] = pd.to_datetime(_full_df["reading_time"])
    return _full_df


def get_connection():
    """Stub: no real connection yet. Returns None."""
    return None


def insert_reading(record: dict) -> None:
    """Stub no-op. The dashboard never calls this itself; kept for interface parity
    with what Davis's StreamingSimulator will call once wired to the real DB."""
    return None


def fetch_all() -> pd.DataFrame:
    """Returns the entire simulated table in one call, as if querying a DB that
    already holds all the data. Used by the debug 'Bulk Load' button."""
    return _load_full_df().copy()


def fetch_since(last_ts) -> pd.DataFrame:
    """Stub polling helper (see module docstring). Advances an internal row cursor
    over the CSV each call and returns the next slice, simulating rows that have
    "just landed" since last_ts. last_ts is accepted for interface parity with the
    eventual real query but is not used by this stub (the cursor tracks position
    instead of filtering by timestamp)."""
    global _cursor
    df = _load_full_df()
    batch_size = 5
    next_cursor = min(_cursor + batch_size, len(df))
    batch = df.iloc[_cursor:next_cursor].copy()
    _cursor = next_cursor
    return batch


def reset_cursor() -> None:
    """Test/debug helper to restart fetch_since() from the beginning of the CSV."""
    global _cursor
    _cursor = 0
