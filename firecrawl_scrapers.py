import re
import time
from datetime import date
from firecrawl import Firecrawl
from database import PremierLeagueDB

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_fc = Firecrawl()  # reads FIRECRAWL_API_KEY from env

_cache = {}
_CACHE_TTL = 3600  # 1 hour


def _get_cached(key, fn):
    now = time.time()
    if key in _cache and _cache[key]['data'] and now - _cache[key]['ts'] < _CACHE_TTL:
        return _cache[key]['data']
    data = fn()
    if data:  # never cache empty — retry next request instead
        _cache[key] = {'data': data, 'ts': now}
    return data


# ── Standings (extract — LLM handles the table well) ─────────────────────────

_STANDINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "teams": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "position":        {"type": "integer"},
                    "team_name":       {"type": "string"},
                    "played":          {"type": "integer"},
                    "wins":            {"type": "integer"},
                    "draws":           {"type": "integer"},
                    "losses":          {"type": "integer"},
                    "goals_for":       {"type": "integer"},
                    "goals_against":   {"type": "integer"},
                    "goal_difference": {"type": "integer"},
                    "points":          {"type": "integer"},
                },
                "required": ["position", "team_name", "played", "wins", "draws",
                             "losses", "goals_for", "goals_against", "goal_difference", "points"]
            }
        }
    }
}

def scrape_premier_league_table():
    return _get_cached('standings', _scrape_standings)

def _scrape_standings():
    try:
        result = _fc.extract(
            urls=["https://www.bbc.com/sport/football/premier-league/table"],
            prompt="Extract the full Premier League standings table with all 20 teams and all their stats.",
            schema=_STANDINGS_SCHEMA
        )
        teams = (result.data or {}).get('teams', [])
    except Exception as e:
        print(f"[Firecrawl] standings error: {e}")
        return []

    if not teams:
        return []

    db = PremierLeagueDB()
    if not db.standings_unchanged(teams):
        db.save_standings(teams)

    return teams


# ── Top Scorers (extract — table data, LLM handles well) ─────────────────────

_SCORERS_SCHEMA = {
    "type": "object",
    "properties": {
        "scorers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rank":        {"type": "integer"},
                    "player_name": {"type": "string"},
                    "team":        {"type": "string"},
                    "goals":       {"type": "integer"},
                    "assists":     {"type": "integer"},
                    "played":      {"type": "integer"},
                },
                "required": ["rank", "player_name", "team", "goals", "assists", "played"]
            }
        }
    }
}

def scrape_top_scorers():
    return _get_cached('top_scorers', _scrape_top_scorers)

def _scrape_top_scorers():
    try:
        result = _fc.extract(
            urls=["https://www.bbc.com/sport/football/premier-league/top-scorers"],
            prompt="Extract the top Premier League goal scorers with their rank, name, team, goals, assists and games played.",
            schema=_SCORERS_SCHEMA
        )
        scorers = (result.data or {}).get('scorers', [])
    except Exception as e:
        print(f"[Firecrawl] top scorers error: {e}")
        return []

    return scorers[:20]


# ── Fixtures (scrape + parse — Sky Sports markdown is clean) ─────────────────

def scrape_fixtures():
    return _get_cached('fixtures', _scrape_fixtures)

def _scrape_fixtures():
    try:
        result = _fc.scrape(
            "https://www.skysports.com/premier-league-scores-fixtures",
            formats=["markdown"]
        )
        markdown = result.markdown or ''
    except Exception as e:
        print(f"[Firecrawl] fixtures scrape error: {e}")
        return []

    fixtures = []
    current_date = ''

    for line in markdown.split('\n'):
        line = line.strip()
        # Date header: ## Friday 1st May
        date_match = re.match(r'^## (.+)$', line)
        if date_match:
            current_date = date_match.group(1).strip()
            continue
        # Fixture line: TeamA vs TeamB. Kick-off at TIME
        fixture_match = re.match(r'^(.+?) vs (.+?)\. Kick-off at (.+)$', line)
        if fixture_match and current_date:
            home = fixture_match.group(1).strip()
            away = fixture_match.group(2).strip()
            if home and away and home != away:
                fixtures.append({
                    'home_team': home,
                    'away_team': away,
                    'time': fixture_match.group(3).strip(),
                    'date': current_date,
                })

    return fixtures[:20]


# ── Results (scrape + parse — BBC Sport markdown has clean score pattern) ─────

def scrape_results():
    return _get_cached('results', _scrape_results)

def _scrape_results():
    today = date.today()
    # Early in the month means no results yet — use previous month
    if today.day <= 7:
        year = today.year - 1 if today.month == 1 else today.year
        month = 12 if today.month == 1 else today.month - 1
    else:
        year, month = today.year, today.month

    url = f"https://www.bbc.com/sport/football/premier-league/scores-fixtures/{year}-{month:02d}"

    try:
        result = _fc.scrape(url, formats=["markdown"])
        markdown = result.markdown or ''
    except Exception as e:
        print(f"[Firecrawl] results scrape error: {e}")
        return []

    # BBC Sport pattern: [TeamA N , TeamB M at Full time
    results = []
    for match in re.finditer(
        r'\[(.+?) (\d+) , (.+?) (\d+) at Full time', markdown
    ):
        home = match.group(1).strip()
        away = match.group(3).strip()
        if not home or not away:
            continue
        results.append({
            'home_team': home,
            'away_team': away,
            'home_score': int(match.group(2)),
            'away_score': int(match.group(4)),
        })

    return results[:20]
