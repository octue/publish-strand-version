import json
import logging
import os

import gql
from gql.transport.requests import RequestsHTTPTransport
import semver

from publish_strand_version.exceptions import StrandsException

STRANDS_API_URL = os.environ.get("STRANDS_API_URL", "http://api.octue.com/graphql")
STRANDS_FRONTEND_URL = os.environ.get("STRANDS_FRONTEND_URL", "https://strands.octue.com")
STRANDS_SCHEMA_REGISTRY_URL = os.environ.get("STRANDS_SCHEMA_REGISTRY_URL", "https://jsonschema.registry.octue.com")

logger = logging.getLogger(__name__)
transport = RequestsHTTPTransport(url=STRANDS_API_URL)
client = gql.Client(transport=transport, fetch_schema_from_transport=True)


def publish_strand_version(account, name, json_schema, version=None, notes=None):
    """Publish a strand version for a new or existing strand.

    :param str account: the handle of the account the strand belongs to
    :param str name: the name of the strand
    :param dict json_schema: the JSON schema to add to the strand as a strand version
    :param str version: the semantic version to give the strand version
    :param str notes: any notes to associate with the strand version
    :return (str, str, str):
    """
    strand = _get_strand(account, name)

    if not strand:
        strand = _create_strand(account, name)

    suid = f"{account}/{name}"
    json_schema_encoded = json.dumps(json.dumps(json_schema))

    if not version:
        version = _suggest_sem_ver(base=suid, proposed=json_schema_encoded)

    strand_version_uuid = _create_strand_version(
        strand=strand,
        json_schema=json_schema_encoded,
        version=version,
        notes=notes,
    )

    strand_url = "/".join((STRANDS_FRONTEND_URL, suid))
    strand_version_uri = "/".join((STRANDS_SCHEMA_REGISTRY_URL, suid, f"{version}.json"))
    return strand_url, strand_version_uri, strand_version_uuid


def _get_strand(account, name):
    """Query the GraphQL endpoint for a strand.

    :param str account: the handle of the account the strand belongs to
    :param str name: the name of the strand
    :return str|None: the strand's UUID if the strand exists; `None` if it doesn't exist
    """
    parameters = {"account": account, "name": name}
    suid = f"{account}/{name}"

    query = gql.gql(
        """
        query getStrand(
            $account: String!,
            $name: String!,
        ){
            strandByName(account: $account, name: $name) {
                ... on Strand {
                    uuid
                }
                ... on DoesNotExist {
                    message
                }
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
    return None


def _create_strand(account, name):
    """Send a mutation to the GraphQL endpoint that creates a strand.

    :param str account: the handle of an existing account to create the strand in
    :param str name: the name to give the strand
    :raises publish_strand_version.exceptions.StrandsException: if the mutation fails for any reason
    :return str: the UUID of the created strand
    """
    parameters = {"account": account, "name": name}

    query = gql.gql(
        """
        mutation createStrand(
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


def _suggest_sem_ver(base, proposed):
    """Query the GraphQL endpoint for a suggested semantic version for the proposed schema relative to a base schema.

    :param str base: the base schema as a strand unique identifier (SUID) of an existing strand
    :param str proposed: the proposed schema as double-JSON-encoded string
    :raises publish_strand_version.exceptions.StrandsException: if the query fails for any reason
    :return str: the suggested semantic version for the proposed schema
    """
    parameters = {"base": base, "proposed": proposed}

    query = gql.gql(
        """
        mutation suggestSemVer(
            $base: String!,
            $proposed: String!,
        ){
            suggestSemVer(base: $base, proposed: $proposed) {
                ... on VersionSuggestion {
                    suggestedVersion
                    isBreaking
                    isFeature
                    isPatch
                }
                ... on VersionSuggestionError {
                    type
                    message
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

    logger.info("Getting suggested semantic version...")
    response = client.execute(query, variable_values=parameters)["suggestSemVer"]

    if "messages" in response or "message" in response:
        raise StrandsException(response.get("messages") or response.get("message"))

    if response["isBreaking"]:
        change_type = "breaking change"
    elif response["isFeature"]:
        change_type = "new feature"
    else:
        change_type = "patch change"

    logger.info(
        "The suggested semantic version is %s. This represents a %s.",
        response["suggestedVersion"],
        change_type,
    )

    return response["suggestedVersion"]


def _create_strand_version(strand, json_schema, version, notes=None):
    """Send a mutation to the GraphQL endpoint that creates a strand version for an existing strand.

    :param str strand: the UUID of the strand to create a new version for
    :param str json_schema: the JSON schema for the strand version as a double-JSON-encoded string
    :param str version: the semantic version for the strand version
    :param str|None notes: any notes to associate with the strand version
    :return dict: either a successful response containing the strand version's UUID or an error response
    """
    semantic_version = semver.Version.parse(version)

    parameters = {
        "strand": strand,
        "json_schema": json_schema,
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
