import os
import unittest
import unittest.mock
import requests
import threading
from unittest.mock import ANY, MagicMock, call, patch
from downloader.protocols.http_handler import HTTPHandler


class TestHTTPHandler(unittest.TestCase):
    def setUp(self):
        self.uri = "https://example.com/dummyFile.pdf"
        self.dest_dir = "/fake/dir"
        self.filename = "dummyFile.pdf"
        self.local_filepath = os.path.join(self.dest_dir, self.filename)
        self.stop_event = threading.Event()
        self.handler = HTTPHandler(self.stop_event)

    @patch("logging.Logger.info")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch("os.makedirs")
    @patch("requests.get")
    def test_successful_download(self, mock_get, mock_makedirs, mock_open, mock_info):
        # Mock the response from requests.get
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.iter_content = MagicMock(return_value=[b"data"])
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        self.handler.download_file(self.uri, self.dest_dir, 1)

        mock_makedirs.assert_called_once_with(self.dest_dir, exist_ok=True)
        mock_get.assert_called_once_with(
            self.uri, headers=ANY, stream=True, timeout=ANY
        )
        mock_open.assert_any_call(self.local_filepath, "wb")
        mock_open().write.assert_any_call(b"data")
        mock_info.assert_called_once_with(
            f"Successfully downloaded '{self.filename}' to '{self.dest_dir}'"
        )

    @patch("logging.Logger.debug")
    @patch("logging.Logger.warning")
    @patch("logging.Logger.error")
    @patch("os.makedirs")
    @patch("requests.get", side_effect=requests.RequestException("Error Not Found"))
    def test_download_failure_and_retries(
        self, mock_get, mock_makedirs, mock_error, mock_warning, mock_debug
    ):
        retries = 2

        with self.assertRaises(requests.RequestException):
            self.handler.download_file(self.uri, self.dest_dir, retries)

        mock_makedirs.assert_called_once_with(self.dest_dir, exist_ok=True)
        self.assertEqual(mock_get.call_count, retries)
        mock_debug.assert_has_calls(
            [
                call(
                    f"(Attempt 1 of 2) - Error downloading file {self.filename}: Error Not Found"
                ),
                call(
                    f"(Attempt 2 of 2) - Error downloading file {self.filename}: Error Not Found"
                ),
            ],
            any_order=False,
        )
        mock_error.assert_called_once_with(
            f"Failed to download '{self.filename}' after {retries} attempts: Error Not Found"
        )
        mock_warning.assert_called_once_with(
            f"No file to remove at {self.dest_dir}/{self.filename}"
        )


if __name__ == "__main__":
    unittest.main()
