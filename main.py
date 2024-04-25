import argparse
import logging
from downloader.download_manager import Downloader


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Output retry logs to a debug_log file to avoid cluttering the console
    file_handler = logging.FileHandler("debug_logs.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(threadName)s] %(levelname)s: %(message)s")
    )
    logger.addHandler(file_handler)

    # Create a console handler for outputting logs to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(
        logging.Formatter("[%(threadName)s] %(levelname)s: %(message)s")
    )
    logger.addHandler(console_handler)


def main():
    setup_logging()

    parser = argparse.ArgumentParser(description="Download files from provided URIs")
    parser.add_argument("uris", nargs="+", help="Lost of uris to download")
    parser.add_argument(
        "--dest",
        type=str,
        default="./downloads",
        help="Destination directory for downloaded files",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of retry attempts for each failed download",
    )

    args = parser.parse_args()

    try:
        downloader = Downloader(args.uris, args.dest, args.retries)
        downloader.download_files()
    except Exception as e:
        logging.exception(f"An error occurred during file downloads: {e}")


if __name__ == "__main__":
    main()
