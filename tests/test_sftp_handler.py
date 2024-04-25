import os
import unittest
import threading
import unittest.mock
import paramiko
from unittest.mock import call, patch
from downloader.protocols.sftp_handler import SFTPHandler


class TestSFTPHandler(unittest.TestCase):
    def setUp(self):
        self.uri = "sftp://username:password@hostname/path/to/dummyFile.pdf"
        self.dest_dir = "/fake/dir"
        self.filename = "dummyFile.pdf"
        self.local_filepath = os.path.join(self.dest_dir, self.filename)
        self.hostname = "hostname"
        self.port = 22
        self.username = "username"
        self.password = "password"
        self.remote_path = "/path/to/dummyFile.pdf"
        self.stop_event = threading.Event()
        self.handler = SFTPHandler(self.stop_event, use_key=False)

    @patch("logging.Logger.info")
    @patch("paramiko.SSHClient")
    @patch("downloader.protocols.sftp_handler.SFTPHandler._ensure_directory")
    def test_successful_download(self, mock_ensure_dir, mock_ssh_client, mock_info):
        mock_ensure_dir.return_value = True
        # Mock entering the with statment to start the SFTP context
        mock_ssh = mock_ssh_client.return_value.__enter__.return_value
        mock_sftp = mock_ssh.open_sftp.return_value.__enter__.return_value
        mock_sftp.get.return_value = None

        self.handler.download_file(self.uri, self.dest_dir, 1)

        mock_ssh.connect.assert_called_once_with(
            self.hostname,
            self.port,
            self.username,
            self.password,
            look_for_keys=False,
            allow_agent=False,
        )

        actual_args, _ = mock_sftp.get.call_args
        self.assertEqual(actual_args[0], self.remote_path)
        self.assertEqual(actual_args[1], self.local_filepath)
        self.assertTrue(callable(actual_args[2]))
        mock_info.assert_called_once_with(
            f"Successfully downloaded '{self.filename}' to '{self.dest_dir}'"
        )

    @patch("logging.Logger.debug")
    @patch("logging.Logger.warning")
    @patch("logging.Logger.error")
    @patch("paramiko.SSHClient")
    @patch("downloader.protocols.sftp_handler.SFTPHandler._ensure_directory")
    def test_download_failure_and_retries(
        self, mock_ensure_dir, mock_ssh_client, mock_error, mock_warning, mock_debug
    ):
        retries = 2

        mock_ensure_dir.return_value = True
        mock_ssh = mock_ssh_client.return_value.__enter__.return_value
        mock_ssh.connect.side_effect = paramiko.SSHException("Connection failed")
        mock_ssh.open_sftp.return_value.__enter__.return_value.get.side_effect = (
            paramiko.SSHException("Transfer failed")
        )

        with self.assertRaises(paramiko.SSHException):
            self.handler.download_file(self.uri, self.dest_dir, retries)

        self.assertEqual(mock_ssh.connect.call_count, retries)
        mock_debug.assert_has_calls(
            [
                call(
                    f"(Attempt 1 of 2) - Error downloading file {self.filename}: Connection failed"
                ),
                call(
                    f"(Attempt 2 of 2) - Error downloading file {self.filename}: Connection failed"
                ),
            ],
            any_order=False,
        )
        mock_error.assert_called_once_with(
            f"Failed to download '{self.filename}' after {retries} attempts: Connection failed"
        )
        mock_warning.assert_called_once_with(
            f"No file to remove at {self.dest_dir}/{self.filename}"
        )


if __name__ == "__main__":
    unittest.main()
