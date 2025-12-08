from config import LOG_FILE, ENABLE_LOGGING, TIME_FORMAT
from datetime import datetime

def log(msg):
    if ENABLE_LOGGING:
        with open(LOG_FILE, "a") as f:
            f.write(f"{datetime.now()}: {msg}\n")

def to_24h_str(tstr):
    if TIME_FORMAT == "12 hour":
        h, m = map(int, tstr.split(":"))
        if h < 12:
            h += 12
        return f"{h:02d}:{m:02d}"
    else:
        return tstr
    