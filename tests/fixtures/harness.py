"""
Test harness to run mara in a separate thread to tests
"""
from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING

import pytest

from mara.app.app import Status
from mara.servers.socket import SocketServer

from .constants import TEST_HOST, TEST_PORT


logger = logging.getLogger("tests.fixtures.harness")


if TYPE_CHECKING:
    from mara import App

# Debug everything that we do
DEBUG = False

# Limits for attempting to start the server, and to connect to the server
ATTEMPT_MAX = 10
ATTEMPT_SLEEP = 0.1


class ThreadCounter(object):
    """
    Global thread counter to generate unique ids
    """

    def __init__(self):
        self.count = 0

    def get(self):
        self.count += 1
        return self.count


_thread_counter = ThreadCounter()


class AppHarness:
    """
    Run the app in a separate thread
    """

    name: str
    app: App

    def __init__(self, name: str):
        self.name = name

    def run(self, app: App):
        self.app = app

        # Give service a thread
        self.thread_id = _thread_counter.get()

        # Start service thread
        self._exception = None
        self.thread = threading.Thread(
            name="%s-%s" % (self.__class__.__name__, self.thread_id),
            target=self._run_app,
        )
        self.thread.daemon = True  # Kill with main process
        logger.debug("App thread starting")
        self.thread.start()

        # Wait for service to start or fail
        running = False
        while not self._exception and not running:
            time.sleep(ATTEMPT_SLEEP)
            running = self.app.status >= Status.RUNNING

        # Catch failure
        if not running:
            logger.debug("App failed to start in time, killing thread")
            self.thread.join()
            raise RuntimeError("Thread %s failed" % self.thread.name)

        if self._exception:
            logger.debug(
                f"App failed to start with exception {self._exception}, killing thread"
            )
            self.thread.join()
            raise RuntimeError("Thread %s failed" % self.thread.name)

        logger.debug("App thread is running")

    def _run_app(self):
        """
        Run the app. Call this as a thread target.
        """
        logger.debug("App running")
        try:
            self.app.run()
        except Exception as e:
            self._exception = e
            logger.debug(f"App error: {e}")
            raise

    def stop(self):
        """
        Stop the app
        """
        if not self.app.loop:
            raise ValueError("Loop does not exist")
        logger.debug("App stopping")
        self.app.loop.call_soon_threadsafe(self.app.stop)
        logger.debug("App stopped, killing thread")
        self.thread.join()
        logger.debug("App thread destroyed")


@pytest.fixture
def app_harness(request: pytest.FixtureRequest):
    harness = AppHarness(name=request.node.name)

    def create_harness(app: App):
        for i, server in enumerate(app.servers):
            if isinstance(server, SocketServer):
                server.host = TEST_HOST
                server.port = TEST_PORT + i
        harness.run(app)

    yield create_harness

    harness.stop()
