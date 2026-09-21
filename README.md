# Robot Predictive Maintenance — Data Streaming and Visualization

**CSCN8010 — Foundations of Machine Learning Frameworks · Group 4**

| Member | Track |
|---|---|
| Namy | Predictive analytics, integration, repo |
| Davis | Streaming simulator |
| Carlos | Dashboard and web app |
| Rangeetha | Neon database and data access layer |

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

| File | Contents |
|---|---|
| `DataStreamVisualization_Workshop.ipynb` | Our submission — all four steps, code and write-up |
| `instructor_material.ipynb` | The instructor's brief, kept for reference |

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

## Running it

Requires Python 3.13 and a `DATABASE_URL` for the Neon database in a local `.env` file (never
committed).

```bash
uv sync
uv run jupyter lab      # then run DataStreamVisualization_Workshop.ipynb top to bottom
```

The standalone dashboard runs separately:

```bash
uv run python src/web_ui/web_ui_interface.py
```

Step 2 streams at the specified 2-second interval, so that cell takes about a minute. It writes its
demo readings to the shared table and deletes them again afterwards, so the notebook can be re-run
without the data drifting.
