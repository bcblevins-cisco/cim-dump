from datetime import datetime, timezone
import sqlite3
from typing import List
from dotenv import dotenv_values
import requests
from version_tools import version_to_integer
import json


# ============================================================================================
# region Environment Setup

ENV = dotenv_values(".env")

PROJECT_IDS = ENV["PROJECT_IDS"].split(",")
PIPELINES_URL = ENV["PIPELINES_URL"]
ONE_PIPELINE_URL = ENV["ONE_PIPELINE_URL"]
RUN_BASE_URL = ENV["RUN_BASE_URL"]
RUN_END_URL = ENV["RUN_END_URL"]
CIM_BASE_URL = ENV["CIM_BASE_URL"]

POST_DB = True
DEV = True

# endregion

# ============================================================================================
# region Main Fns


def get_pipeline_ids(project_ids: List[str], url: str):

    local_ids = []
    for p in project_ids:
        for i in range(4 if DEV else 100): #NOTE: limit to 4 pages of results for testing
            response = requests.get(f"{url}/{p}/{i}/ids")
            data = response.json()
            if len(data['pipeline_ids']) == 0:
                print(f"End of ID groups for project {p}\n")
                break
            print(f"Pipeline group {i} for project {p} captured")
            local_ids.extend(data['pipeline_ids'])

    print(f"\nCaptured a total of {len(local_ids)} pipeline IDs.")
    return local_ids


def get_pipelines(url: str, ids: List[str]):
    local_results = []
    count = 0
    for id in ids[:5] if DEV else ids: #NOTE: Limit to 5 during testing
        count += 1
        response = requests.get(f"{url}/{id}")
        data = response.json()
        print(f"Pipeline {count} recieved:", data['project']['name'])
        stages = data['stages']
        version = data['test_data']['__VERSION__']
        for stage in stages:
            if "report" in stage["name"]:
                continue

            stage_id = stage["id"]

            test_runs_raw = requests.get(f"{RUN_BASE_URL}/{stage_id}?{RUN_END_URL}")
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


def write_to_json(results_data: List[dict[str,str]], filename='automation_results.json'):
    with open(filename, 'w') as f:
        json.dump(results_data, f, indent=4)
    print(f"Successfully inserted {len(results_data)} records into {filename}.")


def insert_into_db(results_data: List[dict[str,str]], db_path='automation_testing.db'):
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
            INSERT INTO results (test_case, result, bundle, cim_url, timestamp, platform)
            VALUES (?, ?, ?, ?, ?, ?)
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
    print(f"Successfully inserted {len(results_data)} records into the database.")


# endregion

# ============================================================================================
# region Main Project Flow


pipeline_ids = get_pipeline_ids(PROJECT_IDS, PIPELINES_URL)
results = get_pipelines(ONE_PIPELINE_URL, pipeline_ids)

if POST_DB:
    insert_into_db(results)
else:
    write_to_json(results)


# endregion
