import json
import logging
import os

import gql
from gql.transport.requests import RequestsHTTPTransport
import semver

from publish_strand_version.exceptions import StrandsException

STRANDS_API_URL = os.environ.get("STRANDS_API_URL", "https://api.octue.com/graphql/")
STRANDS_FRONTEND_URL = os.environ.get("STRANDS_FRONTEND_URL", "https://strands.octue.com")
STRANDS_SCHEMA_REGISTRY_URL = os.environ.get("STRANDS_SCHEMA_REGISTRY_URL", "https://jsonschema.registry.octue.com")

logger = logging.getLogger(__name__)
transport = RequestsHTTPTransport(url=STRANDS_API_URL)
client = gql.Client(transport=transport, fetch_schema_from_transport=True)


def publish_strand_version(token, account, name, json_schema, version=None, notes=None):
    """Publish a strand version for an existing strand.

    :param str token: a Strands access token with permission to add a new strand version to a specific strand
    :param str account: the handle of the account the strand belongs to
    :param str name: the name of the strand
    :param dict json_schema: the JSON schema to add to the strand as a strand version
    :param str version: the semantic version to give the strand version
    :param str notes: any notes to associate with the strand version
    :return (str, str, str):
    """
    suid = f"{account}/{name}"

    if not version:
        version = _suggest_sem_ver(token=token, base=suid, proposed=json.dumps(json_schema))

    strand_version_uuid = _create_strand_version(
        token=token,
        account=account,
        name=name,
        json_schema=json_schema,
        version=version,
        notes=notes,
    )

    strand_url = "/".join((STRANDS_FRONTEND_URL, suid))
    strand_version_url = "/".join((STRANDS_SCHEMA_REGISTRY_URL, suid, f"{version}.json"))
    return strand_url, strand_version_url, strand_version_uuid


def _suggest_sem_ver(token, base, proposed):
    """Query the GraphQL endpoint for a suggested semantic version for the proposed schema relative to a base schema.

    :param str token: a Strands access token with any scope
    :param str base: the base schema as a strand unique identifier (SUID) of an existing strand
    :param str proposed: the proposed schema as a JSON-encoded string
    :raises publish_strand_version.exceptions.StrandsException: if the query fails for any reason
    :return str: the suggested semantic version for the proposed schema
    """
    parameters = {"token": token, "base": base, "proposed": proposed}

    query = gql.gql(
        """
        mutation suggestSemVerViaToken(
            $token: String!,
            $base: String!,
            $proposed: String!,
        ){
            suggestSemVerViaToken(token: $token, base: $base, proposed: $proposed) {
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
    response = client.execute(query, variable_values=parameters)["suggestSemVerViaToken"]

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


def _create_strand_version(token, account, name, json_schema, version, notes=None):
    """Send a mutation to the GraphQL endpoint that creates a strand version for an existing strand.

    :param str token: a Strands access token with permission to add a new strand version to a specific strand
    :param str account: the handle of the account the strand belongs to
    :param str name: the name of the strand
    :param dict json_schema: the JSON schema for the strand version as a JSON-encoded string
    :param str version: the semantic version for the strand version
    :param str|None notes: any notes to associate with the strand version
    :return dict: either a successful response containing the strand version's UUID or an error response
    """
    semantic_version = semver.Version.parse(version)

    parameters = {
        "token": token,
        "account": account,
        "name": name,
        "json_schema": json_schema,
        "major": str(semantic_version.major),
        "minor": str(semantic_version.minor),
        "patch": str(semantic_version.patch),
        "candidate": semantic_version.prerelease,
        "notes": notes,
    }

    query = gql.gql(
        """
        mutation createStrandVersionViaToken(
            $token: String!,
            $account: String!,
            $name: String!,
            $json_schema: JSON!,
            $major: String!,
            $minor: String!,
            $patch: String!,
            $candidate: String,
            $notes: String
        ) {
            createStrandVersionViaToken(
                token: $token,
                account: $account,
                name: $name,
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

    svuid = f"{account}/{name}:{version}"
    logger.info("Creating strand version %r...", svuid)
    response = client.execute(query, variable_values=parameters)["createStrandVersionViaToken"]

    if "messages" in response:
        raise StrandsException(response["messages"])

    logger.info("Finished creating strand version.")
    return response["uuid"]
