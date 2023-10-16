"""CustomProcess class definition.

This module contains the CustomProcess class definition.

"""
import multiprocessing
import logging
from .process_status import ProcessStatus


class CustomProcess:
    """Representative class for subprocesses, encapsulating their management."""

    def __init__(self, name: str, process: multiprocessing.Process):
        """Initializes a CustomProcess instance.

        Args:
            name (str): Name of the subprocess.
            process (multiprocessing.Process): Multiprocessing instance to run.
        """
        self.name = name
        self.process = process
        self.status = ProcessStatus.NOT_STARTED

    def start(self) -> None:
        """Starts the subprocess."""
        self.status = ProcessStatus.RUNNING
        logging.info("%s started", self.name)
        self.process.start()

    def join(self) -> None:
        """Waits for the subprocess to finish execution."""
        self.process.join()
        logging.info("%s finished", self.name)
        self.status = ProcessStatus.COMPLETED
