import logging
from typing import Dict, List

from models import Config, ResultRecord # Assuming Config is also in models
from version_tools import version_to_integer


class ResultProcessor:
    """
    Processes raw pipeline data into a structured list of ResultRecord objects.

    This class is designed to be resilient, gracefully skipping records or stages
    that are malformed or missing required data, while logging appropriate errors.
    """

    def __init__(self, raw_results: List[Dict], config: Config, logger: logging.Logger) -> None:
        """
        Initializes the ResultProcessor.

        Args:
            raw_results (List[Dict]): The raw pipeline data from the API.
            config (Config): The application configuration object.
            logger (logging.Logger): The logger for status and error messages.
        """
        self.raw_results = raw_results
        self.config = config
        self.logger = logger
        self.processed_records: List[ResultRecord] = []

    def _process_single_result(self, result: Dict) -> List[ResultRecord]:
        """
        Processes a single raw pipeline result dictionary into a list of ResultRecords.

        One pipeline result can produce multiple ResultRecords (one per stage).

        Args:
            result (Dict): A single raw pipeline result dictionary.

        Returns:
            A list of ResultRecord objects derived from the result's stages.
        """
        records = []
        
        # Safely extract top-level information using .get() to avoid KeyErrors
        pipeline_id = result.get('id')
        test_data = result.get('test_data', {})
        version = test_data.get('__VERSION__')
        stages = result.get('stages', [])

        if not all([pipeline_id, version, stages]):
            self.logger.warning(f"Skipping result due to missing 'id', '__VERSION__', or 'stages'. Data: {result}")
            return []

        try:
            bundle_version = version_to_integer(version)
        except Exception as e:
            self.logger.error(f"Could not convert version '{version}' for pipeline {pipeline_id}. Skipping. Error: {e}")
            return []

        for stage in stages:
            stage_name = stage.get("name")
            if not stage_name or "report" in stage_name:
                continue

            try:
                record = ResultRecord(
                    test_case=stage_name,
                    result=f"Passed: {stage['total_passed_pct']}%",
                    bundle=bundle_version,
                    cim_url=f"{self.config.cim_base_url}/{pipeline_id}",
                    timestamp=stage["end_time"],
                    platform=self.config.platform
                )
                records.append(record)
            except KeyError as e:
                self.logger.warning(f"Skipping stage '{stage_name}' in pipeline {pipeline_id} due to missing key: {e}")
            except Exception as e:
                self.logger.error(f"An unexpected error occurred while processing stage '{stage_name}' in pipeline {pipeline_id}: {e}")

        return records

    def process_results(self) -> None:
        """
        Processes all raw results and populates the `self.processed_records` list.

        This method iterates through the raw data, delegating the processing of
        each item to a helper method and collecting the structured results.
        """
        self.processed_records = []
        for result in self.raw_results:
            # The helper method handles all logic and errors for a single result
            records_from_result = self._process_single_result(result)
            if records_from_result:
                self.processed_records.extend(records_from_result)
        
        self.logger.info(f"Successfully processed {len(self.raw_results)} raw results into {len(self.processed_records)} records.")