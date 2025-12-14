from src.fetcher import PDFFetcher
from src.parser import ScheduleParser
from src.calendar import CalendarManager
from src.emailer import EmailSender
from utils import log
from config import TEAM_NAME

def main():
    log("Script started")

    fetcher = PDFFetcher()
    calendar = CalendarManager()
    mailer = EmailSender()

    if not fetcher.fetch():
        log("No new PDF found")
        return
    
    log("New pdf, checking for new event details")
    parser = ScheduleParser(text=fetcher.text)
    event = parser.parse()

    if event:
        log("Adding/updating event in calendar")
        calendar.add_or_update_events(event)
    else:
        log(f"No events found for team {TEAM_NAME}")

    log("Sending email notification")
    mailer.send(event if event else None)


if __name__ == "__main__":
    main()
