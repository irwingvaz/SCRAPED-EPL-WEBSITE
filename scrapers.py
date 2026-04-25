import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def scrape_top_scorers():
    """Scrape Premier League top scorers from BBC Sport."""
    url = "https://www.bbc.com/sport/football/premier-league/top-scorers"

    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch top scorers: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'lxml')
    table = soup.find('table')

    if not table:
        print("Could not find top scorers table")
        return []

    scorers = []
    tbody = table.find('tbody')
    if not tbody:
        return []

    rows = tbody.find_all('tr')

    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 7:
            name_cell = cells[1]

            # Find the player name element by its specific class
            player_name_elem = name_cell.find(class_=lambda c: c and 'PlayerName' in c)
            if player_name_elem:
                player_name = player_name_elem.get_text(strip=True)
            else:
                # Fallback: extract from text before team name
                player_name = cells[1].text.strip()[:20]

            # Find team name element by its specific class
            team_elem = name_cell.find(class_=lambda c: c and 'TeamsSummary' in c)
            if team_elem:
                team = team_elem.get_text(strip=True)
            else:
                # Fallback: get from badge
                badge = row.find(attrs={'data-testid': lambda x: x and 'badge-container' in x if x else False})
                team = badge.get('data-testid', '').replace('badge-container-', '').replace('-', ' ').title() if badge else ''

            scorers.append({
                'rank': int(cells[0].text.strip()),
                'player_name': player_name,
                'team': team,
                'goals': int(cells[2].text.strip()),
                'assists': int(cells[4].text.strip()),
                'played': int(cells[6].text.strip()),
            })

    return scorers[:20]  # Return top 20


def scrape_fixtures():
    """Scrape upcoming Premier League fixtures from BBC Sport."""
    import re
    from datetime import datetime

    url = "https://www.bbc.com/sport/football/premier-league/scores-fixtures"

    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch fixtures: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'lxml')
    fixtures = []

    # Find all H2 date headers and their associated fixtures
    current_date = ""

    # Iterate through elements to track current date context
    for elem in soup.find_all(['h2', 'li']):
        if elem.name == 'h2':
            # This is a date header like "Friday 6th February"
            date_text = elem.get_text(strip=True)
            # Check if it looks like a date
            if any(day in date_text for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']):
                current_date = date_text
            continue

        # This is an li element - check if it's a fixture
        text = elem.get_text()
        if 'versus' not in text.lower():
            continue

        # Skip results (matches with scores)
        if re.search(r'(\d+)\s*-\s*(\d+)', text):
            continue

        spans = elem.find_all('span')
        span_texts = [s.get_text(strip=True) for s in spans if s.get_text(strip=True)]

        if len(span_texts) < 7:
            continue

        time_elem = elem.find('time')
        time_24h = time_elem.get_text(strip=True) if time_elem else ''

        # Convert 24h to 12h format
        time_12h = time_24h
        if time_24h and ':' in time_24h:
            try:
                t = datetime.strptime(time_24h, '%H:%M')
                time_12h = t.strftime('%I:%M %p').lstrip('0')
            except:
                pass

        home_team = span_texts[2] if len(span_texts) > 2 else ''
        away_team = span_texts[7] if len(span_texts) > 7 else span_texts[-1] if span_texts else ''

        if not home_team or not away_team or home_team == away_team:
            continue

        fixtures.append({
            'home_team': home_team,
            'away_team': away_team,
            'time': time_12h,
            'date': current_date
        })

    # Remove duplicates
    seen = set()
    unique_fixtures = []
    for f in fixtures:
        key = (f['home_team'], f['away_team'])
        if key not in seen:
            seen.add(key)
            unique_fixtures.append(f)

    return unique_fixtures[:20]


def scrape_results():
    """Scrape recent Premier League results from Sky Sports."""
    import json

    # Current Premier League teams (2025/26 season)
    PL_TEAMS = {
        'arsenal', 'aston villa', 'bournemouth', 'afc bournemouth', 'brentford',
        'brighton', 'brighton & hove albion', 'brighton and hove albion',
        'chelsea', 'crystal palace', 'everton', 'fulham',
        'ipswich', 'ipswich town', 'leeds', 'leeds united',
        'leicester', 'leicester city', 'liverpool',
        'manchester city', 'manchester united', 'man city', 'man utd',
        'newcastle', 'newcastle united',
        'nottingham forest', 'nottm forest',
        'southampton', 'tottenham', 'tottenham hotspur', 'spurs',
        'west ham', 'west ham united', 'wolves', 'wolverhampton', 'wolverhampton wanderers'
    }

    url = "https://www.skysports.com/premier-league-results"

    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch results: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'lxml')

    results = []

    # Find match elements with JSON data
    matches = soup.find_all(class_='ui-sport-match-score')

    for match in matches:
        data_state = match.get('data-state')
        if not data_state:
            continue

        try:
            data = json.loads(data_state)

            # Only include completed matches
            if not data.get('isResult'):
                continue

            home = data['teams']['home']
            away = data['teams']['away']

            home_name = home['name']['full']
            away_name = away['name']['full']

            # Filter to only include actual Premier League teams
            if home_name.lower() not in PL_TEAMS or away_name.lower() not in PL_TEAMS:
                continue

            results.append({
                'home_team': home_name,
                'away_team': away_name,
                'home_score': home['score']['current'],
                'away_score': away['score']['current']
            })

        except (json.JSONDecodeError, KeyError):
            continue

    return results[:20]


if __name__ == "__main__":
    print("Testing scrapers...\n")

    print("=== TOP SCORERS ===")
    scorers = scrape_top_scorers()
    for s in scorers[:5]:
        print(f"{s['rank']}. {s['player_name']} ({s['team']}) - {s['goals']} goals")

    print("\n=== FIXTURES ===")
    fixtures = scrape_fixtures()
    for f in fixtures[:5]:
        print(f"{f['home_team']} vs {f['away_team']} - {f['time']}")

    print("\n=== RESULTS ===")
    results = scrape_results()
    for r in results[:5]:
        print(f"{r['home_team']} {r['home_score']}-{r['away_score']} {r['away_team']}")
