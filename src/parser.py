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
        self.text = text
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
        return [ln.strip() for ln in text.splitlines() if ln.strip()]

    def detect_date(self, line):
        date_match = re.search(r"([A-Z][a-z]+ \d{1,2}, \d{4})", line)
        if not date_match:
            return None

        try:
            self.current_date = datetime.strptime(
                date_match.group(1), "%B %d, %Y"
            ).date()
            self.uid = self.current_date.strftime("%Y%m%d")
            return True
        except ValueError:
            return None

    def detect_gym(self, line):
        for gym in self.gyms:
            if line.lower().startswith(gym.lower()):
                self.current_gym = gym
                return True
        return False

    def detect_pool(self, line):
        for pool in self.pools:
            if line.lower().startswith(pool.lower()):
                self.current_pool = pool
                return True
        return False

    def extract_block(self, start_index):
        block = []
        j = start_index + 1

        while j < len(self.lines):
            nxt = self.lines[j]

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
                name = time_pat.sub("", name)
                name = re.sub(r"\s+", " ", name).strip()
                teams.append({
                    "num": m.group(1),
                    "name": name
                })
        return teams

    @staticmethod
    def _pm_to_24h(tstr: str) -> str:
        """
        Convert a PM time like '6:30' to '18:30'.
        Assumes input is always PM.
        """
        hour, minute = map(int, tstr.split(":"))
        if TIME_FORMAT.lower() == "12 hour":
            if hour != 12:
                hour += 12
        return f"{hour:02d}:{minute:02d}"

    def parse(self):
        i = 0

        while i < len(self.lines):
            line = self.lines[i]

            self.detect_gym(line)

            if self.detect_date(line):
                i += 1
                continue

            if self.detect_pool(line):
                pool_for_block = self.current_pool  # capture the pool here
                block, next_i = self.extract_block(i)

                start_raw, end_raw = self.extract_time(block)
                teams = self.extract_teams(block)

                if start_raw and end_raw and self.current_date:
                    start_24 = self._pm_to_24h(start_raw)
                    end_24 = self._pm_to_24h(end_raw)

                    start_dt = datetime.strptime(
                        f"{self.current_date} {start_24}",
                        "%Y-%m-%d %H:%M"
                    )
                    end_dt = datetime.strptime(
                        f"{self.current_date} {end_24}",
                        "%Y-%m-%d %H:%M"
                    )

                    for t in teams:
                        if t["name"].lower() == self.team_name.lower():
                            self.events.append({
                                "uid": self.uid,
                                "summary": f"{self.team_name} Volleyball",
                                "description": (
                                    f"Gym: {self.current_gym}, "
                                    f"Pool: {pool_for_block}"  # use captured pool
                                ),
                                "start": start_dt,
                                "end": end_dt,
                            })

                i = next_i
                continue

            i += 1

        return self.events
