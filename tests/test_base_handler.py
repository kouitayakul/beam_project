import os
import threading
import unittest
from unittest.mock import patch
from downloader.protocols.base_handler import BaseHandler


class TestBaseHandler(unittest.TestCase):
    def setUp(self):
        self.handler = BaseHandler("test_logger", threading.Event())
        self.test_path = "/fake/dir"
        self.test_file = "/fake/dir/dummyFile.pdf"
        self.handler.downloaded_files = {}

    @patch("os.makedirs")
    def test_ensure_directory_success(self, mock_makedirs):
        mock_makedirs.return_value = None

        result = self.handler._ensure_directory(self.test_path)

        self.assertTrue(result)
        mock_makedirs.assert_called_once_with(self.test_path, exist_ok=True)

    @patch("logging.Logger.error")
    @patch("os.makedirs", side_effect=OSError("Error creating directory"))
    def test_ensure_directory_failure(self, mock_makedirs, mock_error):
        result = self.handler._ensure_directory(self.test_path)

        mock_makedirs.assert_called_once_with(self.test_path, exist_ok=True)
        self.assertFalse(result)
        mock_error.assert_called_once_with(
            f"Failed to create directory {self.test_path}: Error creating directory"
        )

    @patch("logging.Logger.info")
    @patch("os.remove")
    def test_cleanup_file_exists(self, mock_remove, mock_info):
        mock_remove.return_value = None

        self.handler._cleanup_file(self.test_file)

        mock_remove.assert_called_once_with(self.test_file)
        mock_info.assert_called_with(f"Removed partial download {self.test_file}")

    @patch("logging.Logger.warning")
    @patch("os.remove", side_effect=FileNotFoundError)
    def test_cleanup_file_not_exists(self, mock_remove, mock_warning):
        self.handler._cleanup_file(self.test_file)

        mock_remove.assert_called_once_with(self.test_file)
        mock_warning.assert_called_with(f"No file to remove at {self.test_file}")

    @patch("logging.Logger.error")
    @patch("os.remove", side_effect=OSError("Error removing file"))
    def test_cleanup_file_failure(self, mock_remove, mock_error):
        self.handler._cleanup_file(self.test_file)

        mock_remove.assert_called_once_with(self.test_file)
        mock_error.assert_called_with(
            f"Failed to remove partial download {self.test_file}: Error removing file"
        )

    def test_parse_ftp_uri(self):
        test_uri = "ftp://username:password@hostname:21/path/to/dummyFile.pdf"
        expected_result = (
            "hostname",
            21,
            "username",
            "password",
            "/path/to/dummyFile.pdf",
        )

        result = self.handler._parse_uri(test_uri, 21)

        self.assertEqual(result, expected_result)

    def test_parse_ftp_uri_with_defaults(self):
        test_uri = "ftp://hostname/path/to/dummyFile.pdf"
        expected_result = (
            "hostname",
            21,
            "anonymous",
            "anonymous",
            "/path/to/dummyFile.pdf",
        )

        result = self.handler._parse_uri(test_uri, 21)

        self.assertEqual(result, expected_result)

    @patch("downloader.protocols.base_handler.BaseHandler._cleanup_file")
    @patch("logging.Logger.debug")
    @patch("logging.Logger.error")
    def test_handle_error_last_attempt(self, mock_error, mock_debug, mock_cleanup):
        filename = "dummyFile.pdf"
        filepath = "/fake/dir/dummyFile.pdf"
        error = Exception("Download error")

        with self.assertRaises(Exception) as context:
            self.handler._handle_error(error, 3, 3, filename, filepath)

        self.assertTrue("Download error" in str(context.exception))
        mock_debug.assert_called_with(
            f"(Attempt 3 of 3) - Error downloading file {filename}: Download error"
        )
        mock_error.assert_called_with(
            f"Failed to download '{filename}' after 3 attempts: Download error"
        )
        mock_cleanup.assert_called_once_with(filepath)

    @patch("downloader.protocols.base_handler.BaseHandler._cleanup_file")
    @patch("logging.Logger.debug")
    @patch("logging.Logger.error")
    def test_handle_error_not_last_attempt(self, mock_error, mock_debug, mock_cleanup):
        filename = "dummyFile.pdf"
        filepath = "/fake/dir/dummyFile.pdf"
        error = Exception("Download error")

        self.handler._handle_error(error, 1, 3, filename, filepath)

        mock_debug.assert_called_once_with(
            f"(Attempt 1 of 3) - Error downloading file {filename}: Download error"
        )
        mock_error.assert_not_called()
        mock_cleanup.assert_not_called()

    def test_existing_key_in_downloaded_files(self):
        filepath = "/fake/dir/dummyFile.pdf"
        self.handler.downloaded_files["uri|dest_dir"] = filepath

        result = self.handler._get_local_filepath("uri", "dest_dir")

        self.assertEqual(result, filepath)

    @patch("os.path.exists")
    def test_filepath_does_not_exist_yet(self, mock_exists):
        mock_exists.return_value = False
        expected = os.path.join("dest_dir", "uri")

        result = self.handler._get_local_filepath("uri", "dest_dir")

        self.assertEqual(result, expected)

    @patch("os.path.exists", side_effect=[True, True, False])
    def test_filepath_already_exist(self, mock_exists):
        result = self.handler._get_local_filepath(
            "http://example.com/dummyFile.pdf", "dest_dir"
        )

        self.assertEqual(result, "dest_dir/dummyFile_2.pdf")


if __name__ == "__main__":
    unittest.main()
