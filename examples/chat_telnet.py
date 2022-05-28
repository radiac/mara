"""
An extension of the chat server that runs with telnet support

Requires additional libraries::

    pip install telnetlib3
"""

from chat import app, server

from mara.servers.telnet import TelnetServer


app.remove_server(server)
app.add_server(TelnetServer(host="0", port=9000))

if __name__ == "__main__":
    app.run()
