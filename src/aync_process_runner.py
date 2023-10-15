"""
This script is used to run all the sub-processes in the sub_processes directory

Usage - standalone:
    python async_process_runner.py

    Default values:
        sub_processs_dir: sub_processes
        main_method: main
        logging_dir: logs

Usage - module:
    ```
        import async_process_runner

        runner = async_process_runner.AsyncProcessRunner()
        runner.run()
    ```
"""
import logging
import os
import sys
import importlib
import json
import asyncio
import multiprocessing
from multiprocessing import Process
from datetime import datetime, timedelta
from types import ModuleType
from typing import Any, Union, Dict, Callable, List


class Custom_Process:
    """This class is used to keep track of the status of the sub-processes

    Attributes:
        name (str): The name of the sub-process
        process (Process): The sub-process
        status (str): The status of the sub-process
        start_time (datetime): The start time of the sub-process
        end_time (datetime): The end time of the sub-process
        run_duration (timedelta): The duration of the sub-process

    Possible Statuses:
        - Not Started
        - Running
        - Completed
        - Failed
        - Killed

    """

    def __init__(
        self,
        name: str,
        process: Process,
        status: str = "Not Started",
        start_time: datetime = datetime.now(),
        end_time: datetime = datetime.now(),
        run_duration: timedelta = timedelta(microseconds=0),
    ):
        """This method initializes the process_status class

        Args:
            name (str): The name of the sub-process
        """
        self.name = name
        self.process = process
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        self.run_duration = run_duration

    def start(self) -> None:
        """This method starts the sub-process"""
        self.start_time = datetime.now()
        self.status = "Running"
        self.process.start()

    def join(self) -> None:
        """This method joins the sub-process"""
        self.process.join()
        self.end_time = datetime.now()
        self.run_duration = self.end_time - self.start_time
        self.status = "Completed"

    def get_run_duration(self) -> timedelta:
        """This method returns the run duration of the sub-process"""
        return self.run_duration

    def to_json(self) -> str:
        def serializer(
            serialized_object: Any,
        ) -> Union[
            Dict[str, Union[float, str]],
            Dict[str, Union[Callable[[], float], str]],
            Dict[str, Any],
        ]:
            if isinstance(serialized_object, datetime):
                return {
                    "timestamp": serialized_object.timestamp(),
                    "human_readable": serialized_object.strftime("%Y-%m-%d %H:%M:%S"),
                }
            elif isinstance(serialized_object, timedelta):
                return {
                    "total_seconds": serialized_object.total_seconds(),
                    "human_readable": str(serialized_object),
                }
            elif isinstance(serialized_object, object):
                if hasattr(serialized_object, "__dict__"):
                    return serialized_object.__dict__
                return {
                    "type": str(type(serialized_object)),
                    "value": str(serialized_object),
                }  # added this line to handle other objects
            else:
                raise TypeError(
                    f"Object of type {type(serialized_object)} is not JSON serializable"
                )

        return json.dumps(self, default=serializer, sort_keys=True, indent=4)


class AsyncProcessRunner:
    def __init__(
        self,
        sub_processs_dir: str = "sub_processes",
        main_method: str = "main",
        logging_dir: str = "logs",
    ):
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.MAIN_METHOD = main_method
        self.LOGGING_DIR = logging_dir
        self.sub_processs_dir = sub_processs_dir

    def get_sub_processes(self) -> List[ModuleType]:
        """Call the main method of each sub_process"""

        module_name = ""
        modules: List[ModuleType] = []

        for self.sub_process in os.listdir(self.BASE_DIR):
            if os.path.isdir(os.path.join(self.BASE_DIR, self.sub_process)):
                # Get the sub_process's main module
                # Try to import the sub_process's main module
                try:
                    module_name = (
                        f".sub_processes.{self.sub_process}.{self.sub_process}"
                    )
                    sub_process_module = importlib.import_module(
                        self.sub_process, module_name
                    )

                    # If the module has the main method, call it
                    if hasattr(sub_process_module, self.MAIN_METHOD):
                        modules.append(sub_process_module)
                except ImportError:
                    print(f"Failed to import {module_name}")

        return modules

    def create_sub_processes(
        self, sub_processes: List[ModuleType]
    ) -> List[Custom_Process]:
        """This method creates a list of sub-processes for each sub_process"""
        processes: List[Custom_Process] = []

        for sub_process in sub_processes:
            process = multiprocessing.Process(
                target=getattr(sub_process, self.MAIN_METHOD)
            )
            processes.append(Custom_Process(sub_process.__name__, process))
        return processes

    async def start_process(self, custom_process: Custom_Process):
        """Async function to start a Custom_Process."""
        custom_process.start()
        logging.info(f"{custom_process.name} started")
        await asyncio.sleep(0)  # Yield back to the event loop

    async def check_processes(self, process: Custom_Process) -> None:
        """This method checks the status of all the sub-processes"""
        while True:
            if process.status == "Running":
                logging.info(f"{process.name} is running")
                await asyncio.sleep(60)
                continue
            if process.status == "Completed":
                logging.info(
                    f"{process.name} completed in {process.get_run_duration()}"
                )
            elif process.status == "Failed":
                logging.error(f"{process.name} failed")
            elif process.status == "Killed":
                logging.error(f"{process.name} was killed")
            await asyncio.sleep(1)

    async def main(self) -> None:
        """This method calls all the sub-processes and starts them
        it then monitors the status of all the sub-processes until they
        either all complete, fail, or are killed
        """

        sub_processes: List[ModuleType] = self.get_sub_processes()
        if not sub_processes:
            print("No sub-processes found")
            exit(-1)

        processes: List[Custom_Process] = self.create_sub_processes(sub_processes)

        try:
            tasks = [
                self.start_process(custom_process) for custom_process in processes
            ] + [self.check_processes(custom_process) for custom_process in processes]

            await asyncio.gather(*tasks)

        except Exception as e:
            print(e)
            exit()

    def run(self) -> None:
        """This method sets up the logging and runs the main method"""

        # if directory does not exist then create it recursively
        if not os.path.exists(self.LOGGING_DIR):
            os.makedirs(self.LOGGING_DIR)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(os.path.join(self.LOGGING_DIR, "log.txt")),
                logging.StreamHandler(),
            ],
        )
        logging.info("Starting main process")
        asyncio.run(self.main())
        logging.info("Main process completed")


if __name__ == "__main__":
    # get the arguments passed in from the command line
    args = sys.argv[1:]

    # if there are no arguments then run the script with the default values
    if len(args) == 0:
        runner = AsyncProcessRunner()
    # if there are arguments then run the script with the arguments
    else:
        # if there are 3 arguments then run the script with the arguments
        if len(args) == 3:
            runner = AsyncProcessRunner(args[0], args[1], args[2])
        # if there are not 3 arguments then run the script with the default values
        else:
            runner = AsyncProcessRunner()

    runner.run()
