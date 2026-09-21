# Robot Predictive Maintenance — Data Streaming and Visualization

**CSCN8010 — Foundations of Machine Learning Frameworks · Group 4**

| Member    | Track                                   |
| --------- | --------------------------------------- |
| Nnamdi    | Predictive analytics, integration, repo |
| Davis     | Streaming simulator                     |
| Carlos    | Dashboard and web app                   |
| Rangeetha | Neon database and data access layer     |

## Setup

Requires **Python 3.13**. The project is managed with [uv](https://docs.astral.sh/uv/), which
installs the right Python version for you.

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
| Step 2 takes about a minute | Expected — it streams at the specified 2-second interval |

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
- **Ranking anomalies by z-score points at the wrong joint.** The score saturates at `(n-1)/√n`
  (5.2947 for our 30-reading window), and it measures deviation relative to each joint's own
  baseline. Ranked by current above baseline instead, axis 2 carries 7,219A of excess against axis
  8's 1,534A.

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

Then open <http://127.0.0.1:8050/>. It replays stored readings from the same starting point as the
notebook's Step 2, one reading every 2 seconds, in the same colours — so a joint looks the same in
both views.

## Notes on running Step 2

Step 2 streams at the specified 2-second interval, so that cell takes about a minute. It writes its
demo readings to the shared table and deletes them again afterwards, so the notebook can be re-run
without the data drifting.
