import json
import unittest
from unittest.mock import patch

from publish_strand_version.api import _create_strand_version, _suggest_sem_ver, publish_strand_version
from publish_strand_version.exceptions import StrandsException


class TestPublishStrandVersion(unittest.TestCase):
    def test_with_existing_strand(self):
        """Test publishing a strand version for an existing strand."""
        expected_strand_version_uuid = "e75dd480-4bfa-4ae9-b5c0-853e9a114194"

        with patch(
            "gql.Client.execute",
            side_effect=[{"createStrandVersionViaToken": {"uuid": expected_strand_version_uuid}}],
        ):
            strand_url, strand_version_uri, strand_version_uuid = publish_strand_version(
                token="some-token",
                account="some",
                name="strand",
                json_schema={"some": "schema"},
                version="1.0.0",
            )

        self.assertEqual(strand_url, "https://strands.octue.com/some/strand")
        self.assertEqual(strand_version_uri, "https://jsonschema.registry.octue.com/some/strand/1.0.0.json")
        self.assertEqual(strand_version_uuid, expected_strand_version_uuid)


class TestSuggestSemVer(unittest.TestCase):
    def test_error_raised_if_unauthenticated(self):
        """Test that an error is raised if trying to get a semantic version suggestion without authentication."""
        with patch(
            "gql.Client.execute",
            return_value={"suggestSemVer": {"messages": [{"message": "User is not authenticated."}]}},
        ):
            with self.assertRaises(StrandsException) as error_context:
                _suggest_sem_ver(base="some/strand", proposed=json.dumps(json.dumps({"some": "schema"})))

        self.assertEqual(error_context.exception.args[0][0]["message"], "User is not authenticated.")

    def test_suggesting_sem_ver(self):
        mock_response = {
            "suggestSemVer": {"suggestedVersion": "0.2.0", "isBreaking": False, "isFeature": True, "isPatch": False}
        }

        json_schema_encoded = json.dumps(json.dumps({"some": "schema"}))

        with patch("gql.Client.execute", return_value=mock_response) as mock_execute:
            response = _suggest_sem_ver(base="some/strand", proposed=json_schema_encoded)

        self.assertEqual(response, "0.2.0")

        self.assertEqual(
            mock_execute.mock_calls[0].kwargs["variable_values"],
            {"base": "some/strand", "proposed": json_schema_encoded},
        )


class TestCreateStrandVersion(unittest.TestCase):
    def test_error_raised_if_unauthenticated(self):
        """Test that an error is raised if trying to create a strand version without authentication."""
        with patch(
            "gql.Client.execute",
            return_value={"createStrandVersionViaToken": {"messages": [{"message": "User is not authenticated."}]}},
        ):
            with self.assertRaises(StrandsException) as error_context:
                _create_strand_version(token="some-token", json_schema='"{}"', version="0.1.0")

        self.assertEqual(error_context.exception.args[0][0]["message"], "User is not authenticated.")

    def test_with_existing_strand(self):
        """Test creating a strand version for an existing strand."""
        strand_version_uuid = "14aca8b2-fb34-4587-a7ba-290585265d32"

        with patch(
            "gql.Client.execute",
            return_value={"createStrandVersionViaToken": {"uuid": strand_version_uuid}},
        ) as mock_execute:
            response = _create_strand_version(
                token="some-token",
                json_schema='"{\\"some\\": \\"schema\\"}"',
                version="0.1.0-rc.1",
            )

        self.assertEqual(response, strand_version_uuid)

        self.assertEqual(
            mock_execute.mock_calls[0].kwargs["variable_values"],
            {
                "token": "some-token",
                "json_schema": '"{\\"some\\": \\"schema\\"}"',
                "major": "0",
                "minor": "1",
                "patch": "0",
                "candidate": "rc.1",
                "notes": None,
            },
        )
