import logging
import threading
from downloader.protocols.ftp_handler import FTPHandler
from downloader.protocols.http_handler import HTTPHandler
from downloader.protocols.sftp_handler import SFTPHandler
from concurrent.futures import ThreadPoolExecutor, as_completed


class Downloader:
    def __init__(self, uris, dest_dir, retries, max_workers=None):
        self.uris = uris
        self.dest_dir = dest_dir
        self.retries = retries
        self.max_workers = max_workers if max_workers else len(uris)
        self.stop_event = threading.Event()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.protocol_handlers = {
            "http": HTTPHandler(self.stop_event),
            "https": HTTPHandler(self.stop_event),
            "ftp": FTPHandler(self.stop_event),
            "sftp": SFTPHandler(self.stop_event),
        }

    def download_files(self):
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._download_file, uri) for uri in self.uris]

            try:
                for future in as_completed(futures):
                    if self.stop_event.is_set():
                        return
                    future.result()
            except KeyboardInterrupt:
                self.stop_event.set()
                return

    def _download_file(self, uri):
        self.logger.info(f"Downloading from {uri} ...")

        protocol = uri.split("://")[0]
        handler = self.protocol_handlers.get(protocol)

        if handler:
            try:
                handler.download_file(uri, self.dest_dir, self.retries)
            except Exception as e:
                self.logger.error(f"Failed to download {uri}: {e}")
        else:
            self.logger.warning(f"Unsupported protocol in uri: {uri}")
