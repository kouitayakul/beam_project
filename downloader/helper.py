import json


def load_downloaded_files():
    try:
        with open("downloaded_files.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_downloaded_files(downloaded_files):
    with open("downloaded_files.json", "w") as file:
        json.dump(downloaded_files, file, indent=4)
