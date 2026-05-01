import re
import time
import requests
from datetime import date, datetime
from bs4 import BeautifulSoup
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

_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}


def _get_cached(key, fn):
    now = time.time()
    if key in _cache and _cache[key]['data'] and now - _cache[key]['ts'] < _CACHE_TTL:
        return _cache[key]['data']
    data = fn()
    if data:  # never cache empty — retry next request instead
        _cache[key] = {'data': data, 'ts': now}
    return data


# ── Standings ─────────────────────────────────────────────────────────────────

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
        if teams:
            db = PremierLeagueDB()
            if not db.standings_unchanged(teams):
                db.save_standings(teams)
            return teams
    except Exception as e:
        print(f"[Firecrawl] standings error: {e}")

    # BeautifulSoup fallback
    try:
        from test_scraper import scrape_premier_league_table as _bs
        return _bs()
    except Exception as e:
        print(f"[Fallback] standings error: {e}")
        return []


# ── Top Scorers ───────────────────────────────────────────────────────────────

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
        if scorers:
            return scorers[:20]
    except Exception as e:
        print(f"[Firecrawl] top scorers error: {e}")

    # BeautifulSoup fallback
    try:
        import scrapers as _bs
        return _bs._scrape_top_scorers()
    except Exception as e:
        print(f"[Fallback] top scorers error: {e}")
        return []


# ── Fixtures ──────────────────────────────────────────────────────────────────

def scrape_fixtures():
    return _get_cached('fixtures', _scrape_fixtures)

def _scrape_fixtures():
    # Firecrawl: scrape Sky Sports and parse markdown
    try:
        result = _fc.scrape(
            "https://www.skysports.com/premier-league-scores-fixtures",
            formats=["markdown"]
        )
        fixtures = _parse_sky_fixtures(result.markdown or '')
        if fixtures:
            return fixtures
    except Exception as e:
        print(f"[Firecrawl] fixtures error: {e}")

    # BeautifulSoup fallback: BBC Sport link text pattern
    return _scrape_fixtures_bs()

def _parse_sky_fixtures(markdown):
    fixtures = []
    current_date = ''
    for line in markdown.split('\n'):
        line = line.strip()
        m = re.match(r'^## (.+)$', line)
        if m:
            current_date = m.group(1).strip()
            continue
        m = re.match(r'^(.+?) vs (.+?)\. Kick-off at (.+)$', line)
        if m and current_date:
            home, away = m.group(1).strip(), m.group(2).strip()
            if home and away and home != away:
                fixtures.append({'home_team': home, 'away_team': away,
                                 'time': m.group(3).strip(), 'date': current_date})
    return fixtures[:20]

def _ordinal(n):
    s = ['th','st','nd','rd'] + ['th'] * 16
    return f"{n}{s[n % 20] if n % 100 not in range(11,14) else 'th'}"

def _scrape_fixtures_bs():
    """ESPN public API — no JS needed, returns upcoming EPL fixtures as JSON."""
    from datetime import timedelta
    today = date.today()
    end = today + timedelta(days=28)
    date_range = f"{today.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}"
    url = (f"https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/"
           f"scoreboard?dates={date_range}&limit=40")
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
    except Exception as e:
        print(f"[Fallback] fixtures ESPN error: {e}")
        return []

    fixtures = []
    for event in data.get('events', []):
        if event.get('status', {}).get('type', {}).get('state') != 'pre':
            continue
        comps = event.get('competitions', [{}])
        competitors = comps[0].get('competitors', []) if comps else []
        home = next((c for c in competitors if c.get('homeAway') == 'home'), None)
        away = next((c for c in competitors if c.get('homeAway') == 'away'), None)
        if not home or not away:
            continue

        home_name = home.get('team', {}).get('displayName', '')
        away_name = away.get('team', {}).get('displayName', '')

        raw_date = event.get('date', '')
        try:
            dt = datetime.strptime(raw_date, '%Y-%m-%dT%H:%MZ')
            day_str = f"{dt.strftime('%A')} {_ordinal(dt.day)} {dt.strftime('%B')}"
            time_str = dt.strftime('%I:%M %p').lstrip('0')
        except Exception:
            day_str, time_str = raw_date[:10], 'TBD'

        if home_name and away_name:
            fixtures.append({'home_team': home_name, 'away_team': away_name,
                             'time': time_str, 'date': day_str})

    return fixtures[:20]


# ── Results ───────────────────────────────────────────────────────────────────

def scrape_results():
    return _get_cached('results', _scrape_results)

def _scrape_results():
    today = date.today()
    if today.day <= 7:
        year = today.year - 1 if today.month == 1 else today.year
        month = 12 if today.month == 1 else today.month - 1
    else:
        year, month = today.year, today.month

    bbc_url = f"https://www.bbc.com/sport/football/premier-league/scores-fixtures/{year}-{month:02d}"

    # Firecrawl: scrape BBC Sport and parse markdown
    try:
        result = _fc.scrape(bbc_url, formats=["markdown"])
        results = _parse_bbc_results(result.markdown or '')
        if results:
            return results
    except Exception as e:
        print(f"[Firecrawl] results error: {e}")

    # BeautifulSoup fallback: same BBC page, same pattern in link text
    return _scrape_results_bs(bbc_url)

def _parse_bbc_results(markdown):
    results = []
    for m in re.finditer(r'\[(.+?) (\d+) , (.+?) (\d+) at Full time', markdown):
        home, away = m.group(1).strip(), m.group(3).strip()
        if home and away:
            results.append({'home_team': home, 'away_team': away,
                            'home_score': int(m.group(2)), 'away_score': int(m.group(4))})
    return results[:20]

def _scrape_results_bs(url):
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=10)
    except Exception:
        return []
    if resp.status_code != 200:
        return []

    soup = BeautifulSoup(resp.content, 'lxml')
    results = []

    # BBC Sport link text: "TeamA N , TeamB M at Full time"
    for link in soup.find_all('a'):
        text = link.get_text(separator=' ', strip=True)
        m = re.search(r'(.+?) (\d+) , (.+?) (\d+) at Full time', text)
        if not m:
            continue
        home, away = m.group(1).strip(), m.group(3).strip()
        if home and away:
            results.append({'home_team': home, 'away_team': away,
                            'home_score': int(m.group(2)), 'away_score': int(m.group(4))})

    # Deduplicate
    seen, unique = set(), []
    for r in results:
        key = (r['home_team'], r['away_team'])
        if key not in seen:
            seen.add(key)
            unique.append(r)

    return unique[:20]
