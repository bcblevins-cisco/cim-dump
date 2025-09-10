"""
Fetches automation pipeline results from a CIM service and stores them.

This script retrieves pipeline IDs for specified projects, fetches detailed
test run data for each pipeline, processes the results, and then stores
them either in a JSON file or a SQLite database.
"""
# TODO: Create an orchestrator class in app.py to manage the overall workflow.
# This class would initialize the API client, result processor, and output handlers.
# It would call the methods to fetch, process, and store the data.

# TODO: Create a cli.py module using argparse to handle command-line arguments.
# This would allow for dynamic configuration, e.g., specifying project IDs,
# output format (JSON/SQLite), and development mode from the command line.
import sqlite3
import json
from typing import List

import requests
from dotenv import dotenv_values

from version_tools import version_to_integer



# ============================================================================================
# region Environment Setup

# TODO: This configuration could be encapsulated in a dedicated Config class,
# or handled within the CimApi class constructor.
ENV = dotenv_values(".env")

PROJECT_IDS = ENV["PROJECT_IDS"].split(",")
PIPELINES_URL = ENV["PIPELINES_URL"]
ONE_PIPELINE_URL = ENV["ONE_PIPELINE_URL"]
RUN_BASE_URL = ENV["RUN_BASE_URL"]
RUN_END_URL = ENV["RUN_END_URL"]
CIM_BASE_URL = ENV["CIM_BASE_URL"]

# TODO: The POST_DB and DEV flags should be replaced by command-line arguments
# handled by the cli.py module.
POST_DB = True
# Flag for development mode to limit the number of API calls
DEV = True

# endregion

# ============================================================================================
# region Main Fns


# TODO: This function should be a method within a `CimApi` class.
# The class would handle all interactions with the CIM API.
# e.g., `cim_api.get_pipeline_ids(project_ids)`
def get_pipeline_ids(project_ids: List[str], url: str):
    """
    Fetch all pipeline IDs for a given list of project IDs.

    Args:
        project_ids: A list of project IDs to query.
        url: The base URL to fetch pipeline ID groups from.

    Returns:
        A list of all pipeline IDs found across all specified projects.
    """
    local_ids = []
    for p in project_ids:
        # The API paginates the IDs into groups, so we iterate through pages.
        for i in range(4 if DEV else 100):
            response = requests.get(f"{url}/{p}/{i}/ids")
            data = response.json()
            # An empty list indicates the last page has been reached.
            if len(data['pipeline_ids']) == 0:
                print(f"End of ID groups for project {p}\n")
                break
            print(f"Pipeline group {i} for project {p} captured")
            local_ids.extend(data['pipeline_ids'])

    print(f"\nCaptured a total of {len(local_ids)} pipeline IDs.")
    return local_ids


# TODO: This function's logic should be split.
# The API fetching part (`requests.get`) should be in the `CimApi` class.
# The data transformation part (looping, creating the dictionary) should be in a `ResultProcessor` class.
def get_pipelines(url: str, ids: List[str]):
    """
    Fetch and process detailed results for each pipeline ID.

    Args:
        url: The base URL to fetch individual pipeline data.
        ids: A list of pipeline IDs to process.

    Returns:
        A list of dictionaries, each containing processed test result data.
    """
    local_results = []
    count = 0
    # Limit to 5 pipelines in development mode for faster testing
    for id in ids[:5] if DEV else ids:
        count += 1
        # TODO: This API call should be moved to the `CimApi` class.
        response = requests.get(f"{url}/{id}")
        data = response.json()
        print(f"Pipeline {count} recieved:", data['project']['name'])
        # TODO: This part of the logic should be handled by a `ResultProcessor` class.
        stages = data['stages']
        version = data['test_data']['__VERSION__']
        for stage in stages:
            # Skip stages that are for reporting and not actual tests
            if "report" in stage["name"]:
                continue

            stage_id = stage["id"]

            # TODO: This API call should also be in the `CimApi` class.
            test_runs_raw = requests.get(
                f"{RUN_BASE_URL}/{stage_id}?{RUN_END_URL}"
                )
            test_runs = test_runs_raw.json()

            passed = 0
            total = 0
            for r in test_runs:
                total += int(r['total'])
                passed += int(r['passed'])

            local_results.append({
                "test_case": stage["name"],
                "result": f"Passed: {passed}, Total: {total}",
                "bundle": version_to_integer(version),
                "cim_url": f"{CIM_BASE_URL}/{id}",
                "timestamp": stage["end_time"],
                "platform": "3110"
            })
    return local_results


# TODO: This function should be a method in a `JsonOutput` class.
# This class would inherit from an abstract `OutputBase` class that defines a common `write(results)` interface.
def write_to_json(
    results_data: List[dict[str, str]],
    filename='automation_results.json'
):
    """
    Write a list of dictionaries to a JSON file.

    Args:
        results_data: The list of result dictionaries to write.
        filename: The name of the output JSON file.
    """
    with open(filename, 'w') as f:
        json.dump(results_data, f, indent=4)
    print(f"Inserted {len(results_data)} records into {filename}.")


# TODO: This function should be a method in a `SqliteOutput` class.
# This class would inherit from an abstract `OutputBase` class that defines a common `write(results)` interface.
def insert_into_db(
    results_data: List[dict[str, str]],
    db_path='automation_testing.db'
):
    """
    Insert a list of test results into a SQLite database.

    Creates the 'results' table if it doesn't exist, then inserts
    each result from the provided list.

    Args:
        results_data: A list of result dictionaries to insert.
        db_path: The file path for the SQLite database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS "results" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_case TEXT NOT NULL,
            bundle INTEGER NOT NULL,
            result TEXT NOT NULL,
            platform TEXT NOT NULL,
            cim_url TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

    for result in results_data:

        cursor.execute("""
            INSERT INTO results (
                test_case,
                result,
                bundle,
                cim_url,
                timestamp,
                platform
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                result["test_case"],
                result["result"],
                result["bundle"],
                result["cim_url"],
                result["timestamp"],
                result["platform"]
        ))

    conn.commit()
    conn.close()
    print(f"Inserted {len(results_data)} records into the database.")


# endregion

# ============================================================================================
# region Main Project Flow

# TODO: This main execution block should be moved into the orchestrator class in `app.py`.
# The orchestrator would use the CLI arguments to decide which output strategy to use (JSON or SQLite).
pipeline_ids = get_pipeline_ids(PROJECT_IDS, PIPELINES_URL)
results = get_pipelines(ONE_PIPELINE_URL, pipeline_ids)

if POST_DB:
    insert_into_db(results)
else:
    write_to_json(results)


# endregion
