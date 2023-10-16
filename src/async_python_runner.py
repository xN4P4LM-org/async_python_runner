""" This script is used to run all the sub-processes in the sub_processes directory.

Usage - standalone:
    python async_process_runner.py

    Default values:
        sub_process_dir: sub_processes
        main_method: main
        logging_dir: logs

Usage - module:
    import async_process_runner

    runner = async_process_runner.AsyncProcessRunner()
    runner.run()
"""
import logging
import os
import importlib
import asyncio
import multiprocessing
import argparse
import sys
import textwrap
from types import ModuleType
from helpers.directory_searcher import get_files
from models.custom_process import CustomProcess

logging.basicConfig(level=logging.INFO)


class AsyncRunner:
    """Class to asynchronously run and manage multiple subprocesses."""

    FILES_TO_IGNORE = ["__init__.py", "__pycache__", "__init__"]
    ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

    def __init__(
        self,
        sub_process_dir: str = "sub_processes",
        main_method: str = "main",
        logging_dir: (str | None) = None,
    ):
        """Initializes an AsyncProcessRunner instance.

        Args:
            sub_process_dir (str): Directory containing the subprocesses.
            Default is 'sub_processes'.
        """

        self.sub_process_dir = sub_process_dir
        self.main_method = main_method
        if logging_dir is None:
            self.logging_dir = os.path.join(self.ROOT_DIR, "logs")
        else:
            self.logging_dir = logging_dir
        self.processes: list[CustomProcess] = []

    def get_sub_processes(self) -> list[ModuleType]:
        """Retrieve subprocesses from the directory.

        Returns:
            list[ModuleType]: list of imported subprocess modules.
        """
        modules: list[ModuleType] = []
        list_of_modules, module_path = get_files(self.ROOT_DIR, self.sub_process_dir)

        updated_modules: list[str] = []

        for module_names in list_of_modules:
            if module_names in self.FILES_TO_IGNORE:
                list_of_modules.remove(module_names)
                continue
            if module_names.endswith(".py"):
                # remove the .py extension
                updated_modules.append(module_names[:-3])

        logging.info("Modules to be imported: %s", updated_modules)
        logging.info("Module path: %s", module_path)

        module_base_name = "."

        for module in updated_modules:
            # combine the module path with the module name
            combined_module_path = module_path + [module]

            full_module_path = module_base_name.join(combined_module_path)
            print(full_module_path, module)
            modules.append(importlib.import_module(full_module_path, self.main_method))

        return modules

    def create_sub_processes(self) -> None:
        """Initializes subprocess instances from discovered modules."""
        for module in self.get_sub_processes():
            process = multiprocessing.Process(target=module.main)
            self.processes.append(CustomProcess(module.__name__, process))

    async def main(self) -> None:
        """Main method that initializes and starts all subprocesses."""
        self.create_sub_processes()
        tasks = [
            task
            for task in (
                [p.start() for p in self.processes] + [p.join() for p in self.processes]
            )
            if task is not None
        ]

        await asyncio.gather(*tasks)

    def run(self) -> None:
        """Sets up logging and runs the main asynchronous method."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            filename=os.path.join(self.logging_dir, "async_python_runner.log"),
        )
        logging.info("Starting main process")
        asyncio.run(self.main())
        logging.info("Main process completed")


def main() -> None:
    """Main function to run the async process runner."""

    long_description = """\
This command allow you to run multiple python both multithreaded and asynchronously.\n

\n
Use:\n
Create a sub_processes directory and point to it using the -d flag to define the
directory. Then create python files in the sub_processes directory and define a main
method in each file. The main method will be the entry point for each subprocess.\n
\n
Example:\n
    async_python_runner -d /User/testing/sub_processes -m main -l /temp/logs\n
\n
This will run all the python files in the /User/testing/sub_processes directory
asynchronously and log the output to the /temp/logs/async_python_runner.log file.
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(long_description),
        prog="async_python_runner",
        usage="%(prog)s [options]",
        add_help=True,
    )
    parser.add_argument(
        "-d",
        "--sub-processes-dir",
        type=str,
        default="sub_processes",
        help="The path to the sub-processes directory.",
    )
    parser.add_argument(
        "-m",
        "--main-method",
        type=str,
        default="main",
        help="The main method name in the sub-processes.",
    )
    parser.add_argument(
        "-l",
        "--logging-dir",
        type=str,
        default="logs",
        help="The path to the logging directory",
    )
    args = parser.parse_args(sys.argv[1:3])

    runner = AsyncRunner(
        sub_process_dir=str(args.sub_processes_dir),
        main_method=str(args.main_method),
        logging_dir=str(args.logging_dir),
    )
    runner.run()


if __name__ == "__main__":
    main()
