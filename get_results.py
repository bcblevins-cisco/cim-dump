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

ids = []

for p in PROJECT_IDS:
    for i in range(1): #NOTE: limit to 4 pages of results for testing
        response = requests.get(f"{PIPELINES_URL}/{p}/{i}/ids")
        data = response.json()
        if len(data['pipeline_ids']) == 0:
            print(f"End of ID groups for project {p}\n")
            break
        print(f"Pipeline group {i} for project {p} captured")
        ids.extend(data['pipeline_ids'])

print(f"\nCaptured a total of {len(ids)} pipeline IDs.")

# endregion

# ============================================================================================
# region Fetch Test Details

results = []
count = 0

for id in ids[:5]: #NOTE: Limit to 5 during testing
    count += 1
    response = requests.get(f"{ONE_PIPELINE_URL}/{id}")
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

        results.append({
            "test_case": stage["name"],
            "result": f"Passed: {passed}, Total: {total}",
            "bundle": version_to_integer(version),
            "cim_url": f"{CIM_BASE_URL}/{id}",
            "timestamp": stage["end_time"],
            "platform": "3110"
        })

output_filename = 'automation_results.json'
with open(output_filename, 'w') as f:
    json.dump(results, f, indent=4)

print(f"\nResults have been saved to {output_filename}")

# endregion