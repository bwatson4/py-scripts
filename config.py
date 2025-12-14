from pathlib import Path

# Directory that holds this config file
BASE_DIR = Path(__file__).resolve().parent

# Application folders
CACHE_DIR = BASE_DIR / "cache"
PDF_DIR = BASE_DIR / "pdfs"
LOG_DIR = BASE_DIR / "logs"

# App settings
# ENABLE_LOGGING = True
ENABLE_LOGGING = False

PAGE_URL = "https://kvapack.ca/adult-indoor/"
TEAM_NAME = "Chewblockas"
# KEYWORD = "tuesday night"
KEYWORD = "wednesday night"

# Ensure folders exist
for folder in (CACHE_DIR, PDF_DIR, LOG_DIR):
    folder.mkdir(parents=True, exist_ok=True)

 # File Setup
LOG_FILE = LOG_DIR / "cron_log.txt"

PDF_FILE = PDF_DIR / "schedule.pdf"
PDF_HASH_FILE = PDF_DIR / "schedule.hash"

#set to 12 hour if times are in 12 hour format and pm
#set to 24 hour if times are in 24 hour format, or times are known to be am
TIME_FORMAT = "12 Hour"  # or "24 Hour"


# iCloud credentials
ICLOUD_USERNAME = "watson.bm4@gmail.com"
ICLOUD_APP_PASSWORD = "xokj-olky-xpuc-xspw"
CALENDAR_INDEX = 1

# Email Notification Setup
from_email_addr = "raspberry44hugh@gmail.com"
from_email_pass = "lcyb kjcl uksd ltkg"
to_email_addr   = [
    "watson.bm4@gmail.com",
    "katiegregson8@gmail.com"
]

GYMS  = ["KCS", "TCC", "OLPH", "PACWAY", "VALLEYVIEW SS"]
POOLS = [f"{c} POOL" for c in "ABCDEFGH"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36"
    )
}