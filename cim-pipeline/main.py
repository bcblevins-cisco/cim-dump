import argparse
import logging
import sys
from dotenv import dotenv_values

from models import Config
from orchestrator import CimOrchestrator
from outputs import JsonOutput, SqliteOutput, OutputBase


def setup_logging() -> logging.Logger:
    """Configures a logger to output to both console (INFO) and a file (DEBUG)."""
    logger = logging.getLogger("CimPipelineLogger")
    logger.setLevel(logging.DEBUG)
    
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    fh = logging.FileHandler('cim_pipeline.log', mode='w') 
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger


def setup_argparse() -> argparse.Namespace:
    """Configures and parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetches automation pipeline results from a CIM service and stores them."
    )
    parser.add_argument(
        "--output",
        choices=["json", "sqlite"],
        default="json",
        help="Output format. Default: json.",
    )
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Run in production mode (disables dev limits). Default is dev mode.",
    )
    parser.add_argument(
        "--output-file",
        help="Output file path. Defaults to 'automation_results.json' or 'automation_results.db'.",
    )
    return parser.parse_args()


def create_config(args: argparse.Namespace) -> Config:
    """Creates a Config object from environment variables and command-line arguments."""
    try:
        env = dotenv_values(".env")
        project_ids = env["PROJECT_IDS"].split(",")
        if not all([env.get("PROJECT_IDS"), env.get("PIPELINES_URL"), env.get("ONE_PIPELINE_URL")]):
            raise KeyError("One or more required environment variables are missing in .env file.")
    except KeyError as e:
        raise ValueError(f"Missing required environment variable in .env file: {e}") from e

    output_file = args.output_file or \
                  ("automation_results.json" if args.output == "json" else "automation_results.db")

    return Config(
        project_ids=project_ids,
        pipelines_url=env["PIPELINES_URL"],
        one_pipeline_url=env["ONE_PIPELINE_URL"],
        run_base_url=env.get("RUN_BASE_URL", ""), 
        run_end_url=env.get("RUN_END_URL", ""),
        cim_base_url=env.get("CIM_BASE_URL", ""),
        dev=not args.prod,
        output_type=args.output,
        output_file=output_file
    )


def create_output_handler(config: Config, logger: logging.Logger) -> OutputBase:
    """Factory function to create the appropriate output handler."""
    if config.output_type == "json":
        return JsonOutput(config, logger)
    if config.output_type == "sqlite":
        return SqliteOutput(config, logger)
    
    raise ValueError(f"Unsupported output type specified: {config.output_type}")


def main():
    """Main entry point for the application."""
    logger = setup_logging()
    try:
        args = setup_argparse()
        config = create_config(args)
        
        logger.info(f"Starting application in {'PROD' if not config.dev else 'DEV'} mode.")
        logger.info(f"Output target: {config.output_type} -> '{config.output_file}'")

        output_handler = create_output_handler(config, logger)
        
        orchestrator = CimOrchestrator(config, logger, output_handler)
        orchestrator.run()

    except (ValueError, KeyError) as e:
        logger.critical(f"Configuration Error: {e}")
        sys.exit(1) 
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()