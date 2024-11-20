import gql
from gql.transport.requests import RequestsHTTPTransport

STRANDS_API_URL = "https://api.octue.com/graphql/"


transport = RequestsHTTPTransport(url=STRANDS_API_URL)
client = gql.Client(transport=transport, fetch_schema_from_transport=True)


def publish_strand_version():
    pass


def _create_strand():
    pass


def _create_strand_version(strand, json_schema, major, minor, patch, candidate=None, notes=None):
    """Create a strand version for an existing strand.

    :param str strand: the UUID of the strand to create a new version for
    :param str json_schema: the JSON schema for the strand version as a JSON-encoded string
    :param str major: the major version for the strand version
    :param str minor: the minor version for the strand version
    :param str patch: the patch version for the strand version
    :param str|None candidate: the candidate version for the strand version if there is one
    :param str|None notes: any notes to associate with the strand version
    :return dict: either a successful response containing the strand version's UUID or an error response
    """
    parameters = {
        "strand": strand,
        "json_schema": json_schema,
        "major": major,
        "minor": minor,
        "patch": patch,
        "candidate": candidate,
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

    result = client.execute(query, variable_values=parameters)["createStrandVersion"]

    if "messages" in result:
        raise Exception(result["messages"])

    return result
