import os
import paramiko
from downloader.helper import save_downloaded_files
from downloader.protocols.base_handler import BaseHandler


class SFTPHandler(BaseHandler):
    DEFAULT_PORT = 22

    def __init__(self, stop_event, use_key=False, key_path=None):
        super().__init__(__class__.__name__, stop_event)
        self.use_key = use_key
        self.key_path = key_path

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
                self.logger.info(
                    f"Successfully downloaded '{filename}' to '{dest_dir}'"
                )

                # Saving downloaded filepath to manage name collisions
                key = f"{uri}|{dest_dir}"
                self.downloaded_files[key] = local_filepath
                save_downloaded_files(self.downloaded_files)
                return
            except paramiko.SSHException as e:
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
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if self.use_key and self.key_path:
                key = paramiko.RSAKey.from_private_key_file(self.key_path)
                ssh.connect(hostname, port, username, pkey=key, look_for_keys=False)
            else:
                ssh.connect(
                    hostname,
                    port,
                    username,
                    password,
                    look_for_keys=False,
                    allow_agent=False,
                )

            with ssh.open_sftp() as sftp:

                def callback(transferred, total):
                    if self.stop_requested.is_set():
                        raise KeyboardInterrupt("Download interrupted.")

                sftp.get(remote_path, local_filepath, callback)
