from src.fetcher import PDFFetcher
from src.parser import ScheduleParser
# from calendar.ical_client import ICloudCalendar
# from notifier.emailer import Emailer
from utils import log

def main():
    log("Script started")

    fetcher = PDFFetcher()
    # parser = ScheduleParser()
    # calendar = ICloudCalendar()
    # mailer = Emailer()

    if not fetcher.fetch():
        log("No new PDF found")
        return
    
    log(f"Schedule changed, sending email")
    
    print(fetcher.text)

    # events = parser.parse(text)

    # if events:
    #     calendar.add_events(events)

    # mailer.send(events if events else None)


if __name__ == "__main__":
    main()
