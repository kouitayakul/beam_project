import os
import requests
from downloader.helper import save_downloaded_files
from downloader.protocols.base_handler import BaseHandler


class HTTPHandler(BaseHandler):
    DEFAULT_CHUNK_SIZE = 8192
    DEFAULT_TIMEOUT = 10
    DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"

    def __init__(
        self,
        stop_event,
        chunk_size=DEFAULT_CHUNK_SIZE,
        timeout=DEFAULT_TIMEOUT,
        user_agent=DEFAULT_USER_AGENT,
    ):
        super().__init__(__class__.__name__, stop_event)
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.user_agent = user_agent

    def download_file(self, uri, dest_dir, retries):
        if not self._ensure_directory(dest_dir):
            return

        filename = os.path.basename(uri)
        local_filepath = self._get_local_filepath(uri, dest_dir)

        for attempt in range(1, retries + 1):
            try:
                self._attempt_download(uri, local_filepath)
                self.logger.info(
                    f"Successfully downloaded '{filename}' to '{dest_dir}'"
                )

                # Saving downloaded filepath to manage name collisions
                key = f"{uri}|{dest_dir}"
                self.downloaded_files[key] = local_filepath
                save_downloaded_files(self.downloaded_files)
                return
            except (requests.RequestException, OSError) as e:
                self._handle_error(e, attempt, retries, filename, local_filepath)
            except KeyboardInterrupt as e:
                self.logger.error(f"Failed to download {filename}: {e}")
                self._cleanup_file(local_filepath)
                return
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                self._cleanup_file(local_filepath)
                return

    def _attempt_download(self, uri, filepath):
        # To avoid web servers from blocking our access, User-Agent helps identify this script as a legitimate tool
        headers = {"User-Agent": self.user_agent}

        response = requests.get(uri, headers=headers, stream=True, timeout=self.timeout)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=self.chunk_size):
                if self.stop_requested.is_set():
                    raise KeyboardInterrupt("Download interrupted.")

                f.write(chunk)
