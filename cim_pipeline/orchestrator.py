import logging
import sys
from typing import Dict, List

from .api import CimApi
from .models import Config, ResultRecord
from .outputs import OutputBase
from .processing import ResultProcessor


class CimOrchestrator:
    """
    Manages the end-to-end workflow for fetching, processing, and saving CIM
    data.

    This class acts as a high-level controller that coordinates the API client,
    the data processor, and the output handler to execute the full data
    pipeline in a sequential, robust, and organized manner.
    """
    def __init__(
        self,
        config:
        Config,
        logger: logging.Logger,
        output_handler: OutputBase
    ):
        """
        Initializes the CimOrchestrator.

        Args:
            config (Config): The application's configuration object.
            logger (logging.Logger): The logger for status and error messages.
            output_handler (OutputBase): The handler responsible for writing
            the final processed data to a destination (e.g., file or database).
        """
        self.config = config
        self.logger = logger
        self.output_handler = output_handler

    def _api_workflow(self) -> List[Dict]:
        """
        Executes the data extraction (API) part of the workflow.

        Returns:
            A list of raw pipeline result dictionaries.
        """
        self.logger.info("Starting API workflow: Fetching pipeline data...")
        api = CimApi(self.config, self.logger)
        api.get_pipeline_ids()
        api.get_pipeline_results()
        self.logger.info("API workflow completed.")
        return api.raw_results

    def _processing_workflow(
        self,
        raw_results: List[Dict]
    ) -> List[ResultRecord]:
        """
        Executes the data transformation (processing) part of the workflow.

        Args:
            raw_results: A list of raw dictionaries from the API client.

        Returns:
            A list of structured ResultRecord objects.
        """
        self.logger.info("Starting processing workflow...")
        processor = ResultProcessor(raw_results, self.config, self.logger)
        processor.process_results()
        self.logger.info("Processing workflow completed.")
        return processor.processed_records

    def _output_workflow(self, processed_records: List[ResultRecord]) -> None:
        """
        Executes the data loading (output) part of the workflow.

        Args:
            processed_records: A list of processed records to be written.
        """
        self.logger.info("Starting output workflow: Writing records...")
        self.output_handler.write(processed_records)
        self.logger.info("Output workflow completed.")

    def run(self):
        """
        Runs the complete end-to-end orchestration workflow.

        This is the main public method that executes the API, processing,
        and output steps, with top-level error handling.
        """
        self.logger.info("CIM Orchestrator starting run.")
        try:
            raw_results = self._api_workflow()

            if not raw_results:
                self.logger.info(
                    "No raw results returned from API. Halting workflow."
                )
                return

            processed_records = self._processing_workflow(raw_results)

            if not processed_records:
                self.logger.info(
                    "No records were produced after processing."
                    "Halting workflow."
                )
                return

            self._output_workflow(processed_records)

            self.logger.info("CIM Orchestrator run finished successfully.")

        except Exception as e:
            self.logger.critical(
                "A critical error occurred during the"
                f"orchestration: {e}", exc_info=True
            )
            sys.exit(1)
