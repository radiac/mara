from __future__ import annotations

from mara import App, events
from mara.servers.socket import SocketServer


app = App()
app.add_server(SocketServer(host="127.0.0.1", port=9000))


@app.listen(events.Receive)
async def echo(event: events.Receive):
    event.client.write(event.data)


if __name__ == "__main__":
    app.run()
