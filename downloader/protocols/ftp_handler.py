import os
import ftplib
from downloader.helper import save_downloaded_files
from downloader.protocols.base_handler import BaseHandler


class FTPHandler(BaseHandler):
    DEFAULT_PORT = 21

    def __init__(self, stop_event):
        super().__init__(__class__.__name__, stop_event)

    def download_file(self, uri, dest_dir, retries):
        if not self._ensure_directory(dest_dir):
            return

        filename = os.path.basename(uri)
        local_filepath = self._get_local_filepath(uri, dest_dir)

        hostname, port, username, password, remote_path = self._parse_uri(
            uri, self.DEFAULT_PORT
        )

        for attempt in range(1, retries + 1):
            try:
                self._attempt_download(
                    hostname, port, username, password, remote_path, local_filepath
                )
                self.logger.info(f"Successfully downloaded {filename} to {dest_dir}")

                # Saving downloaded filepath to manage name collisions
                key = f"{uri}|{dest_dir}"
                self.downloaded_files[key] = local_filepath
                save_downloaded_files(self.downloaded_files)
                return
            except ftplib.all_errors as e:
                self._handle_error(e, attempt, retries, filename, local_filepath)
            except KeyboardInterrupt as e:
                self.logger.error(f"Failed to download {filename}: {e}")
                self._cleanup_file(local_filepath)
                return
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                self._cleanup_file(local_filepath)
                return

    def _attempt_download(
        self, hostname, port, username, password, remote_path, local_filepath
    ):
        with ftplib.FTP() as ftp:
            ftp.connect(hostname, port)
            ftp.login(username, password)

            self.logger.info(f"Connected to FTP server at {hostname}")

            with open(local_filepath, "wb") as f:

                def callback(data):
                    if self.stop_requested.is_set():
                        raise KeyboardInterrupt("Download interrupted.")
                    f.write(data)

                ftp.retrbinary(f"RETR {remote_path}", callback)
