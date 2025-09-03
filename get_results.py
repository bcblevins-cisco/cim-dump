from dotenv import dotenv_values
import requests


# ============================================================================================
# region Environment Setup
ENV = dotenv_values(".env")

PROJECT_IDS = ENV["PROJECT_IDS"].split(",")
PIPELINES_URL = ENV["PIPELINES_URL"]
ONE_PIPELINE_URL = ENV["ONE_PIPELINE_URL"]
RUN_BASE_URL = ENV["RUN_BASE_URL"]
RUN_END_URL = ENV["RUN_END_URL"]

# endregion

# ============================================================================================

# region Fetch Pipelines

ids = []

for p in PROJECT_IDS:
    for i in range(4): # limit to 4 pages of results for testing
        response = requests.get(f"{PIPELINES_URL}/{p}/{i}/ids")
        data = response.json()
        if len(data['pipeline_ids']) == 0:
            print(f"End of ID groups for project {p}\n")
            break
        print(f"Pipeline group {i} for project {p} captured")
        ids.extend(data['pipeline_ids'])

print(f"\nCaptured a total of {len(ids)} pipeline IDs.")