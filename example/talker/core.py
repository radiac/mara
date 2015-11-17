"""
Talker service
"""
import datetime

import cletus
service = cletus.Service()

# Add user to client events
from cletus import events
from cletus.contrib.commands import CommandEvent
from cletus.contrib.users import event_add_user
service.listen(events.Connect, event_add_user)
service.listen(events.Disconnect, event_add_user)
service.listen(events.Receive, event_add_user)
service.listen(CommandEvent, event_add_user)


@service.timer(period=60*60)
def every_minute(timer):
    service.write_all('Another hour has passed')

from cletus.timers.date import DateTimer
@service.timer(DateTimer, minute=0, second=0) # Defaults (explicit for clarity)
def church_bell(timer):
    hour = datetime.datetime.fromtimestamp(service.time).hour % 12
    if hour == 0:
        hour = 12
    service.write_all('A church bell in the distance chimes %d time%s.' % (
        hour, '' if hour == 1 else 's',
    ))


# Set up a filter for write_all to filter to users who have logged in,
# otherwise they'll see things on the login prompt
def filter_to_users(service, clients, **kwargs):
    return (c for c in clients if getattr(c, 'user', None))
service.filter_all = filter_to_users
