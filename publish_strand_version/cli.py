import argparse
import importlib.metadata
import json
import logging
import sys

import semver

from publish_strand_version.exceptions import StrandsException
from publish_strand_version.mutations import publish_strand_version

logger = logging.getLogger(__name__)


RED = "\033[0;31m"
GREEN = "\033[0;32m"
NO_COLOUR = "\033[0m"


def main(argv=None):
    """Publish a strand version for a new or existing strand. If this succeeds, exit successfully with an exit code of
    0; if it doesn't, exit with an exit code of 1.

    :return None:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("account", help="The handle of the account the strand belongs to.")
    parser.add_argument("name", help="The name of the strand.")
    parser.add_argument(
        "path",
        help="The path to the JSON schema for the new strand version. The path must be relative to the repository "
        "root.",
    )
    parser.add_argument("version", help="The semantic version to give the new strand version.")
    parser.add_argument("notes", default=None, help="Any notes to associate to this strand version.")

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

    semantic_version = semver.Version.parse(args.version)

    try:
        strand_version_uuid = publish_strand_version(
            account=args.account,
            name=args.name,
            json_schema=json_schema,
            major=semantic_version.major,
            minor=semantic_version.minor,
            patch=semantic_version.patch,
            candidate=semantic_version.prerelease,
            notes=args.notes,
        )

    except StrandsException:
        logger.exception(f"{RED}Strand version publishing failed.{NO_COLOUR}")
        sys.exit(1)

    logger.info(f"{GREEN}Strand version publishing succeeded (UUID: {strand_version_uuid}).{NO_COLOUR}")
    sys.exit(0)


if __name__ == "__main__":
    main()
