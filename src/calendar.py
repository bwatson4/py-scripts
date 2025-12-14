from caldav import DAVClient
from icalendar import Calendar, Event, Alarm
from datetime import timedelta
from config import ICLOUD_USERNAME, ICLOUD_APP_PASSWORD, CALENDAR_INDEX
from utils import log

class CalendarManager:
    def __init__(self, username=ICLOUD_USERNAME, password=ICLOUD_APP_PASSWORD, calendar_index=CALENDAR_INDEX, client=None, calendar=None):
        # allow injection of mock client/calendar for testing
        if client is not None and calendar is not None:
            self.client = client
            self.calendar = calendar
            return

        self.client = DAVClient(
            url="https://caldav.icloud.com/",
            username=username,
            password=password
        )
        self.principal = self.client.principal()
        self.calendars = self.principal.calendars()
        if len(self.calendars) <= calendar_index:
            raise IndexError("Calendar index out of range")
        self.calendar = self.calendars[calendar_index]

    def add_or_update_event(self, event_data):
        """
        Adds or updates a single event.
        event_data should include:
        {
            'uid': str,
            'summary': str,
            'description': str,
            'start': datetime,
            'end': datetime
        }
        """
        if not isinstance(event_data, dict):
            raise TypeError(
                "add_or_update_event expects a single event dict. "
                "For multiple events, use add_or_update_events()."
            )
        existing_event = None
        for ev in self.calendar.events():
            cal = ev.vobject_instance
            uid = str(cal.vevent.uid.value)
            if uid == event_data["uid"]:
                existing_event = ev
                break

        if existing_event:
            log(f"Updating existing event: {event_data['summary']}")
            cal = existing_event.vobject_instance
            cal.vevent.summary.value = event_data["summary"]
            cal.vevent.description.value = event_data["description"]
            cal.vevent.dtstart.value = event_data["start"]
            cal.vevent.dtend.value = event_data["end"]

            # Update or add alarm
            if hasattr(cal.vevent, 'valarms') and cal.vevent.valarms:
                alarm = cal.vevent.valarms[0]
                alarm.description.value = f"Upcoming: {event_data['summary']}"
                alarm.trigger.value = timedelta(minutes=-30)
            else:
                alarm = cal.vevent.add('valarm')
                alarm.add('action').value = 'DISPLAY'
                alarm.add('description').value = f"Upcoming: {event_data['summary']}"
                alarm.add('trigger').value = timedelta(minutes=-30)


            existing_event.save()
        else:
            cal = Calendar()
            ev = Event()
            ev.add("uid", event_data["uid"])
            ev.add("summary", event_data["summary"])
            ev.add("description", event_data["description"])
            ev.add("dtstart", event_data["start"])
            ev.add("dtend", event_data["end"])

            alarm = Alarm()
            alarm.add("action", "DISPLAY")
            alarm.add("description", f"Upcoming: {event_data['summary']}")
            alarm.add("trigger", timedelta(minutes=-30))
            ev.add_component(alarm)

            cal.add_component(ev)
            self.calendar.add_event(cal.to_ical())

    def add_or_update_events(self, events):
        """
        Adds or updates multiple events.
        Accepts a list of event dictionaries or a single event dictionary.
        """
        if isinstance(events, dict):
            events = [events]

        for event_data in events:
            self.add_or_update_event(event_data)
