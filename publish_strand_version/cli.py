import argparse
import importlib.metadata
import json
import os
import sys

from publish_strand_version.api import publish_strand_version
from publish_strand_version.exceptions import StrandsException

RED = "\033[0;31m"
GREEN = "\033[0;32m"
NO_COLOUR = "\033[0m"


def main(argv=None):
    """Publish a strand version for a new or existing strand. If this succeeds, exit successfully with an exit code of
    0; if it doesn't, exit with an exit code of 1.

    :return None:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "token",
        help="A Strands access token with permission to create a strand version for the given strand.",
    )
    parser.add_argument("account", help="The handle of the account the strand belongs to.")
    parser.add_argument("name", help="The name of the strand.")
    parser.add_argument(
        "path",
        help="The path to the JSON schema for the new strand version. The path must be relative to the repository "
        "root.",
    )
    parser.add_argument("version", nargs="?", help="The semantic version to give the new strand version.")
    parser.add_argument("notes", nargs="?", default=None, help="Any notes to add to the strand version.")

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=importlib.metadata.version("publish-strand-version"),
        help="Print the version of the publish-strand-version CLI.",
    )

    args = parser.parse_args(argv)

    with open(args.path) as f:
        json_schema = json.load(f)

    try:
        strand_url, strand_version_uri, strand_version_uuid = publish_strand_version(
            token=args.token,
            account=args.account,
            name=args.name,
            json_schema=json_schema,
            version=args.version,
            notes=args.notes,
        )

    except StrandsException:
        print(f"{RED}STRAND VERSION PUBLISHING FAILED.{NO_COLOUR}", file=sys.stderr)
        sys.exit(1)

    # Write outputs to GitHub outputs file for action.
    with open(os.environ["GITHUB_OUTPUT"], "a") as f:
        f.writelines(
            [
                f"strand_url={strand_url}",
                f"strand_version_uri={strand_version_uri}",
                f"strand_version_uuid={strand_version_uuid}",
            ]
        )

    print(f"{GREEN}STRAND VERSION PUBLISHING SUCCEEDED:{NO_COLOUR} {strand_version_uuid}.", file=sys.stderr)
    print(strand_version_uuid)
    sys.exit(0)


if __name__ == "__main__":
    main()
