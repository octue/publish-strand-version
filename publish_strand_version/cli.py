import argparse
import importlib.metadata
import json
import logging
import os
import sys

from publish_strand_version.api import publish_strand_version
from publish_strand_version.exceptions import StrandsException

RED = "\033[0;31m"
GREEN = "\033[0;32m"
NO_COLOUR = "\033[0m"


logging.basicConfig(
    stream=sys.stdout,
    format="[%(asctime)s | %(levelname)s | %(name)s] %(message)s",
    level=logging.INFO,
)


def main(argv=None):
    """Publish a new strand version for an existing strand, or just suggest the new semantic version. If this succeeds,
    exit successfully with an exit code of 0; if it doesn't, exit with an exit code of 1.

    :return None:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("token")
    parser.add_argument("account")
    parser.add_argument("name")
    parser.add_argument("path")
    parser.add_argument("version", nargs="?")
    parser.add_argument("notes", nargs="?", default=None)
    # Strings instead of booleans are used below as GitHub Actions input defaults don't support booleans.
    parser.add_argument("allow_beta", nargs="?", default="true")
    parser.add_argument("suggest_only", nargs="?", default="false")

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=importlib.metadata.version("publish-strand-version"),
    )

    args = parser.parse_args(argv)

    if args.allow_beta.lower() == "true":
        allow_beta = True
    else:
        allow_beta = False

    if args.suggest_only.lower() == "true":
        suggest_only = True
        mode = "SUGGESTION"
    else:
        suggest_only = False
        mode = "PUBLISHING"

    with open(args.path) as f:
        json_schema = json.load(f)

    try:
        strand_url, strand_version_url, strand_version_uuid, version = publish_strand_version(
            token=args.token,
            account=args.account,
            name=args.name,
            json_schema=json_schema,
            version=args.version,
            notes=args.notes,
            allow_beta=allow_beta,
            suggest_only=suggest_only,
        )

    except StrandsException:
        print(f"{RED}STRAND VERSION {mode} FAILED.{NO_COLOUR}", file=sys.stderr)
        sys.exit(1)

    # Write outputs to GitHub outputs file for action.
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.writelines(
            [
                f"strand_url={strand_url}\n",
                f"version={version}\n",
                f"strand_version_url={strand_version_url}\n",
                f"strand_version_uuid={strand_version_uuid}\n",
            ]
        )

    print(
        f"{GREEN}STRAND VERSION {mode} SUCCEEDED{NO_COLOUR}\n"
        f"- Strand URL: {strand_url}\n"
        f"- Semantic version: {version}\n"
        f"- Strand version URL: {strand_version_url}\n"
        f"- Strand version UUID: {strand_version_uuid}\n"
    )

    sys.exit(0)


if __name__ == "__main__":
    main()
