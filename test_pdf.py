# test_pdf.py
from check_schedule import download_pdf, extract_text, parse_schedule

download_pdf()

text = extract_text()
with open("schedule_debug.txt", "w", encoding="utf-8") as f:
    f.write(text)

events = parse_schedule(text)

print(f"Found {len(events)} events:")
for e in events:
    print(f"{e['summary']} | {e['description']} | {e['start']} - {e['end']}")
