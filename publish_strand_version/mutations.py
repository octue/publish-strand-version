import json
import logging

import gql
from gql.transport.requests import RequestsHTTPTransport
import semver

from publish_strand_version.exceptions import StrandsException

STRANDS_API_URL = "https://api.octue.com/graphql/"

logger = logging.getLogger(__name__)
transport = RequestsHTTPTransport(url=STRANDS_API_URL)
client = gql.Client(transport=transport, fetch_schema_from_transport=True)


def publish_strand_version(account, name, json_schema, version, notes=None):
    strand = _get_strand(account, name)

    if not strand:
        strand = _create_strand(account, name)

    return _create_strand_version(strand=strand, json_schema=json_schema, version=version, notes=notes)


def _get_strand(account, name):
    parameters = {"account": account, "name": name}
    suid = f"{account}/{name}"

    query = gql.gql(
        """
        query getStrand(
            $account: String!,
            $name: String!,
        ){
            strand(account: $account, name: $name) {
                uuid
            }
        }
        """
    )

    response = client.execute(query, variable_values=parameters)["strand"]

    if response:
        if response.get("messages"):
            raise StrandsException(response["messages"])

        logger.info("Strand %r found.", suid)
        return response["uuid"]

    logger.info("Strand %r not found.", suid)
    return response


def _create_strand(account, name):
    parameters = {"account": account, "name": name}

    query = gql.gql(
        """
        query createStrand(
            $account: String!,
            $name: String!,
        ){
            createStrand(account: $account, name: $name) {
                uuid
            }
        }
        """
    )

    logger.info("Creating strand %r...", f"{account}/{name}")
    response = client.execute(query, variable_values=parameters)["createStrand"]

    if "messages" in response:
        raise StrandsException(response["messages"])

    logger.info("Finished creating strand.")
    return response["uuid"]


def _create_strand_version(strand, json_schema, version, notes=None):
    """Create a strand version for an existing strand.

    :param str strand: the UUID of the strand to create a new version for
    :param dict json_schema: the JSON schema for the strand version
    :param str version: the semantic version for the strand version
    :param str|None notes: any notes to associate with the strand version
    :return dict: either a successful response containing the strand version's UUID or an error response
    """
    semantic_version = semver.Version.parse(version)

    parameters = {
        "strand": strand,
        "json_schema": json.dumps(json.dumps(json_schema)),
        "major": semantic_version.major,
        "minor": semantic_version.minor,
        "patch": semantic_version.patch,
        "candidate": semantic_version.prerelease,
        "notes": notes,
    }

    query = gql.gql(
        """
        mutation createStrandVersion(
            $strand: String!,
            $json_schema: String!,
            $major: String!,
            $minor: String!,
            $patch: String!,
            $candidate: String,
            $notes: String
        ) {
            createStrandVersion(
                strandUuid: $strand,
                jsonSchema: $json_schema,
                major: $major,
                minor: $minor,
                patch: $patch,
                candidate: $candidate,
                notes: $notes
            ) {
                ... on StrandVersion {
                     uuid
                 }
                ... on OperationInfo {
                    messages {
                        kind
                        message
                        field
                        code
                    }
                }
            }
        }
    """
    )

    logger.info("Creating strand version %r.", version)
    response = client.execute(query, variable_values=parameters)["createStrandVersion"]

    if "messages" in response:
        raise StrandsException(response["messages"])

    logger.info("Finished creating strand version.")
    return response["uuid"]
