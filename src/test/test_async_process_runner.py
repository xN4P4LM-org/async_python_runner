""" Unit tests for the AsyncRunner and CustomProcess classes.
"""
from datetime import timedelta
from multiprocessing import Process
import os
import random
import time
import pytest
from async_python_runner import AsyncRunner
from models.custom_process import CustomProcess
from models.process_status import ProcessStatus
from helpers.directory_searcher import get_files


ROOT_DIR = os.getcwd()

PROCESS_DIR = "sub_process"

RELATIVE_DIR = "src/test/sub_process"

FILES_TO_IGNORE = ["__init__.py", "__pycache__"]


def check_timeout(timeout: timedelta) -> bool:
    """Function to timeout the process."""
    time.sleep(1)
    timeout -= timedelta(seconds=1)
    if timeout == timedelta(seconds=0):
        return True
    return False


def test_process() -> None:
    """Test function for the CustomProcess class."""
    print("Hello, world!")


def custom_async_process() -> CustomProcess:
    """Fixture for the CustomProcess class."""
    process: Process = Process(target=test_process)

    return CustomProcess("test_process", process)


def create_sub_processes() -> None:
    """Creates a random number of sub-processes in the sub_processes folder."""

    custom_process = '''
def main() -> None:
    """Test function for the CustomProcess class."""
    print("Hello, world!")
'''
    number_of_processes = random.randint(5, 15)

    if not os.path.exists(os.path.join(ROOT_DIR, RELATIVE_DIR)):
        os.mkdir(os.path.join(ROOT_DIR, RELATIVE_DIR))

    _process_files, relative_dir = get_files(ROOT_DIR, PROCESS_DIR)

    for process_number in range(number_of_processes):
        file_name = f"test_process_{process_number}.py"
        with open(
            os.path.join(os.path.join(ROOT_DIR, "/".join(relative_dir)), file_name),
            "w",
            encoding="utf-8",
        ) as file:
            file.write(custom_process)


def custom_async_process_runner_folder() -> AsyncRunner:
    """Custom definition for the AsyncRunner class."""
    return AsyncRunner(PROCESS_DIR)


def custom_async_process_runner_file() -> AsyncRunner:
    """Fixture for the AsyncRunner class."""
    return AsyncRunner()


@pytest.mark.asyncio
async def test_custom_process() -> None:
    """Test function for the CustomProcess class."""

    async_process = custom_async_process()
    print(async_process.name)

    async_process.start()
    async_process.join()

    print(async_process.status)

    timeout = timedelta(seconds=5)

    # wait until the process is completed
    # Disabling pylint warning because this is a listener
    # pylint: disable=while-used
    while async_process.status != ProcessStatus.COMPLETED:
        if check_timeout(timeout):
            assert False

    assert async_process.status == ProcessStatus.COMPLETED


@pytest.mark.asyncio
async def test_async_process_runner_folder() -> None:
    """Test function for the AsyncRunner class."""

    create_sub_processes()

    async_process_runner = custom_async_process_runner_folder()

    await async_process_runner.main()

    process_status: list[int] = []

    finished_process = 0

    for active_process in async_process_runner.processes:
        process_status.append(active_process.status)

    timeout = timedelta(seconds=5)

    # wait until all processes are completed
    # Disabling pylint warning because this is a listener
    # pylint: disable=while-used
    while finished_process != len(async_process_runner.processes):
        for active_process in async_process_runner.processes:
            if active_process.status == ProcessStatus.COMPLETED:
                finished_process += 1
        if check_timeout(timeout):
            assert False

    # confirm all processes are completed
    for active_process in async_process_runner.processes:
        assert active_process.status == ProcessStatus.COMPLETED
