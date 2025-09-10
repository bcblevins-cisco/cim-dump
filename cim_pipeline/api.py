import logging
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import JSONDecodeError, RequestException

from .models import Config


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
        self.session: requests.Session = requests.Session()

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
            response_text = getattr(response, 'text', 'N/A')
            self.logger.error(
                "Failed to decode JSON from %s. Response text: %s",
                url,
                response_text[:100]
            )

        except RequestException as e:
            self.logger.error("Request failed for %s: %s", url, e)

        return None

    def get_pipeline_ids(self) -> None:
        """
        Fetch all pipeline IDs for the project IDs specified in the config.
        """
        ids: List[str] = []
        page_limit = (
            self.config.max_pages_dev
            if self.config.dev
            else self.config.max_pages_prod
        )

        for project_id in self.config.project_ids:
            for i in range(page_limit):
                url = f"{self.config.pipelines_url}/{project_id}/{i}/ids"
                data = self._make_request(url)

                if data is None:
                    break

                pipeline_ids = data.get('pipeline_ids', [])
                if not pipeline_ids:
                    self.logger.info(
                        "End of ID groups for project %s", project_id
                    )
                    break

                self.logger.info(
                    "Pipeline group %d for project %s captured", i, project_id
                )
                ids.extend(pipeline_ids)

        self.logger.info(
            "Captured a total of %d pipeline IDs.", len(ids)
        )
        self.pipeline_ids = ids

    def get_pipeline_results(self) -> None:
        """
        Fetch and process detailed results for each pipeline ID.
        """
        self.raw_results = []

        LOG_INTERVAL = 100

        pipelines_to_fetch = (
            self.pipeline_ids[:self.config.max_pipelines_dev]
            if self.config.dev
            else self.pipeline_ids
        )

        total_pipelines = len(pipelines_to_fetch)
        self.logger.info(
            "Attempting to fetch details for %d pipelines...", total_pipelines
        )

        for i, pipeline_id in enumerate(pipelines_to_fetch):
            self.logger.debug(
                "Fetching details for pipeline ID: %s", pipeline_id
            )

            if (i + 1) % LOG_INTERVAL == 0:
                self.logger.info(
                    "Progress: Fetched %d of %d pipeline details...",
                    i + 1,
                    total_pipelines
                )

            url = f"{self.config.one_pipeline_url}/{pipeline_id}"
            data = self._make_request(url)

            if data:
                self.raw_results.append(data)

        self.logger.info(
            "Successfully captured details for %d pipelines.",
            len(self.raw_results)
        )
