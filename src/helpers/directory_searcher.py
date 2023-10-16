""" This class is used to search directories for the target directory and get all the 
files in it."""
import logging
import os
from models.file_status import FileStatus


FILES_TO_IGNORE: list[str] = ["__init__.py", "__pycache__"]
ROOT_DIR = os.getcwd()


def find_dir(start_dir: str, target_dir: str) -> tuple[str, str]:
    """Find a directory recursively starting from a given path."""
    for root, dirs, _ in os.walk(start_dir):
        if target_dir in dirs:
            possible_path = os.path.join(root, target_dir)
            relative_path = os.path.relpath(possible_path, start_dir)
            return relative_path, possible_path
    return FileStatus.NOT_FOUND.value, FileStatus.NOT_FOUND.value


def get_files(start_dir: str, target_dir: str) -> tuple[list[str], list[str]]:
    """Get all files in the target directory."""
    logging.info("Searching for %s directory...", target_dir)

    relative_path, absolute_path = find_dir(start_dir, target_dir)

    if relative_path == FileStatus.NOT_FOUND.value:
        return [], ["not found"]

    files = [
        file_name
        for file_name in os.listdir(absolute_path)
        if os.path.isfile(os.path.join(absolute_path, file_name))
        and file_name.endswith(".py")
    ]

    return files, relative_path.split(os.sep)
