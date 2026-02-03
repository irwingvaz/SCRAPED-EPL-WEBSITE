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
            # Extract player name and team from second cell
            name_cell = cells[1].text.strip()
            # Name format is like "E. HaalandMan CityE. HaalandMa..."
            # We need to parse it carefully

            # Try to find team badge container for team name
            badge = row.find(attrs={'data-testid': lambda x: x and 'badge-container' in x if x else False})
            team = ''
            if badge:
                team_slug = badge.get('data-testid', '').replace('badge-container-', '')
                team = team_slug.replace('-', ' ').title()

            # Extract player name from the cell
            # Pattern: "FirstInitial. LastNameTeamNameFirstInitial. ..." or "Full NameTeamName..."
            import re
            # Try pattern like "E. Haaland" or "João Pedro"
            name_match = re.match(r'^([A-Z]\.\s*[A-Za-zÀ-ÿ\-\']+|[A-Za-zÀ-ÿ]+\s+[A-Za-zÀ-ÿ\-\']+)', name_cell)
            player_name = name_match.group(1) if name_match else name_cell[:20]
            # Clean up any team name that got attached
            player_name = re.sub(r'(Man City|Man Utd|Liverpool|Chelsea|Arsenal|Brentford|Brighton|Everton|Fulham|Newcastle|Spurs|West Ham|Wolves|Burnley|Crystal Palace|Bournemouth|Nottm Forest|Leeds|Sunderland|Aston Villa).*$', '', player_name, flags=re.IGNORECASE).strip()

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
    url = "https://www.bbc.com/sport/football/premier-league/scores-fixtures"

    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch fixtures: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'lxml')

    fixtures = []

    # Find list items containing fixture data
    for li in soup.find_all('li'):
        text = li.get_text()
        if 'versus' not in text.lower():
            continue

        spans = li.find_all('span')
        span_texts = [s.get_text(strip=True) for s in spans if s.get_text(strip=True)]

        if len(span_texts) < 7:
            continue

        time_elem = li.find('time')
        time_str = time_elem.get_text(strip=True) if time_elem else ''

        # Parse fixture data from spans
        # Format: ['Title', 'ShortName1', 'FullName1', 'FullName1', 'Time', 'plays', 'ShortName2', 'FullName2', 'FullName2']
        home_team = span_texts[2] if len(span_texts) > 2 else ''
        away_team = span_texts[7] if len(span_texts) > 7 else span_texts[-1] if span_texts else ''

        # Skip if we couldn't get both teams
        if not home_team or not away_team or home_team == away_team:
            continue

        # Check if this is a result (has a score) or upcoming fixture
        # Look for score pattern in text
        import re
        score_match = re.search(r'(\d+)\s*-\s*(\d+)', text)

        if score_match:
            # This is a result, skip for fixtures
            continue

        fixtures.append({
            'home_team': home_team,
            'away_team': away_team,
            'time': time_str,
            'date': ''  # Would need additional parsing for date
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
    """Scrape recent Premier League results from BBC Sport."""
    url = "https://www.bbc.com/sport/football/premier-league/scores-fixtures"

    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch results: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'lxml')

    results = []

    # Find list items containing match data
    for li in soup.find_all('li'):
        text = li.get_text()
        if 'versus' not in text.lower():
            continue

        # Look for score pattern
        import re
        score_match = re.search(r'(\d+)\s*-\s*(\d+)', text)

        if not score_match:
            continue  # This is a fixture, not a result

        home_score = int(score_match.group(1))
        away_score = int(score_match.group(2))

        spans = li.find_all('span')
        span_texts = [s.get_text(strip=True) for s in spans if s.get_text(strip=True)]

        if len(span_texts) < 7:
            continue

        # Parse team names
        home_team = span_texts[2] if len(span_texts) > 2 else ''
        away_team = span_texts[7] if len(span_texts) > 7 else span_texts[-1] if span_texts else ''

        if not home_team or not away_team:
            continue

        results.append({
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
        })

    # Remove duplicates
    seen = set()
    unique_results = []
    for r in results:
        key = (r['home_team'], r['away_team'], r['home_score'], r['away_score'])
        if key not in seen:
            seen.add(key)
            unique_results.append(r)

    return unique_results[:20]


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
