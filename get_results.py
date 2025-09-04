from datetime import datetime, timezone
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

# endregion

# ============================================================================================

# region Fetch Pipeline IDs


def get_pipeline_ids(project_ids, url):
    local_ids = []
    for p in project_ids:
        for i in range(1): #NOTE: limit to 4 pages of results for testing
            response = requests.get(f"{url}/{p}/{i}/ids")
            data = response.json()
            if len(data['pipeline_ids']) == 0:
                print(f"End of ID groups for project {p}\n")
                break
            print(f"Pipeline group {i} for project {p} captured")
            local_ids.extend(data['pipeline_ids'])

    print(f"\nCaptured a total of {len(local_ids)} pipeline IDs.")
    return local_ids

# endregion

# ============================================================================================
# region Fetch Test Details


def get_pipelines(url, ids):
    local_results = []
    count = 0
    for id in ids[:5]: #NOTE: Limit to 5 during testing
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

# endregion

# ============================================================================================
# region Main Project Flow


pipeline_ids = get_pipeline_ids(PROJECT_IDS, PIPELINES_URL)
results = get_pipelines(ONE_PIPELINE_URL, pipeline_ids)


output_filename = 'automation_results.json'
with open(output_filename, 'w') as f:
    json.dump(results, f, indent=4)

print(f"\nResults have been saved to {output_filename}")

# endregion


