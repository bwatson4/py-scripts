# tests/test_calendar.py
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from icalendar import Calendar, Event, Alarm
from src.calendar import CalendarManager  # adjust import if needed

@pytest.fixture
def mock_caldav():
    """Mock DAVClient and calendar structure"""
    with patch("src.calendar.DAVClient") as mock_client:
        # Mock the principal and calendars
        mock_principal = MagicMock()
        mock_calendar = MagicMock()

        # Mock an existing event
        mock_event = MagicMock()
        mock_event.vobject_instance = MagicMock()
        mock_event.vobject_instance.vevent.uid.value = "existing-uid"
        mock_event.vobject_instance.vevent.valarms = []

        # calendar.events() returns a list with one existing event
        mock_calendar.events.return_value = [mock_event]
        mock_principal.calendars.return_value = [mock_calendar]
        mock_client.return_value.principal.return_value = mock_principal

        yield mock_client, mock_principal, mock_calendar, mock_event

def test_add_single_event(mock_caldav):
    _, _, mock_calendar, _ = mock_caldav

    event = {
        "uid": "new-uid",
        "summary": "Test Event",
        "description": "This is a test",
        "start": datetime(2025, 12, 7, 10, 0),
        "end": datetime(2025, 12, 7, 11, 0),
    }

    cm = CalendarManager(event)
    cm.add_or_update_event()

    # Should call add_event once for the new event
    assert mock_calendar.add_event.call_count == 1

def test_update_existing_event(mock_caldav):
    _, _, mock_calendar, mock_event = mock_caldav

    event = {
        "uid": "existing-uid",  # matches the mocked existing event
        "summary": "Updated Event",
        "description": "Updated description",
        "start": datetime(2025, 12, 7, 12, 0),
        "end": datetime(2025, 12, 7, 13, 0),
    }

    cm = CalendarManager(event)
    cm.add_or_update_event()

    # Save should be called on the existing event
    mock_event.save.assert_called_once()
    # No new event should be added
    mock_calendar.add_event.assert_not_called()

def test_add_multiple_events(mock_caldav):
    _, _, mock_calendar, _ = mock_caldav

    events = [
        {
            "uid": "uid1",
            "summary": "Event 1",
            "description": "First event",
            "start": datetime(2025, 12, 7, 9, 0),
            "end": datetime(2025, 12, 7, 10, 0),
        },
        {
            "uid": "uid2",
            "summary": "Event 2",
            "description": "Second event",
            "start": datetime(2025, 12, 7, 10, 30),
            "end": datetime(2025, 12, 7, 11, 30),
        },
    ]

    cm = CalendarManager(events)
    cm.add_or_update_event()

    # Two new events should be added
    assert mock_calendar.add_event.call_count == 2

def test_add_or_update_accepts_single_dict(mock_caldav):
    _, _, mock_calendar, _ = mock_caldav

    event = {
        "uid": "uid-single",
        "summary": "Single Event",
        "description": "Just one",
        "start": datetime(2025, 12, 7, 14, 0),
        "end": datetime(2025, 12, 7, 15, 0),
    }

    cm = CalendarManager(event)
    # Should still work if a single dict is passed
    cm.add_or_update_event()

    assert mock_calendar.add_event.call_count == 1
