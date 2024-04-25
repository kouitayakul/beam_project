import os
import logging
from urllib.parse import urlparse

from downloader.helper import load_downloaded_files


class BaseHandler:
    def __init__(self, logger_name, stop_event):
        self.logger = logging.getLogger(logger_name)
        self.stop_requested = stop_event
        self.downloaded_files = load_downloaded_files()

    def _ensure_directory(self, path):
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except OSError as e:
            self.logger.error(f"Failed to create directory {path}: {e}")
            return False

    def _cleanup_file(self, filepath):
        try:
            os.remove(filepath)
            self.logger.info(f"Removed partial download {filepath}")
        except FileNotFoundError:
            self.logger.warning(f"No file to remove at {filepath}")
        except OSError as e:
            self.logger.error(f"Failed to remove partial download {filepath}: {e}")

    def _parse_uri(self, uri, default_port):
        parsed_uri = urlparse(uri)

        hostname = parsed_uri.hostname
        port = parsed_uri.port or default_port
        username = parsed_uri.username or "anonymous"
        password = parsed_uri.password or "anonymous"
        remote_path = parsed_uri.path

        return hostname, int(port), username, password, remote_path

    def _handle_error(self, e, attempt, retries, filename, local_filepath):
        self.logger.debug(
            f"(Attempt {attempt} of {retries}) - Error downloading file {filename}: {e}"
        )

        if attempt == retries:
            self.logger.error(
                f"Failed to download '{filename}' after {retries} attempts: {e}"
            )
            self._cleanup_file(local_filepath)
            raise e

    def _get_local_filepath(self, uri, dest_dir):
        key = f"{uri}|{dest_dir}"

        if key in self.downloaded_files:
            return self.downloaded_files[key]

        filename = os.path.basename(uri)
        filepath = os.path.join(dest_dir, filename)

        if not os.path.exists(filepath):
            return filepath

        basename, extension = os.path.splitext(filename)

        counter = 1
        new_filename = f"{basename}_{counter}{extension}"
        new_path = os.path.join(dest_dir, new_filename)

        while os.path.exists(new_path):
            counter += 1
            new_filename = f"{basename}_{counter}{extension}"
            new_path = os.path.join(dest_dir, new_filename)

        return new_path
