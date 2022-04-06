import pytest

from examples.echo import app as echo_app


@pytest.fixture(autouse=True)
def echo_app_harness(app_harness):
    return app_harness(echo_app)


def test_single(socket_client_factory):
    client = socket_client_factory()
    client.write(b"hello")
    response = client.read()
    assert response == b"hello"


def test_multiple(socket_client_factory):
    client1 = socket_client_factory()
    client2 = socket_client_factory()
    client1.write(b"client1")
    client2.write(b"client2")
    assert client1.read() == b"client1"
    assert client2.read() == b"client2"
