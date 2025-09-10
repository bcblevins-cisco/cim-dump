

import logging
from typing import List
import requests
from models import Config


class CimApi:
    """
    Client for interacting with the CIM API.

    Implements methods to fetch pipeline IDs, pipeline details, and stage runs,
    with error handling.
    """

    def __init__(self, config: Config, logger: logging.Logger) -> None:
        """
        Initialize the CimApi client.

        Args:
            config (Config): Configuration object with API URLs and settings.
            logger (logging.Logger): Logger for status and error messages.
        """
        self.config = config
        self.logger = logger
        self.session = requests.Session()

        self.project_ids = config.project_ids
        self.pipelines_url = config.pipelines_url
        self.one_pipeline_url = config.one_pipeline_url 
        
        self.dev = config.dev


    def get_pipeline_ids(self):
        """
        Fetch all pipeline IDs for a given list of project IDs.

        Args:
            project_ids: A list of project IDs to query.
            url: The base URL to fetch pipeline ID groups from.

        Returns:
            A list of all pipeline IDs found across all specified projects.
        """
        local_ids = []
        for p in self.project_ids:
            # The API paginates the IDs into groups, so we iterate through pages.
            for i in range(4 if self.dev else 100):
                response = requests.get(f"{self.pipelines_url}/{p}/{i}/ids")
                data = response.json()
                # An empty list indicates the last page has been reached.
                if len(data['pipeline_ids']) == 0:
                    print(f"End of ID groups for project {p}\n")
                    break
                print(f"Pipeline group {i} for project {p} captured")
                local_ids.extend(data['pipeline_ids'])

        print(f"\nCaptured a total of {len(local_ids)} pipeline IDs.")
        return local_ids