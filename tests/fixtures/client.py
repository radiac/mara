from __future__ import annotations

import logging
import socket

import pytest

from .constants import TEST_HOST, TEST_PORT


logger = logging.getLogger("tests.fixtures.client")


class BaseClient:
    """
    Blocking test client to connect to an app server
    """

    name: str

    def __init__(self, name: str):
        self.name = name


class SocketClient(BaseClient):
    socket: socket.socket | None

    def connect(self, host: str, port: int):
        logger.debug("Socket client connecting")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        logger.debug("Socket client connected")

    def write(self, raw: bytes):
        if not self.socket:
            raise ValueError("Socket not open")
        logger.debug(f"Socket client writing {raw!r}")
        self.socket.sendall(raw)

    def read(self, len: int = 1024) -> bytes:
        if not self.socket:
            raise ValueError("Socket not open")
        raw: bytes = self.socket.recv(len)
        logger.debug(f"Socket client received {raw!r}")
        return raw

    def close(self):
        if not self.socket:
            raise ValueError("Socket not open")
        logger.debug("Socket client closing")
        self.socket.close()
        logger.debug("Socket client closed")


@pytest.fixture
def socket_client_factory(request: pytest.FixtureRequest):
    """
    Socket client factory fixture

    Usage::

        def test_client(app_harness, socket_client_factory):
            app_harness(myapp)
            client= socket_client_factory()
            client.write(b'hello')
            assert client.read() == b'hello'
    """
    clients = []

    def connect(host: str = TEST_HOST, port: int = TEST_PORT):
        client = SocketClient(request.node.name)
        client.connect(host, port)
        clients.append(client)
        return client

    yield connect

    for client in clients:
        client.close()
