# CIM Pipeline Results Fetcher

## Overview
Fetches automation pipeline results from a CIM service and stores them. The script retrieves pipeline IDs for specified projects, fetches detailed test run data for each pipeline, aggregates results, and writes them to a SQLite database by default (or JSON if configured).

## Requirements
- Python 3.12.
- Access to the internal company network to reach the CIM service.
- Local Python module available on the import path: `version_tools` (provides `version_to_integer`).
- Python packages:
  - certifi==2025.8.3.
  - charset-normalizer==3.4.3.
  - idna==3.10.
  - python-dotenv==1.1.1.
  - requests==2.32.5.
  - urllib3==2.5.0.

## Setup
- (Optional) Create and activate a virtual environment.
- Install dependencies (either from `requirements.txt` if present, or individually):
  - `pip install -r requirements.txt`
  - Or: `pip install certifi==2025.8.3 charset-normalizer==3.4.3 idna==3.10 python-dotenv==1.1.1 requests==2.32.5 urllib3==2.5.0`.

Ensure the `version_tools` module is available on `PYTHONPATH`.

## Configuration
Provide a `.env` file in the project root with placeholders similar to the following. Values shown are examples only.

```
PROJECT_IDS=123,456
PIPELINES_URL=https://cim.example.internal/api/pipelines
ONE_PIPELINE_URL=https://cim.example.internal/api/pipeline
RUN_BASE_URL=https://cim.example.internal/api/runs
RUN_END_URL=limit=100&page_size=50
CIM_BASE_URL=https://cim.example.internal
```

Notes:
- `PROJECT_IDS` is a comma-separated list.
- Other URLs should point to the appropriate CIM endpoints.

## Usage
Run the script directly:

```
python get_results.py
```

Behavior:
- Reads configuration from `.env`.
- Fetches pipeline IDs for the listed projects.
- Retrieves stage-level test runs, sums passed/total, and associates a bundle version via `version_tools.version_to_integer`.
- Writes results by default to a SQLite database; alternatively, writes to JSON if configured in code.

## Outputs
- SQLite database (default): `automation_testing.db`.
  - Table `results` (created if missing) with columns:
    - `id` (auto-increment).
    - `test_case` (text).
    - `bundle` (integer).
    - `result` (text, e.g., “Passed: X, Total: Y”).
    - `platform` (text).
    - `cim_url` (text).
    - `timestamp` (datetime).
  - Example terminal message: `Inserted N records into the database.`

- JSON (if enabled in code): `automation_results.json`.
  - Example terminal message: `Inserted N records into automation_results.json.`

## Modes and Flags
These are defined in the script source:
- `POST_DB = True` controls destination (True = SQLite, False = JSON).
- `DEV = True` limits API calls for quicker runs (e.g., fewer pages and pipelines). Set to `False` for full fetching.

## Notes
- Network access to the CIM service is required (internal-only endpoints). If your environment uses proxies, ensure they are configured at the system or `requests` level.
- No CLI flags are provided; the script is “run and go” based on `.env` and in-code defaults.