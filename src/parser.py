from config import TEAM_NAME, GYMS, POOLS, TIME_FORMAT
import re
from datetime import datetime


class ScheduleParser:
    def __init__(
        self,
        text,
        team_name=TEAM_NAME,
        gyms=GYMS,
        pools=POOLS,
    ):
        self.text = text  # keep original casing
        self.lines = self._normalize_lines(text)
        self.events = []

        self.team_name = team_name
        self.gyms = gyms
        self.pools = pools

        self.current_date = None
        self.current_gym = None
        self.current_pool = None
        self.uid = None

    def _normalize_lines(self, text):
        # keep original casing, just strip empty lines
        return [ln.strip() for ln in text.splitlines() if ln.strip()]

    def detect_date(self, line):
        date_match = re.search(r"([A-Z][a-z]+ \d{1,2}, \d{4})", line)
        if not date_match:
            return None

        try:
            self.current_date = datetime.strptime(date_match.group(1), "%B %d, %Y").date()
            self.uid = self.current_date.strftime("%Y%m%d")
            return True
        except ValueError:
            return None

    def detect_gym(self, line):
        for gym in self.gyms:
            if line.lower().startswith(gym.lower()):
                self.current_gym = gym  # preserve original casing
                return True
        return False

    def detect_pool(self, line):
        for pool in self.pools:
            if line.lower().startswith(pool.lower()):
                self.current_pool = pool  # preserve original casing
                return True
        return False

    def extract_block(self, start_index):
        block = []
        j = start_index + 1

        while j < len(self.lines):
            nxt = self.lines[j]

            # block ends when next pool, next gym, or next date starts
            if self.detect_pool(nxt) or self.detect_gym(nxt) or self.detect_date(nxt):
                break

            block.append(nxt)
            j += 1

        return block, j

    def extract_time(self, block_lines):
        time_pat = re.compile(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})")

        for ln in block_lines:
            m = time_pat.search(ln)
            if m:
                return m.group(1), m.group(2)
        return None, None

    def extract_teams(self, block_lines):
        teams = []
        time_pat = re.compile(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})")

        for ln in block_lines:
            m = re.match(r"^\s*(\d+)\s+(.*)$", ln)
            if m:
                name = m.group(2)
                name = time_pat.sub("", name)  # remove times
                name = re.sub(r"\s+", " ", name).strip()
                teams.append({
                    "num": m.group(1),
                    "name": name
                })
        return teams

    def parse(self):
        i = 0

        while i < len(self.lines):
            line = self.lines[i]

            # detect gym
            self.detect_gym(line)

            # detect date
            if self.detect_date(line):
                i += 1
                continue

            # detect pool
            if self.detect_pool(line):
                block, next_i = self.extract_block(i)

                start_raw, end_raw = self.extract_time(block)
                teams = self.extract_teams(block)

                # build events only if valid
                if start_raw and end_raw and self.current_date:
                    start_dt = datetime.strptime(
                        f"{self.current_date} {start_raw}",
                        "%Y-%m-%d %H:%M"
                    )
                    end_dt = datetime.strptime(
                        f"{self.current_date} {end_raw}",
                        "%Y-%m-%d %H:%M"
                    )

                    for t in teams:
                        if t["name"].lower() == self.team_name.lower():
                            self.events.append({
                                "uid": f"{self.uid}",
                                "summary": f"{self.team_name} Volleyball",
                                "description": f"Gym: {self.current_gym}, Pool: {self.current_pool}",
                                "start": start_dt,
                                "end": end_dt,
                            })

                i = next_i
                continue

            i += 1

        return self.events
