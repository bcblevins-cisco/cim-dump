import logging
from typing import List, Dict, Optional, Any

import requests
from requests.exceptions import RequestException, JSONDecodeError
from models import Config


class CimApi:
    """
    Client for interacting with the CIM API.

    Implements methods to fetch pipeline IDs and their corresponding details.
    Uses a requests.Session for efficiency and includes robust error handling.
    """

    def __init__(self, config: Config, logger: logging.Logger) -> None:
        """
        Initialize the CimApi client.

        Args:
            config (Config): Configuration object with API URLs and settings.
            logger (logging.Logger): Logger for status and error messages.
        """
        self.config: Config = config
        self.logger: logging.Logger = logger
        self.session: requests.Session = requests.Session() # Create a session object

        self.pipeline_ids: List[str] = []
        self.raw_results: List[Dict] = []

    def _make_request(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Private helper to perform a GET request and handle common errors.

        Args:
            url (str): The URL to send the GET request to.

        Returns:
            A dictionary with the JSON response, or None if an error occurred.
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status() 
            return response.json()

        except JSONDecodeError:
            # The response text might not exist if the request fully failed
            response_text = getattr(response, 'text', 'N/A')
            self.logger.error(f"Failed to decode JSON from {url}. Response text: {response_text[:100]}")

        except RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")

        return None

    def get_pipeline_ids(self) -> None:
        """
        Fetch all pipeline IDs for the project IDs specified in the config.
        """
        ids: List[str] = []
        page_limit = self.config.max_pages_dev if self.config.dev else self.config.max_pages_prod

        for project_id in self.config.project_ids:
            for i in range(page_limit):
                url = f"{self.config.pipelines_url}/{project_id}/{i}/ids"
                data = self._make_request(url)


                if data is None:
                    break

                pipeline_ids = data.get('pipeline_ids', [])
                if not pipeline_ids:
                    self.logger.info(f"End of ID groups for project {project_id}")
                    break

                self.logger.info(f"Pipeline group {i} for project {project_id} captured")
                ids.extend(pipeline_ids)

        self.logger.info(f"Captured a total of {len(ids)} pipeline IDs.")
        self.pipeline_ids = ids

    def get_pipeline_results(self) -> None:
        """
        Fetch and process detailed results for each pipeline ID.
        """
        self.raw_results = []
        
        pipelines_to_fetch = (
            self.pipeline_ids[:self.config.max_pipelines_dev]
            if self.config.dev
            else self.pipeline_ids
        )

        for pipeline_id in pipelines_to_fetch:
            url = f"{self.config.one_pipeline_url}/{pipeline_id}"
            data = self._make_request(url)

            if data:
                self.raw_results.append(data)

        self.logger.info(f"Successfully captured details for {len(self.raw_results)} pipelines.")