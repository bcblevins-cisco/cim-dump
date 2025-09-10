from dataclasses import dataclass
from typing import List, Optional


@dataclass()
class Config:
    """
    Configuration for CIM pipeline automation.

    Stores API URLs, project IDs, output settings, and operational parameters.
    """
    project_ids: List[str]
    pipelines_url: str
    one_pipeline_url: str
    cim_base_url: str

    # Behavior and CLI toggles
    output_type: str
    dev: bool
    output_file: Optional[str]

    # Dev/Prod limits
    max_pages_dev: int = 4
    max_pages_prod: int = 100
    max_pipelines_dev: int = 5
    platform: str = "3110"


@dataclass(frozen=True)
class ResultRecord:
    """
    Represents a single test result record for a pipeline stage.

    Attributes:
        test_case (str): Name of the test case or stage.
        result (str): Result summary (e.g., 'Passed: X, Total: Y').
        bundle (int): Integer representation of the bundle version.
        cim_url (str): URL to the CIM pipeline.
        timestamp (str): Timestamp of the test completion.
        platform (str): Platform identifier.
    """
    test_case: str
    result: str
    bundle: int
    cim_url: str
    timestamp: str
    platform: str
