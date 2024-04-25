import os
import ftplib
import threading
import unittest
from unittest.mock import call, patch, mock_open
from downloader.protocols.ftp_handler import FTPHandler


class TestFTPHandler(unittest.TestCase):
    def setUp(self):
        self.uri = "ftp://username:password@hostname/path/to/dummyFile.pdf"
        self.dest_dir = "/fake/dir"
        self.filename = "dummyFile.pdf"
        self.local_filepath = os.path.join(self.dest_dir, self.filename)
        self.stop_event = threading.Event()
        self.handler = FTPHandler(self.stop_event)

    @patch("logging.Logger.info")
    @patch("ftplib.FTP")
    @patch("builtins.open", new_callable=mock_open)
    @patch("downloader.protocols.ftp_handler.FTPHandler._ensure_directory")
    def test_successful_download(self, mock_ensure_dir, mock_open, mock_ftp, mock_info):
        mock_ensure_dir.return_value = True
        # Mock entering the with statment to start the FTP context
        mock_ftp_instance = mock_ftp.return_value.__enter__.return_value
        mock_ftp_instance.retrbinary.side_effect = lambda _, callback: callback(
            b"file data"
        )

        self.handler.download_file(self.uri, self.dest_dir, 1)

        mock_open.assert_any_call(self.local_filepath, "wb")
        mock_ftp_instance.retrbinary.assert_called_once()
        args, _ = mock_ftp_instance.retrbinary.call_args
        assert args[0] == "RETR /path/to/dummyFile.pdf"
        mock_ftp_instance.connect.assert_called_once_with("hostname", 21)
        mock_ftp_instance.login.assert_called_once_with("username", "password")
        mock_info.assert_has_calls(
            [
                call("Connected to FTP server at hostname"),
                call(f"Successfully downloaded {self.filename} to {self.dest_dir}"),
            ],
            any_order=False,
        )

    @patch("logging.Logger.debug")
    @patch("logging.Logger.warning")
    @patch("logging.Logger.error")
    @patch("builtins.open", new_callable=mock_open)
    @patch("ftplib.FTP")
    @patch("downloader.protocols.ftp_handler.FTPHandler._ensure_directory")
    def test_download_failure_and_retries(
        self, mock_ensure_dir, mock_ftp, mock_open, mock_error, mock_warning, mock_debug
    ):
        retries = 2

        mock_ensure_dir.return_value = True
        mock_ftp_instance = mock_ftp.return_value.__enter__.return_value
        mock_ftp_instance.retrbinary.side_effect = ftplib.error_perm(
            "550 Permission denied."
        )

        with self.assertRaises(ftplib.error_perm):
            self.handler.download_file(self.uri, self.dest_dir, retries)

        self.assertEqual(mock_ftp_instance.retrbinary.call_count, retries)
        mock_debug.assert_has_calls(
            [
                call(
                    f"(Attempt 1 of 2) - Error downloading file {self.filename}: 550 Permission denied."
                ),
                call(
                    f"(Attempt 2 of 2) - Error downloading file {self.filename}: 550 Permission denied."
                ),
            ],
            any_order=False,
        )
        mock_error.assert_called_once_with(
            f"Failed to download '{self.filename}' after {retries} attempts: 550 Permission denied."
        )
        mock_warning.assert_called_once_with(
            f"No file to remove at {self.dest_dir}/{self.filename}"
        )


if __name__ == "__main__":
    unittest.main()
