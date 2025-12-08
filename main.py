from src.fetcher import PDFFetcher
from src.parser import ScheduleParser
from src.calendar import CalendarManager
# from notifier.emailer import Emailer
from utils import log

def main():
    log("Script started")

    fetcher = PDFFetcher()
    calendar = CalendarManager()
    # mailer = Emailer()

    if not fetcher.fetch():
        log("No new PDF found")
        return
    
    log(f"Schedule changed, sending email")
    parser = ScheduleParser(text=fetcher.text)
    event = parser.parse()
    

    if event:
        calendar.add_or_update_event(event)

    # mailer.send(events if events else None)


if __name__ == "__main__":
    main()
