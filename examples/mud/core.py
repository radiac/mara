"""
Talker service
"""
import datetime

import mara
service = mara.Service()


from mara.timers.date import DateTimer
@service.timer(DateTimer, minute=0, second=0) # Defaults (explicit for clarity)
def church_bell(timer):
    hour = datetime.datetime.fromtimestamp(service.time).hour % 12
    if hour == 0:
        hour = 12
    service.write_all('A church bell in the distance chimes %d time%s.' % (
        hour, '' if hour == 1 else 's',
    ))
