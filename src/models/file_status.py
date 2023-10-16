"""This is a enum for file status."""

import enum


class FileStatus(enum.Enum):
    """Enum for file status."""

    SUCCESS = "success"
    FAILURE = "failure"
    NOT_FOUND = "not found"
