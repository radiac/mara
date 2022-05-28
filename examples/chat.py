"""
A basic chat server
"""
from mara import App, events
from mara.servers.base import AbstractServer
from mara.servers.socket import TextServer
from mara.timers import PeriodicTimer


app = App()
server = TextServer(host="0", port=9000)
app.add_server(server)


def broadcast(server: AbstractServer, msg: str):
    "Send a message out to all connected users"
    for client in server.clients:
        if "username" not in client.session:
            continue
        client.write(msg)


@app.listen(events.Connect)
async def login(event: events.Connect):
    "Prompt for a username and announce to users"
    event.client.write("Username: ", end="")
    username = await event.client.read()
    event.client.write("")

    event.client.session.username = username
    broadcast(event.client.server, f"* {username} has joined")


@app.listen(events.Receive)
async def input(event: events.Receive):
    "Broadcast a chat message"
    broadcast(
        event.client.server, f"{event.client.session.username} says: {event.data}"
    )


@app.listen(events.Disconnect)
async def leave(event: events.Disconnect):
    "Announce departure to users"
    broadcast(event.client.server, f"* {event.client.session.username} has left")


@app.add_timer(PeriodicTimer(every=60))
async def poll(timer):
    for server in timer.app.servers:
        for client in server.clients:
            if "username" not in client.session:
                continue
            client.write("Beep!")


if __name__ == "__main__":
    app.run()
