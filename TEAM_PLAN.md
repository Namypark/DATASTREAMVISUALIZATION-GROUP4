# Data Stream Visualization Workshop — Team Implementation Plan

**Use case:** Manufacturing Robot Predictive Maintenance
**Team:** Nnamdi, Davis, Carlos, Rangeetha
**Deadline:** Monday, 2026-09-21
**Repo:** [https://github.com/Namypark/DATASTREAMVISUALIZATION-GROUP4](https://github.com/Namypark/DATASTREAMVISUALIZATION-GROUP4)
**Deliverable:** One completed Jupyter Notebook pushed to the repo above, plus an email to the instructor with the `.git` link.

---

## 1. Problem Context

- **Issue:** Torque tube failure caused 480 minutes of downtime.
- **Root cause:** Equipment age.
- **Roadblock:** Limited options for monitoring equipment health.
- **Gap:** No tool exists to move from reactive breakdown response to proactive maintenance.
- **Goal:** Build a Predictive Maintenance Dashboard that streams robot controller data (per-axis electrical current), persists it, visualizes it live, and flags anomalies as maintenance alerts.

Data source: `data/RMBR4-2_export_test.csv` — 39,672 data rows, one reading roughly every 2 seconds, columns `Trait, Axis #1 … Axis #14, Time`.

---

## 1b. Verified Data Profile — read this before you build

These findings come from profiling the actual CSV and **correct three assumptions** we made in the first draft of this plan. Build against these, not against the column headers.

| First assumption                  | Verified reality                                                                                             |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Traits include current and torque | **Only** `current` — all 39,672 rows. No torque data exists in this file.                                    |
| 14 axes of data                   | **Only axes 1–8 carry data.** Axes 9–14 are 100% null — an 8-axis robot logged in a 14-column export format. |
| Continuous sampling               | Two real collection gaps: **402s** (Oct 17 12:33) and **333s** (Oct 17 13:07).                               |

**Shape of the dataset:**

- Window: 2022-10-17 12:18 → 2022-10-18 10:44 UTC (**22.5 hours**), median sampling interval 1.89s.
- **64.2% of rows are fully idle** — all 8 axes read exactly 0.0. Only 35.8% represent active motion.
- **Axis #2 and #3 carry the load** — mean 10.1A and 7.6A when active, versus 0.3–2.7A for the remaining axes. Peak observed: 51.7A on Axis #2.

**Key event — a ~3-hour production stoppage.** Idle percentage per hour:

| Hour (UTC)      | Idle % |
| --------------- | ------ |
| Oct 17 16:00    | 99.8%  |
| Oct 18 03:00    | 95.4%  |
| Oct 18 04:00    | 100.0% |
| Oct 18 05:00    | 99.6%  |
| All other hours | 43–82% |

The controller continued reporting every ~2 seconds throughout (~1,780 rows/hour), so this is **not a data outage — the robot was powered and polled but not moving.** Treat it as an availability event, not a health event.

**Baseline trend:** mean active current summed across axes is ~28.4A in the first hour and ~28.3A in the last. **There is no degradation trend in this window** — see Section 4.4 for why that matters.

---

## 2. Roles & Track Split

Work is split by track, built against stubs in parallel, then integrated — nobody blocks on anybody else at the start.

| Person        | Track                    | Deliverable                                                                                                                     |
| ------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| **Rangeetha** | Database                 | Neon.tech Postgres project; `robot_readings` schema; `get_connection()`, `insert_reading()`, `fetch_all()` functions            |
| **Davis**     | Streaming                | `StreamingSimulator` OOP class (Steps 1–2 of the workshop spec): `nextDataPoint()`, configurable playback speed, bulk-load path |
| **Carlos**    | Dashboard                | Matplotlib inline live-refresh chart (Step 2) + final summary chart (Additional Challenge)                                      |
| **Nnamdi**    | Predictive + integration | Rolling z-score anomaly module (Steps 3–4), markdown talking points, repo ownership, merging PRs                                |

Davis, Carlos, and Namy each start by building against a **stub interface** (a no-op DB call, or fake/random data) so nothing is blocked on Rangeetha's Neon setup landing first.

---

## 3. Timeline

| When                                               | Activity                                                                                                                                                                                                                                                                 |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Day 1 (kickoff)**                                | Confirm roles. Rangeetha starts the Neon.tech project and shares schema + connection details with the team as soon as possible. Davis, Carlos, and Namy start building against stubs in parallel, each on their own branch.                                              |
| **Day 2 (integration)**                            | Swap stubs for real pieces: Davis's `StreamingSimulator` calls Rangeetha's `insert_reading()`; Carlos's dashboard consumes Davis's live buffer; Namy wires the predictive module to `fetch_all()`. Open PRs into `main` as each piece is ready; Namy reviews and merges. |
| **Day 3 (full run-through + polish)**              | Run the notebook top to bottom, run the full CSV backfill, produce the summary chart (Additional Challenge), finish Step 3/4 markdown (anomalies + Maintenance Notification alerts), fill in "team talking point" cells. Fix anything integration broke.                 |
| **Day 4 (submission day, before Monday deadline)** | Final fresh run of the whole notebook top-to-bottom to confirm it executes cleanly, final merge to `main`, email the instructor the `.git` link.                                                                                                                         |

No hard clock per phase — each day is a checkpoint so no one is stuck waiting until the last minute.

---

## 4. Component Specs

### 4.1 Database schema — Rangeetha

- Single table `robot_readings`:
  - `id` — serial primary key
  - `trait` — text (always `'current'` in this dataset; kept as a column so other traits can be added later)
  - `axis_1` … `axis_8` — numeric, nullable
  - `reading_time` — timestamptz (from the CSV's `Time` column)
  - `inserted_at` — timestamptz, default now
- Backend: Neon Postgres via `psycopg2` or SQLAlchemy.
- Exposes three functions everyone else calls:
  - `get_connection()`
  - `insert_reading(record: dict)`
  - `fetch_all() -> pd.DataFrame`
- Connection string lives in a local `.env` (never committed). Everyone sets their own `DATABASE_URL` once Rangeetha shares it.

> **Corrected from the first draft:** the schema is **8 axis columns, not 14**. Axes 9–14 in the CSV are null in every one of the 39,672 rows (see Section 1b). Do not create six permanently-empty columns.

### 4.2 StreamingSimulator — Davis

- `StreamingSimulator(csv_path, interval=2.0)` — the default **is** the instruction ("a single reading every 2 seconds"). Pass a smaller `interval` only to speed up testing.
- `nextDataPoint()` — returns the next row as a dict/Series, advances an internal pointer, signals end-of-file at exhaustion.
- `run(n_steps, on_tick)` — drives `n_steps` calls spaced `interval` seconds apart, invoking a callback each tick (the callback does the DB insert + chart update).
- `bulk_load(csv_path)` — separate no-delay path for the full-dataset backfill used by the summary chart and predictive module.

> **Why a slice, not the whole file:** 39,672 readings × 2s = **22 hours**, which is the real span of the data. The notebook streams ~30 readings live (about a minute) to demonstrate the mechanism at the specified interval; the full dataset reaches the database through the separate bulk load. State this explicitly in the Step 2 markdown.

### 4.3 Dashboard — Carlos

- Matplotlib figure using `IPython.display.clear_output` inside the loop for the live-refresh chart during the demo slice, driven by `StreamingSimulator.run`'s callback.
- Separate static chart, built after the full backfill, summarizing per-axis energy consumption across the whole dataset (the Additional Challenge).

### 4.4 Predictive module — Namy

Two layers: point anomalies (spikes) and trend (wear). Only the second is genuinely _predictive_.

**Layer 1 — point anomalies, computed over active samples only.**

A rolling z-score on the raw column **does not work on this dataset** and must not be used. 64.2% of rows are fully idle, so the rolling standard deviation over a window of idle readings is `0`; the first active reading then produces a near-infinite z-score. The result is that every motion start is flagged as an anomaly.

Measured on Axis #2:

| Method                               | Readings flagged                                              |
| ------------------------------------ | ------------------------------------------------------------- |
| Rolling z on raw column              | **780** — dominated by idle→active transitions (false alarms) |
| Rolling z on **active samples only** | **242** of 13,850 active rows (1.7%)                          |

The corrected implementation filters first:

```python
def detect_anomalies(df, axis_col, window=30, threshold=3.0):
    """Flag readings extreme relative to recent ACTIVE operation."""
    active = df[df[axis_col] > 0].copy()
    rolling_mean = active[axis_col].rolling(window).mean()
    rolling_std = active[axis_col].rolling(window).std()
    active['z_score'] = (active[axis_col] - rolling_mean) / rolling_std
    active['is_anomaly'] = active['z_score'].abs() > threshold
    return active[active['is_anomaly']]
```

Verification target: Axis #2 should yield **242 anomalies**, the largest around **43–47A** at Oct 17 22:56, Oct 17 15:07, and Oct 18 02:42. A result of 780 means the active filter is missing.

Anomalies are collected into an alert log DataFrame: `trait, axis, time, value, z_score`.

**Layer 2 — degradation trend.**

Wear failures (the torque tube in the problem statement) show up as the same motion drawing progressively more current as friction rises. Track hourly mean current across active samples per axis. In this dataset the trend is **flat** (~28.4A first hour, ~28.3A last hour), which is the honest finding to report: 22.5 hours is far too short a window to reveal wear that develops over weeks. The notebook is the instrument that would detect it under continuous collection.

**Step 4 alert classification.** The markdown discussion should separate alert classes rather than treating every anomaly as a fault:

| Class        | Evidence in this dataset                                                              | Robot unhealthy?                         |
| ------------ | ------------------------------------------------------------------------------------- | ---------------------------------------- |
| Availability | ~3-hour stoppage Oct 18 03:00–06:00; 95–100% idle with the controller still reporting | No — production stopped, robot is fine   |
| Load spike   | 242 readings above 3σ on Axis #2 (43–47A vs 10.1A active mean)                        | Not yet — transient, no supporting trend |
| Wear         | Not present; baseline is flat                                                         | No signal in this window                 |

The defensible conclusion is that **no maintenance notification is warranted from this data**, paired with an explicit definition of the trigger that would warrant one (e.g. hourly active-mean for Axis #2 rising more than 15% above its 7-day baseline). Specifying when _not_ to alert is what keeps the tool credible.

---

## 5. Data Flow

```text
CSV file
  │
  ├─▶ StreamingSimulator.run(n_steps, on_tick)   [~30 readings live, interval=2.0s]
  │        on_tick(record):
  │          ├─▶ insert_reading(record)          → Neon `robot_readings`
  │          └─▶ dashboard.update(record)         → live matplotlib refresh
  │
  └─▶ StreamingSimulator.bulk_load(csv_path)     [full 39,672 rows, no delay]
           └─▶ insert_reading(record) per row     → Neon `robot_readings`
                     │
                     ▼
           fetch_all() → pd.DataFrame
                     │
        ┌────────────┴────────────┐
        ▼                          ▼
  summary chart                anomaly detector
  (Additional Challenge)       → alert log → Step 4 markdown
```

Note: the demo slice and the full backfill both go through `insert_reading()`, so a handful of demo rows end up duplicated in the DB alongside the full dataset. This is acceptable for the workshop; if it matters, Rangeetha can dedupe on `(trait, reading_time)` at insert time as a nice-to-have.

---

## 6. Git Workflow

The repo is already live and public at **[https://github.com/Namypark/DATASTREAMVISUALIZATION-GROUP4](https://github.com/Namypark/DATASTREAMVISUALIZATION-GROUP4)**. Namy owns it and will send collaborator invites — accept the email invite when it arrives, then clone:

```bash
git clone https://github.com/Namypark/DATASTREAMVISUALIZATION-GROUP4.git
cd DATASTREAMVISUALIZATION-GROUP4
```

- Branch per person: `davis-streaming-sim`, `carlos-dashboard`, `rangeetha-db-setup`, `namy-predictive-analytics`.
- Each person opens a PR into `main` as their section is ready; Namy reviews and merges.
- To minimize conflicts on the shared notebook, each person works in a distinct range of cells corresponding to their workshop step. Notebooks are JSON — two people editing the same cells produces a conflict that can stop the file from opening at all.
- `.env` / credentials are excluded via `.gitignore` and never committed. Rangeetha shares the Neon connection string over a secure channel (not in the repo, not in a commit); each teammate sets it as their own local environment variable.
- At least one commit must contain a meaningful "talking point" per the submission checklist.

**Everyday commands:**

```bash
git checkout -b your-branch-name     # create and switch to your branch
git add <the files you changed>
git commit -m "describe what you did"
git push -u origin your-branch-name  # -u only needed on the first push

git checkout main && git pull        # get teammates' merged work
git checkout your-branch-name
git merge main                       # bring it into your branch
```

---

## 7. Talking Points & Submission Checklist

- **Team talking points:** add a markdown cell labeled "Team Talking Point" under each of the instructor's "Instructor Talking Point" cells, in your own words, tied to what the code in that step actually does.
- **Recommended primary talking point:** the naive rolling z-score failure documented in Section 4.4 — a real defect caught with measured evidence (780 false alarms reduced to 242 real flags once idle samples were excluded). It demonstrates understanding of the data rather than just the API.
- **Flagged assumption:** the original workshop instructions mention testing "your Inverted Index with 2 phrase queries" — there is no inverted index or text-search component in this use case; that line appears to be leftover boilerplate from a different exercise template. We are treating it as not applicable. If the instructor does intend a query-testing requirement, the closest equivalent is running 2 sample SQL queries against `robot_readings` (e.g. filter by an axis threshold, filter by a time range) and documenting the results — call this out explicitly in the notebook if included as a substitute.
- **Submission checklist:**
  - [ ] Notebook with demo code for streaming/collection, DB persistence, visualization, and the predictive analytics module (Sections 4.2–4.4)
  - [ ] Markdown explanations for each major step
  - [ ] Labeled team talking point(s)
  - [ ] `README.md` updated with all four team member names, use case description, and dataset link/license
  - [ ] Public GitHub repo `DATASTREAMVISUALIZATION-GROUP4` with at least one meaningful commit per person
  - [ ] Email to instructor with the `.git` link — subject: `CSCN8010 - Data Stream Visualization Workshop, Team #___`
