# Robot Predictive Maintenance — Data Streaming and Visualization

**CSCN8010 — Foundations of Machine Learning Frameworks · Group 4**

| Member    | Track                                   |
| --------- | --------------------------------------- |
| Nnamdi    | Predictive analytics, integration, repo |
| Davis     | Streaming simulator                     |
| Carlos    | Dashboard and web app                   |
| Rangeetha | Neon database and data access layer     |

## Setup

| | |
|---|---|
| **Python** | 3.13 (pinned in `.python-version`; developed on 3.13.13) |
| **Package manager** | [uv](https://docs.astral.sh/uv/) — installs the right Python version for you |
| **Database** | Neon PostgreSQL (connection string via `.env`) |

### 1. Install uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Get the code and its dependencies

```bash
git clone https://github.com/Namypark/DATASTREAMVISUALIZATION-GROUP4.git
cd DATASTREAMVISUALIZATION-GROUP4
uv sync
```

`uv sync` reads `pyproject.toml` and `uv.lock`, creates a `.venv` with Python 3.13, and installs
every pinned dependency.

### 3. Add the database connection string

The notebook reads from a shared Neon PostgreSQL database. Create a file called `.env` in the
project root:

```text
DATABASE_URL=postgresql://<user>:<password>@<host>/<database>?sslmode=require
```

Ask a team member for the value. **`.env` is git-ignored and must never be committed.**

### 4. Run it

```bash
uv run jupyter lab
```

Then open `DataStreamVisualization_Workshop.ipynb` and run it top to bottom. Start Jupyter from the
project root — the notebook resolves its paths relative to the working directory.

**A full run takes about 2.5 minutes**, 2 minutes of which is Step 2 streaming 60 readings at its
2-second interval.

To check it runs cleanly without opening Jupyter:

```bash
uv run python -m nbconvert --to notebook --execute \
  DataStreamVisualization_Workshop.ipynb --output-dir /tmp/check
```

It writes the executed copy to `/tmp/check` and leaves your version untouched. Any cell that raises
stops the run and reports the error.

### Alternative: pip instead of uv

```bash
python3.13 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab
```

`requirements.txt` holds the same pinned versions. Python 3.13 is required either way — the code
uses syntax that older versions reject.

### Troubleshooting

| Problem | Cause |
|---|---|
| `ModuleNotFoundError` on the first cell | Jupyter wasn't started from the project root |
| `DATABASE_URL is missing` | No `.env` file, or it's not in the project root |
| Step 2 takes about 2 minutes | Expected — 60 readings at the specified 2-second interval |

## The problem

A materials-handling robot failed and took **480 minutes of production** with it. The cause was wear
in a torque tube. Nobody saw it coming, because there was no way to watch the robot's health while
it ran — maintenance could only react after a breakdown.

This project builds the monitoring tool that would have seen it: it reads the electrical current
each joint draws, stores every reading in a cloud database, shows them on a live dashboard, and
flags readings that suggest something is going wrong.

## The data

`data/RMBR4-2_export_test.csv` — one Kawasaki materials-handling robot, recorded 17–18 October 2022.

- **39,672 readings** taken roughly every 2 seconds across 22.5 hours
- Each reading is the current in amps for eight joints
- The export format has fourteen axis columns, but this robot has eight; columns 9–14 are empty in
  every row
- Supplied as course material for CSCN8010. Not a public dataset, so no external link or licence
  applies

## What we found

- **The robot is idle 64.2% of the time.** Any average that includes idle readings measures the
  production schedule rather than the machine.
- **Two joints do most of the work.** Axes 2 and 3 draw 62% of all current.
- **There is a three-hour production stoppage** on 18 October (03:00–06:00 UTC), during which the
  controller kept reporting normally. A stopped production line and a failed monitoring system look
  identical on a current chart and mean entirely different things.
- **No degradation is present.** Total active current moves from 28.5A to 28.3A across the window —
  0.6%, which is noise. 22.5 hours is far too short to reveal wear that develops over months. What
  this delivers is the instrument that would catch it under continuous collection.
- **Ranking anomalies by flag count points at the wrong joint.** A z-score measures deviation
  relative to each joint's own baseline, so axis 8 — which normally draws 0.3A — produces the most
  flags (605) from 3–4A excursions, while axis 2's genuinely heavy 51A spikes produce 341. Ranked
  by current above baseline instead, axis 2 carries 9,605A of excess against axis 8's 1,575A.
  Maintenance attention belongs on axes 2 and 3.
- **The detector needed correcting before its numbers were trustworthy.** The rolling window
  originally included the reading being tested, which capped every score at `(n-1)/√n` = 5.2947, and
  a baseline that spanned a three-hour stoppage was not "recent behaviour" in any useful sense.
  Both versions produced plausible-looking output — see the Step 4 talking point.

Full reasoning is in the notebook's talking points and findings cells.

## Notebooks

| File                                     | Contents                                           |
| ---------------------------------------- | -------------------------------------------------- |
| `DataStreamVisualization_Workshop.ipynb` | Our submission — all four steps, code and write-up |
| `instructor_material.ipynb`              | The instructor's brief, kept for reference         |

## Project structure

```text
.
├── data/                              # the robot readings CSV
├── src/
│   ├── data_collection/
│   │   ├── data_collection_agent.py   # get_connection, insert_reading, fetch_all, fetch_since
│   │   └── streaming_simulator.py     # replays the CSV as a live controller feed
│   ├── database-service/
│   │   └── migrate_schema.py          # one-off schema rebuild: create / load / verify / swap
│   └── web_ui/                        # standalone Dash dashboard
└── DataStreamVisualization_Workshop.ipynb
```

## The standalone dashboard

Besides the charts inside the notebook, `src/web_ui/` holds a Dash web app built on the same
database layer. It runs independently of the notebook:

```bash
uv run python src/web_ui/web_ui_interface.py
```

Then open <http://127.0.0.1:8050/>. Stop it with `Ctrl+C`.

It replays stored readings from the first one in the file, the same starting point as the notebook's
Step 2, one reading every 2 seconds, in the same colours — so a joint looks the same in both views.

- The chart trims to the last 90 seconds, so it takes **90 seconds to fill**, then scrolls.
- It keeps going for about **22 hours** before running out of readings, at which point the chart
  simply stops updating.
- **Live** restarts the replay from the first reading. **Bulk Load** drops the
  whole dataset onto the chart at once and stops the polling.

Don't leave it running while the notebook's Step 2 is streaming — both write to the same Neon
database, and the free tier limits concurrent connections.

## Rebuilding the database from scratch

Only needed for a fresh Neon project. `migrate_schema.py` runs in four steps so the result can be
checked before anything is replaced:

```bash
uv run python src/database-service/migrate_schema.py create   # build robot_readings_new
uv run python src/database-service/migrate_schema.py load     # insert the 39,672 CSV rows
uv run python src/database-service/migrate_schema.py verify   # compare counts and time span
uv run python src/database-service/migrate_schema.py swap     # rename into place
```

Run `verify` before `swap` — it prints `MATCH` or `MISMATCH`. The swap keeps the previous table as
`robot_readings_old` rather than dropping it.

## Notes on running Step 2

Step 2 streams at the specified 2-second interval, so that cell takes about a minute. It writes its
demo readings to the shared table and deletes them again afterwards, so the notebook can be re-run
without the data drifting.
