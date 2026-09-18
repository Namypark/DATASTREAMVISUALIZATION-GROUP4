# DataEngineeringOne

A data engineering project with a data collection agent, a database service agent, a controller/orchestrator, and a web UI, tied together with Jupyter/pandas/plotly for analysis and visualization.

## Project Structure

```text
.
├── data/                       # Sample/working datasets (CSV)
├── src/
│   ├── data_collection/        # Data collection agent
│   ├── database-service/       # Database service agent
│   └── controller/             # Orchestration logic
├── web-ui/                     # Web UI interface
├── main.py                     # Entry point
├── pyproject.toml              # Project metadata & dependencies (uv)
└── requirements.txt            # Pinned dependencies (pip)
```

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip`

## Installation

### Option A: using uv (recommended)

1. Install uv if you don't have it:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone the repository and move into it:

   ```bash
   git clone <repo-url>
   cd DataEngineeringOne
   ```

3. Sync dependencies (creates `.venv` and installs from `uv.lock`):

   ```bash
   uv sync
   ```

4. Run the project:

   ```bash
   uv run main.py
   ```

### Option B: using pip + venv

1. Clone the repository and move into it:

   ```bash
   git clone <repo-url>
   cd DataEngineeringOne
   ```

2. Create and activate a virtual environment (Python 3.13):

   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate   # on Windows: .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the project:

   ```bash
   python main.py
   ```

## Usage

Launch the web UI:

```bash
uv run web-ui/web-ui-interface.py
# or, with the venv activated:
python web-ui/web-ui-interface.py
```

Explore the data with Jupyter:

```bash
uv run jupyter lab
```
