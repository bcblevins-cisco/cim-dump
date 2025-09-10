# CIM Pipeline Data Fetcher

A command-line tool for fetching automation pipeline results from a CIM service, processing them, and storing them in either a JSON file or a SQLite database.

This tool is designed to be robust, configurable, and easy to use, providing detailed logging and flexible output options.

## Key Features

-   **Multiple Output Formats**: Save results as a structured `JSON` file or in a `SQLite` database.
-   **Configurable Modes**: Run in **Development** mode to limit API calls for faster testing, or switch to **Production** mode to fetch all data.
-   **Robust Error Handling**: Gracefully handles network errors, API issues, and malformed data without crashing.
-   **Centralized Configuration**: All API endpoints and parameters are managed via a `.env` file and command-line arguments.
-   **Detailed Logging**: Logs high-level progress to the console and detailed debug information to a file (`cim_pipeline.log`).
-   **Modular and Maintainable Code**: The application is split into logical components (API, Processing, Output, Orchestration) for clarity and ease of maintenance.

## Prerequisites

-   Python 3.7+
-   `pip` for installing packages

## Installation & Setup

**1. Clone the Repository**

```bash
git clone <your-repository-url>
cd <your-repository-name>
```

**2. Install Dependencies**

The required Python packages are listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```

*(Note: If you don't have a `requirements.txt` file, create one with the following content:)*
```
# requirements.txt
requests
python-dotenv
```

**3. Configure Environment Variables**

The script requires API endpoints and project IDs to be configured in a `.env` file.

Create a file named `.env` in the root of the project. Edit the `.env` file with your specific values:

```ini
# .env

# Comma-separated list of project IDs to query
PROJECT_IDS=project1,project2,project3

# API Endpoints
PIPELINES_URL="https://your-api.com/v1/projects"
ONE_PIPELINE_URL="https://your-api.com/v1/pipelines"
CIM_BASE_URL="https://your-cim-instance.com/pipelines"
```

## Usage

The script is run from the command line using `main.py`.

#### **Default Usage (Development Mode, JSON Output)**

This will run in development mode (limited API calls) and save the results to `automation_results.json`.

```bash
python main.py
```

#### **Running in Production Mode**

Use the `--prod` flag to disable development limits and fetch all data.

```bash
python main.py --prod
```

#### **Specifying SQLite Output**

Use the `--output sqlite` argument to save results to a SQLite database. The default file will be `automation_results.db`.

```bash
python main.py --output sqlite
```

#### **Specifying a Custom Output File**

Use the `--output-file` argument to set a custom name or path for the output.

```bash
python main.py --output-file my_custom_results.json
```

#### **Combined Example (Production, SQLite, Custom File)**

This command runs in production mode, saves to a SQLite database, and names the file `production_data.db`.

```bash
python main.py --prod --output sqlite --output-file production_data.db
```

### Command-Line Arguments

| Argument        | Description                                                                  | Default                        |
| --------------- | ---------------------------------------------------------------------------- | ------------------------------ |
| `--prod`        | Disables development mode to fetch all data.                                 | (Dev mode is default)          |
| `--output`      | The output format. Choices: `json`, `sqlite`.                                | `json`                         |
| `--output-file` | The path for the output file.                                                | `automation_results.json` or `automation_results.db` |

## Project Structure

The project is organized into several modules, each with a specific responsibility:

```
.
├── main.py
├── cim_fetcher/
│   ├── __init__.py 
│   ├── orchestrator.py
│   ├── api.py
│   ├── processing.py
│   ├── outputs.py
│   └── models.py
├── .env
└── requirements.txt
```  
 
