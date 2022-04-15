import pytest

from examples.chat import app as chat_app


@pytest.fixture(autouse=True)
def echo_app_harness(app_harness):
    return app_harness(chat_app)


def test_single(socket_client_factory):
    alice = socket_client_factory()
    assert alice.read() == b"Username: "
    alice.write(b"alice\r\n")
    assert alice.read() == b"* alice has joined\r\n"
    alice.write(b"hello\r\n")
    assert alice.read() == b"alice says: hello\r\n"


def test_multiple__login_private__chat_public(socket_client_factory):
    alice = socket_client_factory(name="alice")
    bob = socket_client_factory(name="bob")

    # Alice logs in
    assert alice.read() == b"Username: "
    alice.write(b"alice\r\n")
    assert alice.read() == b"* alice has joined\r\n"

    # Alice cannot talk to bob until he is logged in
    alice.write(b"alone\r\n")
    assert alice.read() == b"alice says: alone\r\n"

    # Bob logs in
    assert bob.read() == b"Username: "
    bob.write(b"bob\r\n")
    assert bob.read() == b"* bob has joined\r\n"

    # Alice sees this
    assert alice.read() == b"* bob has joined\r\n"

    # They can now talk
    alice.write(b"hello\r\n")
    assert alice.read() == b"alice says: hello\r\n"
    assert bob.read() == b"alice says: hello\r\n"
    bob.write(b"goodbye\r\n")
    assert alice.read() == b"bob says: goodbye\r\n"
    assert bob.read() == b"bob says: goodbye\r\n"
