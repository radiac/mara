import pytest

from examples.chat import app as chat_app


@pytest.fixture(autouse=True)
def echo_app_harness(app_harness):
    return app_harness(chat_app)


def test_single(socket_client_factory):
    alice = socket_client_factory()
    assert alice.read() == b"Username: "
    alice.write(b"alice\r\n")
    assert alice.read_line() == b""
    assert alice.read_line() == b"* alice has joined"
    alice.write(b"hello\r\n")
    assert alice.read_line() == b"alice says: hello"


def test_multiple__login_private__chat_public(socket_client_factory):
    alice = socket_client_factory(name="alice")
    bob = socket_client_factory(name="bob")

    # Alice logs in
    assert alice.read() == b"Username: "
    alice.write(b"alice\r\n")
    assert alice.read_line() == b""
    assert alice.read_line() == b"* alice has joined"

    # Alice cannot talk to bob until he is logged in
    alice.write(b"alone\r\n")
    assert alice.read_line() == b"alice says: alone"

    # Bob logs in
    assert bob.read() == b"Username: "
    bob.write(b"bob\r\n")
    assert bob.read_line() == b""
    assert bob.read_line() == b"* bob has joined"

    # Alice sees this
    assert alice.read_line() == b"* bob has joined"

    # They can now talk
    alice.write(b"hello\r\n")
    assert alice.read_line() == b"alice says: hello"
    assert bob.read_line() == b"alice says: hello"
    bob.write(b"goodbye\r\n")
    assert alice.read_line() == b"bob says: goodbye"
    assert bob.read_line() == b"bob says: goodbye"
