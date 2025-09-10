from dotenv import dotenv_values
from models import Config
import argparse



def setupParseArgs():
    # --prod (bool), --output (json or sqlite), --output-file
    parser = argparse.ArgumentParser(
        description="Fetches automation pipeline results from a CIM service and stores them."
    )
    parser.add_argument(
        "--output",
        choices=["json", "sqlite"],
        default="json",
        help="Output target. Default: json.",
    )
    dev_group = parser.add_mutually_exclusive_group()
    dev_group.add_argument(
        "--dev",
        dest="dev",
        action="store_true",
        default=True,
        help="Enable dev mode (limits pages and pipelines). Default: on.",
    )
    dev_group.add_argument(
        "--no-dev",
        dest="dev",
        action="store_false",
        help="Disable dev mode.",
    )
    parser.add_argument(
        "--output-file",
        default=None,
        help="Output file path. Defaults: automation_results.json (json) or automation_testing.db (sqlite).",
    )
    return parser.parse_args()


# Create environment
def setupEnvironment(args):
    output_file = ""
    if args.output_file:
        output_file = args.output_file
    else:
        output_file = "automation_results.json" if args.output == "json" else "automation_results.db"

    env = dotenv_values(".env")
    return Config(
        project_ids = env["PROJECT_IDS"].split(","),
        pipelines_url = env["PIPELINES_URL"],
        one_pipeline_url = env["ONE_PIPELINE_URL"],
        run_base_url = env["RUN_BASE_URL"],
        run_end_url = env["RUN_END_URL"],
        cim_base_url = env["CIM_BASE_URL"],
        dev=args.dev,
        output_type=args.output,
        output_file=output_file
    )

# Instance orchestrator


# Run 