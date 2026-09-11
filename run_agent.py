"""Run the local AmazonHelp support agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.agent import AmazonHelpAgent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--message", required=True, help="Customer message to analyze")
    args = parser.parse_args()
    result = AmazonHelpAgent(Path(__file__).resolve().parent).respond(args.message)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
