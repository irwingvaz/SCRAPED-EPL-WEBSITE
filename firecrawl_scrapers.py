import os
import time
from typing import List
from pydantic import BaseModel
from firecrawl import FirecrawlApp
from database import PremierLeagueDB

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_fc = FirecrawlApp(api_key=os.environ.get('FIRECRAWL_API_KEY'))

_cache = {}
_CACHE_TTL = 3600  # 1 hour — data changes at most a few times per match day


def _get_cached(key, fn):
    now = time.time()
    if key in _cache and now - _cache[key]['ts'] < _CACHE_TTL:
        return _cache[key]['data']
    data = fn()
    _cache[key] = {'data': data, 'ts': now}
    return data


# ── Schemas ───────────────────────────────────────────────────────────────────

class TeamStanding(BaseModel):
    position: int
    team_name: str
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int

class StandingsPage(BaseModel):
    teams: List[TeamStanding]


class TopScorer(BaseModel):
    rank: int
    player_name: str
    team: str
    goals: int
    assists: int
    played: int

class TopScorersPage(BaseModel):
    scorers: List[TopScorer]


class Fixture(BaseModel):
    home_team: str
    away_team: str
    time: str
    date: str

class FixturesPage(BaseModel):
    fixtures: List[Fixture]


class MatchResult(BaseModel):
    home_team: str
    away_team: str
    home_score: int
    away_score: int

class ResultsPage(BaseModel):
    results: List[MatchResult]


# ── Standings ─────────────────────────────────────────────────────────────────

def scrape_premier_league_table():
    return _get_cached('standings', _scrape_standings)

def _scrape_standings():
    try:
        result = _fc.scrape_url(
            "https://www.bbc.com/sport/football/premier-league/table",
            formats=["extract"],
            extract={"schema": StandingsPage.model_json_schema()}
        )
        teams = (result.extract or {}).get('teams', [])
    except Exception as e:
        print(f"[Firecrawl] standings error: {e}")
        return []

    if not teams:
        return []

    db = PremierLeagueDB()
    if not db.standings_unchanged(teams):
        db.save_standings(teams)

    return teams


# ── Top Scorers ───────────────────────────────────────────────────────────────

def scrape_top_scorers():
    return _get_cached('top_scorers', _scrape_top_scorers)

def _scrape_top_scorers():
    try:
        result = _fc.scrape_url(
            "https://www.bbc.com/sport/football/premier-league/top-scorers",
            formats=["extract"],
            extract={"schema": TopScorersPage.model_json_schema()}
        )
        scorers = (result.extract or {}).get('scorers', [])
    except Exception as e:
        print(f"[Firecrawl] top scorers error: {e}")
        return []

    return scorers[:20]


# ── Fixtures ──────────────────────────────────────────────────────────────────

def scrape_fixtures():
    return _get_cached('fixtures', _scrape_fixtures)

def _scrape_fixtures():
    try:
        result = _fc.scrape_url(
            "https://www.bbc.com/sport/football/premier-league/scores-fixtures",
            formats=["extract"],
            extract={
                "schema": FixturesPage.model_json_schema(),
                "systemPrompt": (
                    "Extract only upcoming Premier League fixtures that have not been played yet. "
                    "Do not include completed matches with scores. "
                    "Include the match date (e.g. 'Saturday 3rd May') and kick-off time in 12-hour format (e.g. '3:00 PM')."
                )
            }
        )
        fixtures = (result.extract or {}).get('fixtures', [])
    except Exception as e:
        print(f"[Firecrawl] fixtures error: {e}")
        return []

    return fixtures[:20]


# ── Results ───────────────────────────────────────────────────────────────────

def scrape_results():
    return _get_cached('results', _scrape_results)

def _scrape_results():
    try:
        result = _fc.scrape_url(
            "https://www.skysports.com/premier-league-results",
            formats=["extract"],
            extract={
                "schema": ResultsPage.model_json_schema(),
                "systemPrompt": (
                    "Extract recent Premier League match results. "
                    "Only include fully completed matches with final numeric scores. "
                    "Use the full team name as it appears on the page."
                )
            }
        )
        results = (result.extract or {}).get('results', [])
    except Exception as e:
        print(f"[Firecrawl] results error: {e}")
        return []

    return results[:20]
