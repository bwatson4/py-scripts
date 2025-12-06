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
import smtplib
from email.message import EmailMessage

import config
from utils import log, to_24h_str

# ====== GET PDF URL ======
def get_wednesday_pdf_url(page_url=PAGE_URL, KEYWORD="Wednesday Night"):
    """Parse the Adult Indoor page to find the Wednesday Night PDF link."""
    resp = requests.get(page_url, headers=HEADERS)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Find any <h1> containing "Wednesday Night" in its text (ignoring nested tags)
    h1 = None
    for candidate in soup.find_all("h1"):
        if KEYWORD in candidate.get_text(strip=True).lower():
            h1 = candidate
            break

    if not h1:
        log(f"Could not find {KEYWORD} section on page.")
        return None

    # Look for the parent div with class 'fl-rich-text' that contains the PDF link
    parent_div = h1.find_parent("div", class_="fl-rich-text")
    if not parent_div:
        log("Could not find parent div containing PDF link.")
        return None

    # Find <a> link containing "Click Here"
    link = parent_div.find("a", string=re.compile("Click Here", re.I))
    if not link:
        log(f"Could not find PDF link in {KEYWORD} section.")
        return None

    pdf_url = urljoin(page_url, link["href"])
    return pdf_url


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

# ====== EMAIL ======
def send_email(events=None):
    msg = EmailMessage()

    # Determine body
    if events:
        event = events[0]
        body = (
            f"Event Summary: {event['summary']}\n"
            f"Details: {event['description']}\n\n"
            f"Start: {event['start'].strftime('%Y-%m-%d %H:%M')}\n"
            f"End:   {event['end'].strftime('%Y-%m-%d %H:%M')}\n"
        )
    else:
        body = extract_text(PDF_PATH)

    msg.set_content(body)
    msg["From"] = from_email_addr
    msg["To"] = to_email_addr
    msg["Subject"] = "KVA Schedule Updated"

    # attach PDF
    with open(PDF_PATH, "rb") as f:
        pdf_data = f.read()
    msg.add_attachment(pdf_data, maintype="application", subtype="pdf", filename=os.path.basename(PDF_PATH))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(from_email_addr, from_email_pass)
    server.send_message(msg)
    server.quit()

# ====== MAIN ======
def main():
    pdf_url = get_wednesday_pdf_url()
    if not pdf_url:
        return

    download_pdf(pdf_url)

    if not has_pdf_changed():
        return

    log(f"Schedule changed, sending email")

    text = extract_text()
    events = parse_schedule(text)

    if events:
        add_events_to_calendar(events)

    send_email(events if events else None)

if __name__ == "__main__":
    log("Script started")
    main()
