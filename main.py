from fetcher.pdf_fetcher import PDFFetcher
from parser.schedule_parser import ScheduleParser
from calendar.ical_client import ICloudCalendar
from notifier.emailer import Emailer
from utils import log

def main():
    log("Script started")

    fetcher = PDFFetcher()
    parser = ScheduleParser()
    calendar = ICloudCalendar()
    mailer = Emailer()

    url = fetcher.get_wednesday_pdf_url()
    if not url:
        log("No PDF URL found.")
        return

    fetcher.download_pdf(url)

    if not fetcher.has_changed():
        return

    log("Schedule changed — processing")

    text = fetcher.extract_text()
    events = parser.parse(text)

    if events:
        calendar.add_events(events)

    mailer.send(events if events else None)


if __name__ == "__main__":
    main()
