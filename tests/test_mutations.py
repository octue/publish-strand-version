import unittest
from unittest.mock import patch

from publish_strand_version.exceptions import StrandsException
from publish_strand_version.mutations import _create_strand, _create_strand_version, _get_strand, publish_strand_version


class TestPublishStrandVersion(unittest.TestCase):
    def test_with_non_existent_strand(self):
        """Test publishing a strand version for a non-existent strand."""
        strand_uuid = "14aca8b2-fb34-4587-a7ba-290585265d32"
        strand_version_uuid = "e75dd480-4bfa-4ae9-b5c0-853e9a114194"

        with patch(
            "gql.Client.execute",
            side_effect=[
                {"strand": None},
                {"createStrand": {"uuid": strand_uuid}},
                {"createStrandVersion": {"uuid": strand_version_uuid}},
            ],
        ):
            response = publish_strand_version(
                account="some",
                name="strand",
                json_schema={"some": "schema"},
                version="1.0.0",
            )

        self.assertEqual(response, strand_version_uuid)

    def test_with_existing_strand(self):
        """Test publishing a strand version for an existing strand."""
        strand_uuid = "14aca8b2-fb34-4587-a7ba-290585265d32"
        strand_version_uuid = "e75dd480-4bfa-4ae9-b5c0-853e9a114194"

        with patch(
            "gql.Client.execute",
            side_effect=[
                {"strand": {"uuid": strand_uuid}},
                {"createStrandVersion": {"uuid": strand_version_uuid}},
            ],
        ):
            with patch("publish_strand_version.mutations._create_strand") as mock_create_strand:
                response = publish_strand_version(
                    account="some",
                    name="strand",
                    json_schema={"some": "schema"},
                    version="1.0.0",
                )

        mock_create_strand.assert_not_called()
        self.assertEqual(response, strand_version_uuid)


class TestGetStrand(unittest.TestCase):
    def test_none_returned_for_non_existent_strand(self):
        """Test that `None` is returned if trying to get a non-existent strand."""
        with patch("gql.Client.execute", return_value={"strand": None}):
            response = _get_strand(account="some", name="strand")

        self.assertIsNone(response)

    def test_strand_uuid_returned_for_existing_strand(self):
        """Test that the strand's UUID is returned if the strand exists."""
        strand_uuid = "14aca8b2-fb34-4587-a7ba-290585265d32"

        with patch("gql.Client.execute", return_value={"strand": {"uuid": strand_uuid}}):
            response = _get_strand(account="some", name="strand")

        self.assertEqual(response, strand_uuid)


class TestCreateStrand(unittest.TestCase):
    def test_error_raised_if_unauthenticated(self):
        """Test that an error is raised if trying to create a strand without authentication."""
        with patch(
            "gql.Client.execute",
            return_value={"createStrand": {"messages": [{"message": "User is not authenticated."}]}},
        ):
            with self.assertRaises(StrandsException) as error_context:
                _create_strand(account="some", name="strand")

        self.assertEqual(error_context.exception.args[0][0]["message"], "User is not authenticated.")

    def test_creating_strand(self):
        """Test creating a strand successfully."""
        strand_uuid = "14aca8b2-fb34-4587-a7ba-290585265d32"

        with patch("gql.Client.execute", return_value={"createStrand": {"uuid": strand_uuid}}) as mock_execute:
            response = _create_strand(account="some", name="strand")

        self.assertEqual(response, strand_uuid)
        self.assertEqual(mock_execute.mock_calls[0].kwargs["variable_values"], {"account": "some", "name": "strand"})


class TestCreateStrandVersion(unittest.TestCase):
    def test_error_raised_if_unauthenticated(self):
        """Test that an error is raised if trying to create a strand version without authentication."""
        with patch(
            "gql.Client.execute",
            return_value={"createStrandVersion": {"messages": [{"message": "User is not authenticated."}]}},
        ):
            with self.assertRaises(StrandsException) as error_context:
                _create_strand_version(strand="some-uuid", json_schema={}, version="0.1.0")

        self.assertEqual(error_context.exception.args[0][0]["message"], "User is not authenticated.")

    def test_with_existing_strand(self):
        """Test creating a strand version for an existing strand."""
        strand_version_uuid = "14aca8b2-fb34-4587-a7ba-290585265d32"

        with patch(
            "gql.Client.execute",
            return_value={"createStrandVersion": {"uuid": strand_version_uuid}},
        ) as mock_execute:
            response = _create_strand_version(strand="some-uuid", json_schema={"some": "schema"}, version="0.1.0-rc.1")

        self.assertEqual(response, strand_version_uuid)

        self.assertEqual(
            mock_execute.mock_calls[0].kwargs["variable_values"],
            {
                "strand": "some-uuid",
                "json_schema": '"{\\"some\\": \\"schema\\"}"',
                "major": 0,
                "minor": 1,
                "patch": 0,
                "candidate": "rc.1",
                "notes": None,
            },
        )
