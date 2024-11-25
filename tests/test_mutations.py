import unittest
from unittest.mock import patch

from publish_strand_version.exceptions import StrandsException
from publish_strand_version.mutations import _create_strand, _create_strand_version


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
                _create_strand_version(
                    strand="some-uuid",
                    json_schema={},
                    major="0",
                    minor="1",
                    patch="0",
                )

        self.assertEqual(error_context.exception.args[0][0]["message"], "User is not authenticated.")

    def test_with_existing_strand(self):
        """Test creating a strand version for an existing strand."""
        strand_version_uuid = "14aca8b2-fb34-4587-a7ba-290585265d32"

        with patch(
            "gql.Client.execute",
            return_value={"createStrandVersion": {"uuid": strand_version_uuid}},
        ) as mock_execute:
            response = _create_strand_version(
                strand="some-uuid",
                json_schema={"some": "schema"},
                major="0",
                minor="1",
                patch="0",
            )

        self.assertEqual(response, strand_version_uuid)

        self.assertEqual(
            mock_execute.mock_calls[0].kwargs["variable_values"],
            {
                "strand": "some-uuid",
                "json_schema": '"{\\"some\\": \\"schema\\"}"',
                "major": "0",
                "minor": "1",
                "patch": "0",
                "candidate": None,
                "notes": None,
            },
        )
