import asyncio
import logging
import sys
from os import getenv


class Whitelist(logging.Filter):
    def __init__(self, *whitelist):
        self.whitelist = [logging.Filter(name) for name in whitelist]

    def filter(self, record):
        return any(f.filter(record) for f in self.whitelist)


def configure():
    """
    Configure logging

    Pick up the log level from the env var LOGLEVEL, otherwise default to INFO
    """
    # TODO: Simple configuration of what to log and where to log it to
    level_name = getenv("LOGLEVEL", "INFO")
    level = getattr(logging, level_name)
    logging.basicConfig(stream=sys.stdout, filemode="w", level=level)

    for handler in logging.root.handlers:
        handler.addFilter(Whitelist("mara", "tests"))


def get_tasks(loop):
    """
    List the current tasks in the loop

    Usage::

        logger.debug(get_tasks(app.loop))
    """
    tasks = asyncio.all_tasks(loop)
    return "Tasks: " + ", ".join(
        [f"{task.get_name()}: {task.get_coro().__name__}" for task in tasks]
    )
