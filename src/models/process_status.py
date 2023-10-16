"""Enum-like class representing the status of a process."""
import dataclasses


@dataclasses.dataclass
class ProcessStatus:
    """Enum-like class representing the status of a process."""

    NOT_STARTED, RUNNING, COMPLETED, FAILED, KILLED = range(5)
