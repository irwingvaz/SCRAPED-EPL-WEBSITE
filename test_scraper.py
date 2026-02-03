import requests
from bs4 import BeautifulSoup
from database import PremierLeagueDB

def scrape_premier_league_table():
    """
    Scrapes the Premier League standings from BBC Sport
    """
    
    url = "https://www.bbc.com/sport/football/premier-league/table"
    
    print(f"Fetching data from: {url}\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✓ Successfully fetched the page!\n")
        
        soup = BeautifulSoup(response.content, 'lxml')
        table = soup.find('table', {'data-testid': 'football-table'})
        
        if table:
            rows = table.find('tbody').find_all('tr')
            
            # Store data in a list
            standings_data = []
            
            for row in rows:
                cells = row.find_all('td')
                
                if len(cells) >= 9:
                    pos_team = cells[0].text.strip()
                    position = ''.join(filter(str.isdigit, pos_team[:3]))
                    team_name = pos_team[len(position):]
                    
                    team_data = {
                        'position': int(position),
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
            
            # Display the data
            print("PREMIER LEAGUE STANDINGS")
            print("=" * 100)
            print(f"{'Pos':<4} {'Team':<25} {'P':<4} {'W':<4} {'D':<4} {'L':<4} {'GF':<5} {'GA':<5} {'GD':<5} {'Pts':<5}")
            print("=" * 100)
            
            for team in standings_data:
                print(f"{team['position']:<4} {team['team_name']:<25} {team['played']:<4} {team['wins']:<4} {team['draws']:<4} {team['losses']:<4} {team['goals_for']:<5} {team['goals_against']:<5} {team['goal_difference']:<5} {team['points']:<5}")
            
            print("=" * 100)
            
            # Save to database
            print("\nSaving to database...")
            db = PremierLeagueDB()
            db.save_standings(standings_data)
            
            return standings_data
        
        else:
            print("✗ Could not find the table")
            return []
    
    else:
        print(f"✗ Failed to fetch page. Status code: {response.status_code}")
        return []

if __name__ == "__main__":
    scrape_premier_league_table()