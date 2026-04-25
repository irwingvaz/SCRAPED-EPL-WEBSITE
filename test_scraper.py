import time
import re
import requests
from bs4 import BeautifulSoup
from database import PremierLeagueDB

def scrape_premier_league_table(retries=3, delay=5):
    url = "https://www.bbc.com/sport/football/premier-league/table"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    response = None
    for attempt in range(1, retries + 1):
        try:
            print(f"Fetching data (attempt {attempt}/{retries})...")
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                break
            print(f"Status {response.status_code}, retrying in {delay}s...")
        except requests.RequestException as e:
            print(f"Request failed: {e}, retrying in {delay}s...")
        if attempt < retries:
            time.sleep(delay)

    if not response or response.status_code != 200:
        print("Failed to fetch page after all retries.")
        return []

    print("Successfully fetched the page!\n")

    soup = BeautifulSoup(response.content, 'lxml')
    table = soup.find('table', {'data-testid': 'football-table'})

    if not table:
        print("WARNING: Table not found — BBC Sport may have changed their markup.")
        return []

    rows = table.find('tbody').find_all('tr')
    standings_data = []

    for row in rows:
        cells = row.find_all('td')

        if len(cells) >= 9:
            pos_cell = cells[0].text.strip()
            match = re.match(r'^(\d+)(.+)$', pos_cell)
            if not match:
                print(f"WARNING: Could not parse row: '{pos_cell}', skipping.")
                continue
            position = int(match.group(1))
            team_name = match.group(2).strip()

            team_data = {
                'position': position,
                'team_name': team_name,
                'played': int(cells[1].text.strip()),
                'wins': int(cells[2].text.strip()),
                'draws': int(cells[3].text.strip()),
                'losses': int(cells[4].text.strip()),
                'goals_for': int(cells[5].text.strip()),
                'goals_against': int(cells[6].text.strip()),
                'goal_difference': int(cells[7].text.strip()),
                'points': int(cells[8].text.strip())
            }

            standings_data.append(team_data)

    if not standings_data:
        print("WARNING: 0 teams scraped — data may be empty or markup changed.")
        return []

    print("PREMIER LEAGUE STANDINGS")
    print("=" * 100)
    print(f"{'Pos':<4} {'Team':<25} {'P':<4} {'W':<4} {'D':<4} {'L':<4} {'GF':<5} {'GA':<5} {'GD':<5} {'Pts':<5}")
    print("=" * 100)

    for team in standings_data:
        print(f"{team['position']:<4} {team['team_name']:<25} {team['played']:<4} {team['wins']:<4} {team['draws']:<4} {team['losses']:<4} {team['goals_for']:<5} {team['goals_against']:<5} {team['goal_difference']:<5} {team['points']:<5}")

    print("=" * 100)

    db = PremierLeagueDB()

    if db.standings_unchanged(standings_data):
        print("\nData unchanged since last scrape, skipping save.")
        return standings_data

    print("\nSaving to database...")
    db.save_standings(standings_data)

    return standings_data

if __name__ == "__main__":
    scrape_premier_league_table()
