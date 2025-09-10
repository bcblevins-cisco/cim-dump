from dataclasses import dataclass
from typing import List, Optional



@dataclass(frozen=True)
class Config:
    """
    Configuration for CIM pipeline automation.

    Stores API URLs, project IDs, output settings, and operational parameters.
    """
    project_ids: List[str]
    pipelines_url: str
    one_pipeline_url: str
    run_base_url: str
    run_end_url: str
    cim_base_url: str

    # Behavior and CLI toggles
    output_type: str            # 'json' or 'sqlite'
    dev: bool                   # True by default (limits API volume)
    output_file: Optional[str]  # Path to json or sqlite file

    # Dev/Prod limits
    max_pages_dev: int = 4
    max_pages_prod: int = 100
    max_pipelines_dev: int = 5
    platform: str = "3110"

