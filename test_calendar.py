from caldav import DAVClient
from caldav.elements import dav, cdav
from icalendar import Calendar, Event
from datetime import datetime, timedelta

# iCloud credentials
ICLOUD_USERNAME = "watson.bm4@gmail.com"
ICLOUD_APP_PASSWORD = "xokj-olky-xpuc-xspw"

# Connect to iCloud CalDAV
client = DAVClient(
    url="https://caldav.icloud.com/",
    username=ICLOUD_USERNAME,
    password=ICLOUD_APP_PASSWORD
)
principal = client.principal()
calendars = principal.calendars()

print("Available calendars:")
for idx, cal in enumerate(calendars):
    print(idx, cal.name)