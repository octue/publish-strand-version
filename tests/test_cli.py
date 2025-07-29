import os
import unittest
from unittest.mock import mock_open, patch

from publish_strand_version import cli
from publish_strand_version.exceptions import StrandsException


class TestCLI(unittest.TestCase):
    def test_with_failed_publishing(self):
        """Test that the exit code is 1 if publishing fails."""
        with patch("builtins.open", mock_open(read_data="{}")):
            with patch(
                "publish_strand_version.cli.publish_strand_version",
                side_effect=StrandsException("Error raised for testing!"),
            ):
                with patch("sys.stderr") as mock_stderr:
                    with self.assertLogs() as logging_context:
                        with self.assertRaises(SystemExit) as e:
                            cli.main(
                                [
                                    "token",
                                    "some",
                                    "strand",
                                    "non-existent-path.json",
                                    "1.0.0",
                                ]
                            )

        self.assertEqual(e.exception.code, 1)
        self.assertIn("Error raised for testing!", logging_context.output[0])

        message = mock_stderr.method_calls[0].args[0]
        self.assertIn("STRAND VERSION PUBLISHING FAILED.", message)

    def test_with_skipped_publishing(self):
        """Test the output when publishing is skipped."""

        with patch("builtins.open", mock_open(read_data='{"some": "schema"}')):
            with patch(
                "publish_strand_version.cli.publish_strand_version",
                return_value=(None, None, None, "1.0.0", False),
            ):
                with patch.dict(os.environ, {"GITHUB_OUTPUT": "/dev/null"}):
                    with patch("sys.stdout") as mock_stdout:
                        with self.assertRaises(SystemExit) as e:
                            cli.main(
                                [
                                    "some-token",
                                    "some",
                                    "strand",
                                    "non-existent-path.json",
                                ]
                            )

        self.assertEqual(e.exception.code, 0)
        self.assertIn("STRAND VERSION PUBLISHING SKIPPED", mock_stdout.method_calls[0].args[0])

    def test_with_successful_publishing(self):
        """Test that the exit code is 0 if publishing succeeds and that the mutation is called with the correct
        arguments.
        """
        strand_version_uuid = "14aca8b2-fb34-4587-a7ba-290585265d32"
        strand_url = "strand-url"
        strand_version_url = "strand-version-url"

        mock_publish_strand_version = patch(
            "publish_strand_version.cli.publish_strand_version",
            return_value=(strand_url, strand_version_url, strand_version_uuid, "1.0.0-rc.1", True),
        )

        with patch("builtins.open", mock_open(read_data='{"some": "schema"}')):
            with mock_publish_strand_version as mock_publish_strand_version:
                with patch.dict(os.environ, {"GITHUB_OUTPUT": "/dev/null"}):
                    with patch("sys.stdout") as mock_stdout:
                        with self.assertRaises(SystemExit) as e:
                            cli.main(
                                [
                                    "some-token",
                                    "some",
                                    "strand",
                                    "non-existent-path.json",
                                    "1.0.0-rc.1",
                                    "Some notes.",
                                ]
                            )

        mock_publish_strand_version.assert_called_with(
            token="some-token",
            account="some",
            name="strand",
            json_schema={"some": "schema"},
            version="1.0.0-rc.1",
            notes="Some notes.",
            allow_beta=True,
            suggest_only=False,
        )

        self.assertEqual(e.exception.code, 0)

        message = mock_stdout.method_calls[0].args[0]
        self.assertIn("STRAND VERSION PUBLISHING SUCCEEDED", message)
        self.assertIn(strand_url, message)
        self.assertIn(strand_version_url, message)
        self.assertIn(strand_version_uuid, message)

    def test_with_successful_suggestion(self):
        """Test the output for a successful version suggestion."""
        strand_version_uuid = "14aca8b2-fb34-4587-a7ba-290585265d32"
        strand_url = "strand-url"
        strand_version_url = "strand-version-url"

        mock_publish_strand_version = patch(
            "publish_strand_version.cli.publish_strand_version",
            return_value=(strand_url, strand_version_url, strand_version_uuid, "1.0.0-rc.1", False),
        )

        with patch("builtins.open", mock_open(read_data='{"some": "schema"}')):
            with mock_publish_strand_version as mock_publish_strand_version:
                with patch.dict(os.environ, {"GITHUB_OUTPUT": "/dev/null"}):
                    with patch("sys.stdout") as mock_stdout:
                        with self.assertRaises(SystemExit) as e:
                            cli.main(
                                [
                                    "some-token",
                                    "some",
                                    "strand",
                                    "non-existent-path.json",
                                    "1.0.0-rc.1",
                                    "Some notes.",
                                    "true",
                                    "true",
                                ]
                            )

        mock_publish_strand_version.assert_called_with(
            token="some-token",
            account="some",
            name="strand",
            json_schema={"some": "schema"},
            version="1.0.0-rc.1",
            notes="Some notes.",
            allow_beta=True,
            suggest_only=True,
        )

        self.assertEqual(e.exception.code, 0)

        message = mock_stdout.method_calls[0].args[0]
        self.assertIn("STRAND VERSION SUGGESTION SUCCEEDED", message)
        self.assertIn(strand_url, message)
        self.assertIn(strand_version_url, message)
        self.assertIn(strand_version_uuid, message)
