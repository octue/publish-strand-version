import json
import unittest
from unittest.mock import patch

from publish_strand_version.api import _create_strand_version, _suggest_sem_ver, publish_strand_version
from publish_strand_version.exceptions import StrandsException


class TestPublishStrandVersion(unittest.TestCase):
    def test_error_raised_if_version_manually_set_in_suggest_only_mode(self):
        """Test that an error is raised if the `version` argument is set when `suggest_only=True`."""
        with self.assertRaises(ValueError) as error_context:
            publish_strand_version(
                token="some-token",
                account="some",
                name="strand",
                json_schema={"some": "schema"},
                version="1.0.0",
                suggest_only=True,
            )

        self.assertEqual(
            error_context.exception.args[0],
            "The `version` argument cannot be set while `suggest_only=True`.",
        )

    def test_suggest_only_mode(self):
        """Test that the strand version creation mutation is not used when suggest-only mode is enabled."""
        mock_response = {"suggestSemVerViaToken": {"suggestedVersion": "0.2.0", "changeType": "minor"}}

        with patch("publish_strand_version.api._create_strand_version") as mock_create_strand_version:
            with patch("gql.Client.execute", return_value=mock_response):
                strand_url, strand_version_url, strand_version_uuid, version = publish_strand_version(
                    token="some-token",
                    account="some",
                    name="strand",
                    json_schema={"some": "schema"},
                    suggest_only=True,
                )

        mock_create_strand_version.assert_not_called()
        self.assertEqual(version, "0.2.0")
        self.assertIsNone(strand_url)
        self.assertIsNone(strand_version_url)
        self.assertIsNone(strand_version_uuid)

    def test_publish_mode(self):
        """Test publishing a strand version."""
        expected_strand_version_uuid = "e75dd480-4bfa-4ae9-b5c0-853e9a114194"

        with patch(
            "gql.Client.execute",
            side_effect=[{"createStrandVersionViaToken": {"uuid": expected_strand_version_uuid}}],
        ):
            strand_url, strand_version_url, strand_version_uuid, version = publish_strand_version(
                token="some-token",
                account="some",
                name="strand",
                json_schema={"some": "schema"},
                version="1.0.0",
            )

        self.assertEqual(strand_url, "https://strands.octue.com/some/strand")
        self.assertEqual(strand_version_url, "https://jsonschema.registry.octue.com/some/strand/1.0.0.json")
        self.assertEqual(strand_version_uuid, expected_strand_version_uuid)
        self.assertEqual(version, "1.0.0")

    def test_publishing_skipped_if_schema_not_changed(self):
        """Test that publishing is skipped if the schema hasn't changed."""
        mock_response = {"suggestSemVerViaToken": {"suggestedVersion": "0.2.0", "changeType": "equal"}}

        with patch("publish_strand_version.api._create_strand_version") as mock_create_strand_version:
            with patch("gql.Client.execute", return_value=mock_response):
                strand_url, strand_version_url, strand_version_uuid, version = publish_strand_version(
                    token="some-token",
                    account="some",
                    name="strand",
                    json_schema={"some": "schema"},
                )

        mock_create_strand_version.assert_not_called()
        self.assertEqual(version, "0.2.0")
        self.assertIsNone(strand_url)
        self.assertIsNone(strand_version_url)
        self.assertIsNone(strand_version_uuid)


class TestSuggestSemVer(unittest.TestCase):
    def test_error_raised_if_unauthenticated(self):
        """Test that an error is raised if trying to get a semantic version suggestion without authentication."""
        with patch(
            "gql.Client.execute",
            return_value={"suggestSemVerViaToken": {"messages": [{"message": "User is not authenticated."}]}},
        ):
            with self.assertRaises(StrandsException) as error_context:
                _suggest_sem_ver(
                    token="some-token",
                    base="some/strand",
                    proposed=json.dumps({"some": "schema"}),
                    allow_beta=True,
                )

        self.assertEqual(error_context.exception.args[0][0]["message"], "User is not authenticated.")

    def test_suggesting_sem_ver(self):
        mock_response = {"suggestSemVerViaToken": {"suggestedVersion": "0.2.0", "changeType": "minor"}}
        json_schema_encoded = json.dumps({"some": "schema"})

        with patch("gql.Client.execute", return_value=mock_response) as mock_execute:
            response = _suggest_sem_ver(
                token="some-token",
                base="some/strand",
                proposed=json_schema_encoded,
                allow_beta=True,
            )

        self.assertEqual(response, ("0.2.0", True))

        self.assertEqual(
            mock_execute.mock_calls[0].kwargs["variable_values"],
            {"token": "some-token", "base": "some/strand", "proposed": json_schema_encoded, "allowBeta": True},
        )


class TestCreateStrandVersion(unittest.TestCase):
    def test_error_raised_if_unauthenticated(self):
        """Test that an error is raised if trying to create a strand version without authentication."""
        with patch(
            "gql.Client.execute",
            return_value={"createStrandVersionViaToken": {"messages": [{"message": "User is not authenticated."}]}},
        ):
            with self.assertRaises(StrandsException) as error_context:
                _create_strand_version(
                    token="some-token",
                    account="some-user",
                    name="some-strand",
                    json_schema={},
                    version="0.1.0",
                )

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
                account="some-user",
                name="some-strand",
                json_schema={"some": "schema"},
                version="0.1.0",
            )

        self.assertEqual(response, strand_version_uuid)

        self.assertEqual(
            mock_execute.mock_calls[0].kwargs["variable_values"],
            {
                "token": "some-token",
                "account": "some-user",
                "name": "some-strand",
                "json_schema": {"some": "schema"},
                "major": 0,
                "minor": 1,
                "patch": 0,
                "candidate": None,
                "notes": None,
            },
        )

    def test_with_existing_strand_with_candidate_version(self):
        """Test creating a strand version with a candidate semantic version for an existing strand."""
        strand_version_uuid = "14aca8b2-fb34-4587-a7ba-290585265d32"

        with patch(
            "gql.Client.execute",
            return_value={"createStrandVersionViaToken": {"uuid": strand_version_uuid}},
        ) as mock_execute:
            response = _create_strand_version(
                token="some-token",
                account="some-user",
                name="some-strand",
                json_schema={"some": "schema"},
                version="0.1.0-rc.1",
            )

        self.assertEqual(response, strand_version_uuid)

        self.assertEqual(
            mock_execute.mock_calls[0].kwargs["variable_values"],
            {
                "token": "some-token",
                "account": "some-user",
                "name": "some-strand",
                "json_schema": {"some": "schema"},
                "major": 0,
                "minor": 1,
                "patch": 0,
                "candidate": "rc.1",
                "notes": None,
            },
        )
