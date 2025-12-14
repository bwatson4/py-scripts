from src.parser import ScheduleParser
from datetime import datetime
import pytest

# ----------------------------
# 1️⃣ Test: Initialization
# ----------------------------
def test_initialization():
    parser = ScheduleParser(
        text="""2025 KVA Co-Ed League
        Final Week of 2025 League
        Wednesday
        VALLEYVIEW SS* December 3, 2025
        A POOL- East Gym
        1 Watch my 6
        2 Parents Night Out
        3 Smash Or Pass 8:00-9:45
        4 All Sets Are Off
        5 Nice Tips
        """,
        team_name="Chewblockas",
        gyms=["KCS", "TCC", "OLPH", "PACWAY", "VALLEYVIEW SS"],
        pools=["A POOL", "B POOL", "C POOL", "D POOL", "E POOL", "F POOL", "G POOL", "H POOL"]
    )
    assert parser.team_name == "Chewblockas"
    assert parser.gyms == ["KCS", "TCC", "OLPH", "PACWAY", "VALLEYVIEW SS"]
    assert parser.pools == ["A POOL", "B POOL", "C POOL", "D POOL", "E POOL", "F POOL", "G POOL", "H POOL"]
    assert parser.current_date is None
    assert parser.current_gym is None
    assert parser.current_pool is None

# ----------------------------
# 2️⃣ Test: _normalize_lines
# ----------------------------
def test_normalize_lines():
    text = """
        2025 KVA Co-Ed League
        Final Week of 2025 League
        Wednesday
        VALLEYVIEW SS* December 3, 2025
        A POOL- East Gym
        1 Watch my 6
        3 Smash Or Pass 8:00-9:45
        """
    parser = ScheduleParser(text=text)
    normalized = parser._normalize_lines(text)
    assert normalized[0] == "2025 KVA Co-Ed League"
    assert normalized[1] == "Final Week of 2025 League"
    assert normalized[3] == "VALLEYVIEW SS* December 3, 2025"
    assert normalized[6] == "3 Smash Or Pass 8:00-9:45"

# ----------------------------
# 3️⃣ Test: parse (case-insensitive)
# ----------------------------
def test_parse_case_insensitive():
    text = """
        2025 KVA Co-Ed League
        Final Week of 2025 League
        Wednesday
        valleyview ss* December 3, 2025
        a pool- East Gym
        1 watch my 6
        3 Smash Or Pass 8:00-9:45
        """
    parser = ScheduleParser(
        text=text,
        team_name="WATCH MY 6",       # different case
        gyms=["VALLEYVIEW SS"],       # different case
        pools=["A POOL"]              # different case
    )
    events = parser.parse()
    
    assert len(events) == 1
    event = events[0]
    
    assert event["summary"] == "WATCH MY 6 Volleyball"
    assert event["description"] == "Gym: VALLEYVIEW SS, Pool: A POOL"
    assert event["start"] == datetime(2025, 12, 3, 20, 0)
    assert event["end"] == datetime(2025, 12, 3, 21, 45)
