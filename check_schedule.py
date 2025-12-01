#!/usr/bin/env python3


# check_schedule.py
import os
import hashlib
import re
from datetime import datetime, timedelta
import requests
import pdfplumber
from caldav import DAVClient
from icalendar import Calendar, Event, Alarm
import uuid

#for email
import smtplib
from email.message import EmailMessage


with open("/home/brysen/projects/myscripts/cron_log.txt", "a") as f:
    f.write(f"Script started at {datetime.now()}\n")

# ====== CONFIGURATION ======
PDF_URL = "https://kvapack.ca/wp-content/uploads/sites/3620/2025/11/Adult-Indoor-Schedule-2025_2026-Website-Schedule-43.pdf"
TEAM_NAME = "Chewblockas"

# iCloud credentials
ICLOUD_USERNAME = "watson.bm4@gmail.com"
ICLOUD_APP_PASSWORD = "xokj-olky-xpuc-xspw"
CALENDAR_INDEX = 1

# Email Notification Setup
#Set the sender email and password and recipient emaiç
from_email_addr ="raspberry44hugh@gmail.com"
from_email_pass = "lcyb kjcl uksd ltkg"
to_email_addr ="watson.bm4@gmail.com"

PDF_PATH = "/home/brysen/projects/myscripts/schedule.pdf"
HASH_PATH = "/home/brysen/projects/myscripts/schedule.hash"

GYMS = ["KCS", "TCC", "OLPH", "PACWAY"]
POOLS = [f"{c} POOL" for c in "ABCDEFGH"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36"
    )
}

# ====== UTILITIES ======
def to_24h_str(tstr):
    """Convert hh:mm (12-hour PM) to HH:MM 24-hour string."""
    h, m = map(int, tstr.split(":"))
    if h < 12:
        h += 12
    return f"{h:02d}:{m:02d}"

def download_pdf(url=PDF_URL, path=PDF_PATH):
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    with open(path, "wb") as fh:
        fh.write(resp.content)
    return path

def has_pdf_changed(path=PDF_PATH, hash_path=HASH_PATH):
    if not os.path.exists(path):
        return True
    with open(path, "rb") as fh:
        new_hash = hashlib.md5(fh.read()).hexdigest()
    old_hash = None
    if os.path.exists(hash_path):
        with open(hash_path, "r") as fh:
            old_hash = fh.read().strip()
    if new_hash == old_hash:
        return False
    with open(hash_path, "w") as fh:
        fh.write(new_hash)
    return True

def extract_text(pdf_path=PDF_PATH):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
    return text

# ====== PARSING ======
def parse_schedule(text, team_name=TEAM_NAME):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    events = []
    current_date = None
    current_gym = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect gym
        for gym in GYMS:
            if line.startswith(gym):
                current_gym = gym
                break

        # Detect date
        date_match = re.search(r"([A-Z][a-z]+ \d{1,2}, \d{4})", line)
        if date_match:
            try:
                current_date = datetime.strptime(date_match.group(1), "%B %d, %Y").date()
            except:
                current_date = None
            i += 1
            continue

        # Detect pool header
        pool_found = None
        for pool in POOLS:
            if line.startswith(pool):
                pool_found = pool
                break

        if pool_found:
            current_pool = pool_found

            # Collect entire block until next pool/gym/date
            block_lines = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if any(nxt.startswith(x) for x in POOLS + GYMS) or re.search(r"[A-Z][a-z]+ \d{1,2}, 2025", nxt):
                    break
                block_lines.append(nxt)
                j += 1

            # Extract pool time
            time_pattern = re.compile(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})")
            pool_time = None
            for bl in block_lines:
                m = time_pattern.search(bl)
                if m:
                    pool_time = f"{m.group(1)}-{m.group(2)}"
                    break

            # Extract teams
            team_pattern = re.compile(r"^\s*(\d+)\s+(.*)$")
            teams = []
            for bl in block_lines:
                m = team_pattern.match(bl)
                if m:
                    name_part = m.group(2)
                    name_part = time_pattern.sub("", name_part).strip()
                    name_part = re.sub(r"\s+", " ", name_part)
                    teams.append({"num": m.group(1), "name": name_part})

            # Build events
            if pool_time and current_date:
                start_raw, end_raw = pool_time.split("-")
                start_dt = datetime.strptime(f"{current_date} {to_24h_str(start_raw)}", "%Y-%m-%d %H:%M")
                end_dt = datetime.strptime(f"{current_date} {to_24h_str(end_raw)}", "%Y-%m-%d %H:%M")

                for t in teams:
                    if t["name"].lower() == team_name.lower():
                        events.append({
                            "summary": f"{team_name} Volleyball",
                            "description": f"Gym: {current_gym}, Pool: {current_pool}",
                            "start": start_dt,
                            "end": end_dt
                        })

            i = j
            continue

        i += 1

    return events

# ====== CALDAV / ICLOUD ======
def add_events_to_calendar(events):
    """Add events with a 30-min VALARM and unique UID to avoid duplicates."""
    client = DAVClient(
        url="https://caldav.icloud.com/",
        username=ICLOUD_USERNAME,
        password=ICLOUD_APP_PASSWORD
    )
    principal = client.principal()
    calendars = principal.calendars()
    calendar = calendars[CALENDAR_INDEX]

    for e in events:
        cal = Calendar()
        ical_event = Event()
        ical_event.add("summary", e["summary"])
        ical_event.add("dtstart", e["start"])
        ical_event.add("dtend", e["end"])
        ical_event.add("description", e["description"])
        ical_event.add("uid", str(uuid.uuid4()))  # unique UID

        # Add 30-minute reminder
        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("description", f"Upcoming: {e['summary']}")
        alarm.add("trigger", timedelta(minutes=-30))
        ical_event.add_component(alarm)

        cal.add_component(ical_event)
        calendar.add_event(cal.to_ical())


def send_email(events, **kwargs):
    """Send an email with details about the events"""
    # Create a message object
    msg = EmailMessage()
    event = events[0]

    summary = event['summary']
    description = event['description']
    start_time = event['start'].strftime("%Y-%m-%d %H:%M")
    end_time = event['end'].strftime("%Y-%m-%d %H:%M")

    # Set the email body
    body = f"""
        Event Summary: {summary}
        Details: {description}

        Start: {start_time}
        End:   {end_time}
    """
    msg.set_content(body)

    # Set sender and recipient
    msg['From'] = from_email_addr
    msg['To'] = to_email_addr

    # Set your email subject
    msg['Subject'] = 'KVA Schedule Updated'

    # Connecting to server and sending email
    # Edit the following line with your provider's SMTP server details
    server = smtplib.SMTP('smtp.gmail.com', 587)

    # Comment out the next line if your email provider doesn't use TLS
    server.starttls()
    # Login to the SMTP server
    server.login(from_email_addr, from_email_pass)

    # Send the message
    server.send_message(msg)

    # print('Email sent')
    #Disconnect from the Server
    server.quit()

# ====== MAIN ======
def main():
    download_pdf()
    if not has_pdf_changed():
        return
    with open("/home/brysen/projects/myscripts/cron_log.txt", "a") as f:
        f.write(f"pdf changed at {datetime.now()}\n")
    text = extract_text()
    events = parse_schedule(text)
    if events:
        add_events_to_calendar(events)
        send_email(events)
        
if __name__ == "__main__":
    main()
