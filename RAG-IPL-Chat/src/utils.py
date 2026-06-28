"""
Utility functions for IPL match data processing.
"""

TEAM_ABBREV_MAP = {
    "Kolkata Knight Riders": "KKR",
    "Royal Challengers Bangalore": "RCB",
    "Royal Challengers Bengaluru": "RCB",
    "Chennai Super Kings": "CSK",
    "Mumbai Indians": "MI",
    "Rajasthan Royals": "RR",
    "Kings XI Punjab": "KXIP",
    "Punjab Kings": "PBKS",
    "Delhi Daredevils": "DD",
    "Delhi Capitals": "DC",
    "Deccan Chargers": "DC",
    "Sunrisers Hyderabad": "SRH",
    "Pune Warriors": "PWI",
    "Kochi Tuskers Kerala": "KTK",
    "Gujarat Lions": "GL",
    "Rising Pune Supergiant": "RPS",
    "Rising Pune Supergiants": "RPS",
    "Lucknow Super Giants": "LSG",
    "Gujarat Titans": "GT",
}

SEASON_YEAR_MAP = {
    "2007/08": "2008",
    "2009/10": "2010",
    "2020/21": "2020",
}


def get_season_year(season_str: str) -> str:
    """Normalize season string to a 4-digit year."""
    season_str = str(season_str)
    return SEASON_YEAR_MAP.get(season_str, season_str)


def get_team_abbr(team_name: str) -> str:
    """Return the abbreviation for a team name."""
    if team_name in TEAM_ABBREV_MAP:
        return TEAM_ABBREV_MAP[team_name]
    # Fallback to initials
    words = team_name.replace("Supergiant", "Super giant").split()
    return "".join(word[0].upper() for word in words if word[0].isalnum())


def get_ordinal(n: int) -> str:
    """Return the ordinal string for a number (e.g. 1 -> '1st')."""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def calculate_overs(overs_list: list) -> float:
    """Calculate the number of overs bowled from a list of over objects."""
    if not overs_list:
        return 0.0
    last_over = overs_list[-1]
    over_num = last_over.get("over", 0)
    legal_balls = 0
    for d in last_over.get("deliveries", []):
        extras = d.get("extras", {})
        if "wides" not in extras and "noballs" not in extras:
            legal_balls += 1
    if legal_balls >= 6:
        return float(over_num + 1)
    return over_num + (legal_balls / 10.0)


def get_sort_key(item: tuple) -> tuple:
    """Return a sort key (date, match_number, filename) for a match tuple."""
    filepath, data = item
    info = data.get("info", {})
    dates = info.get("dates", [])
    date_str = dates[0] if dates else "9999-12-31"

    event = info.get("event", {})
    match_num = event.get("match_number", 999)
    if isinstance(match_num, str):
        lower = match_num.lower()
        if "final" in lower:
            match_num_val = 200
        elif "semi" in lower:
            match_num_val = 190
        elif "qualifier" in lower:
            match_num_val = 180
        elif "eliminator" in lower:
            match_num_val = 175
        else:
            match_num_val = 150
    else:
        match_num_val = int(match_num) if match_num is not None else 999

    filename = filepath.split("/")[-1]
    return (date_str, match_num_val, filename)
