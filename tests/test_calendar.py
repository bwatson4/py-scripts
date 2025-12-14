# tests/test_calendar.py
import pytest
from unittest.mock import MagicMock
from datetime import datetime
from src.calendar import CalendarManager


@pytest.fixture
def mock_calendar_with_existing_event():
    calendar = MagicMock()

    existing_event = MagicMock()
    existing_event.vobject_instance = MagicMock()
    existing_event.vobject_instance.vevent.uid.value = "existing-uid"
    existing_event.vobject_instance.vevent.valarms = []

    calendar.events.return_value = [existing_event]

    return calendar, existing_event


@pytest.fixture
def empty_mock_calendar():
    calendar = MagicMock()
    calendar.events.return_value = []
    return calendar


def test_add_new_event(empty_mock_calendar):
    cm = CalendarManager(client=MagicMock(), calendar=empty_mock_calendar)

    event = {
        "uid": "new-uid",
        "summary": "Test Event",
        "description": "This is a test",
        "start": datetime(2025, 12, 7, 10, 0),
        "end": datetime(2025, 12, 7, 11, 0),
    }

    cm.add_or_update_event(event)

    empty_mock_calendar.add_event.assert_called_once()


def test_update_existing_event(mock_calendar_with_existing_event):
    calendar, existing_event = mock_calendar_with_existing_event
    cm = CalendarManager(client=MagicMock(), calendar=calendar)

    event = {
        "uid": "existing-uid",
        "summary": "Updated Event",
        "description": "Updated description",
        "start": datetime(2025, 12, 7, 12, 0),
        "end": datetime(2025, 12, 7, 13, 0),
    }

    cm.add_or_update_event(event)

    existing_event.save.assert_called_once()
    calendar.add_event.assert_not_called()


def test_add_multiple_events(empty_mock_calendar):
    cm = CalendarManager(client=MagicMock(), calendar=empty_mock_calendar)

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

    cm.add_or_update_events(events)

    assert empty_mock_calendar.add_event.call_count == 2


def test_add_or_update_accepts_single_dict(empty_mock_calendar):
    cm = CalendarManager(client=MagicMock(), calendar=empty_mock_calendar)

    event = {
        "uid": "uid-single",
        "summary": "Single Event",
        "description": "Just one",
        "start": datetime(2025, 12, 7, 14, 0),
        "end": datetime(2025, 12, 7, 15, 0),
    }

    cm.add_or_update_events(event)

    empty_mock_calendar.add_event.assert_called_once()
