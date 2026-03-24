from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_CONFIG_NAME = "proofagent.yaml"

STARTER_CONFIG = """# ProofAgent™ — project configuration
# Official ProofAgent™ Python SDK: https://www.proofagent.ai
#
# Set your API key here or export PROOFAGENT_API_KEY in your environment.

api_key: ""
base_url: "https://api.proofagent.ai"
# timeout_seconds: 60
# max_retries: 3
# retry_backoff_seconds: 0.75
"""


def cmd_init(path: Path, *, force: bool) -> int:
    if path.exists() and not force:
        print(f"File already exists: {path}", file=sys.stderr)
        print("Use --force to overwrite.", file=sys.stderr)
        return 1
    path.write_text(STARTER_CONFIG, encoding="utf-8")
    print("Welcome to ProofAgent™ — the AI agent evaluation platform.")
    print(f"Created starter config: {path.resolve()}")
    print("Next: set api_key in the file or PROOFAGENT_API_KEY, then use the SDK from Python.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="proofagent",
        description="ProofAgent™ — official CLI for the ProofAgent™ Python SDK.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="Create a starter proofagent.yaml in the current directory.")
    init_p.add_argument(
        "-o",
        "--output",
        default=DEFAULT_CONFIG_NAME,
        metavar="FILE",
        help=f"Config file to write (default: {DEFAULT_CONFIG_NAME})",
    )
    init_p.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite the config file if it already exists.",
    )

    args = parser.parse_args()
    if args.command == "init":
        return cmd_init(Path(args.output), force=args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
