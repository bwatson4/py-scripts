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
import io
from bs4 import BeautifulSoup
from urllib.parse import urljoin

#for email
import smtplib
from email.message import EmailMessage


with open("/home/brysen/projects/myscripts/cron_log.txt", "a") as f:
    f.write(f"Script started at {datetime.now()}\n")

# ====== CONFIGURATION ======
PAGE_URL = "https://kvapack.ca/adult-indoor/"
TEAM_NAME = "Chewblockas"

# iCloud credentials
ICLOUD_USERNAME = "watson.bm4@gmail.com"
ICLOUD_APP_PASSWORD = "xokj-olky-xpuc-xspw"
CALENDAR_INDEX = 1

# Email Notification Setup
from_email_addr ="raspberry44hugh@gmail.com"
from_email_pass = "lcyb kjcl uksd ltkg"
to_email_addr   ="watson.bm4@gmail.com"

PDF_PATH  = "/home/brysen/projects/myscripts/schedule.pdf"
HASH_PATH = "/home/brysen/projects/myscripts/schedule.hash"

GYMS  = ["KCS", "TCC", "OLPH", "PACWAY"]
POOLS = [f"{c} POOL" for c in "ABCDEFGH"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36"
    )
}

# ====== DISCOVER SCHEDULE PDF BY CONTENT ======
def discover_wednesday_pdf(page_url=PAGE_URL):
    """
    Attempts the following in order:
    1. Find PDF containing BOTH 'wednesday' and 'chewblockas'
    2. If none found, find PDF containing 'wednesday schedule will be posted on'
    3. Otherwise return None
    """

    resp = requests.get(page_url, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    pdf_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if ".pdf" in href.lower():
            pdf_links.append(urljoin(page_url, href))

    # Terms required for STRONG match
    strong_terms = ["wednesday", "chewblockas"]

    # Fallback phrase
    fallback_phrase = "wednesday schedule will be posted on"

    strong_matches = []
    fallback_matches = []

    for pdf_url in pdf_links:
        try:
            r = requests.get(pdf_url, headers=HEADERS)
            r.raise_for_status()

            with pdfplumber.open(io.BytesIO(r.content)) as pdf:
                text = "\n".join(
                    (page.extract_text() or "") for page in pdf.pages
                ).lower()

            # Check strong match: BOTH terms required
            if all(term in text for term in strong_terms):
                strong_matches.append(pdf_url)

            # Check fallback match
            if fallback_phrase in text:
                fallback_matches.append(pdf_url)

        except Exception as e:
            with open("/home/brysen/projects/myscripts/cron_log.txt", "a") as f:
                f.write(f"Error scanning PDF {pdf_url}: {e}\n")

    # Priority #1 — strong match
    if strong_matches:
        return strong_matches[0]

    # Priority #2 — fallback match
    if fallback_matches:
        return fallback_matches[0]

    # No match
    return None



# ====== UTILITIES ======
def to_24h_str(tstr):
    h, m = map(int, tstr.split(":"))
    if h < 12:
        h += 12
    return f"{h:02d}:{m:02d}"

def download_pdf(url, path=PDF_PATH):
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
            text += (page.extract_text() or "") + "\n"
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

        # detect gym
        for gym in GYMS:
            if line.startswith(gym):
                current_gym = gym
                break

        # detect date
        date_match = re.search(r"([A-Z][a-z]+ \d{1,2}, \d{4})", line)
        if date_match:
            try:
                current_date = datetime.strptime(date_match.group(1), "%B %d, %Y").date()
            except:
                current_date = None
            i += 1
            continue

        # detect pool section
        pool_found = None
        for pool in POOLS:
            if line.startswith(pool):
                pool_found = pool
                break

        if pool_found:
            current_pool = pool_found
            block_lines = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if any(nxt.startswith(x) for x in POOLS + GYMS) or \
                   re.search(r"[A-Z][a-z]+ \d{1,2}, 2025", nxt):
                    break
                block_lines.append(nxt)
                j += 1

            # extract time
            time_pat = re.compile(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})")
            pool_time = None
            for bl in block_lines:
                m = time_pat.search(bl)
                if m:
                    pool_time = f"{m.group(1)}-{m.group(2)}"
                    break

            # extract teams
            teams = []
            for bl in block_lines:
                m = re.match(r"^\s*(\d+)\s+(.*)$", bl)
                if m:
                    name_part = m.group(2)
                    name_part = time_pat.sub("", name_part).strip()
                    name_part = re.sub(r"\s+", " ", name_part)
                    teams.append({"num": m.group(1), "name": name_part})

            # build event
            if pool_time and current_date:
                start_raw, end_raw = pool_time.split("-")
                start_dt = datetime.strptime(f"{current_date} {to_24h_str(start_raw)}", "%Y-%m-%d %H:%M")
                end_dt   = datetime.strptime(f"{current_date} {to_24h_str(end_raw)}", "%Y-%m-%d %H:%M")

                for t in teams:
                    if t["name"].lower() == team_name.lower():
                        events.append({
                            "summary": f"{team_name} Volleyball",
                            "description": f"Gym: {current_gym}, Pool: {current_pool}",
                            "start": start_dt,
                            "end":   end_dt
                        })

            i = j
            continue

        i += 1

    return events


# ====== CALDAV / ICLOUD ======
def add_events_to_calendar(events):
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
        ev  = Event()
        ev.add("summary", e["summary"])
        ev.add("dtstart", e["start"])
        ev.add("dtend", e["end"])
        ev.add("description", e["description"])
        ev.add("uid", str(uuid.uuid4()))

        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("description", f"Upcoming: {e['summary']}")
        alarm.add("trigger", timedelta(minutes=-30))
        ev.add_component(alarm)

        cal.add_component(ev)
        calendar.add_event(cal.to_ical())


def send_email(events):
    msg = EmailMessage()
    event = events[0]

    summary = event['summary']
    description = event['description']
    start_time = event['start'].strftime("%Y-%m-%d %H:%M")
    end_time   = event['end'].strftime("%Y-%m-%d %H:%M")

    msg.set_content(
        f"Event Summary: {summary}\n"
        f"Details: {description}\n\n"
        f"Start: {start_time}\n"
        f"End:   {end_time}"
    )

    msg["From"] = from_email_addr
    msg["To"]   = to_email_addr
    msg["Subject"] = "KVA Schedule Updated"

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(from_email_addr, from_email_pass)
    server.send_message(msg)
    server.quit()


# ====== MAIN ======
def main():
    pdf_url = discover_wednesday_pdf()

    if not pdf_url:
        return
    # print(f"found wednesday pdf: {pdf_url}")
    download_pdf(pdf_url)

    if not has_pdf_changed():
        return

    with open("/home/brysen/projects/myscripts/cron_log.txt", "a") as f:
        f.write(f"Schedule changed at {datetime.now()}\n")

    text = extract_text()
    events = parse_schedule(text)

    if events:
        add_events_to_calendar(events)
        send_email(events)


if __name__ == "__main__":
    main()
