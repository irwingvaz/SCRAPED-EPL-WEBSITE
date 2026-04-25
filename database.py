import sqlite3
from datetime import datetime

class PremierLeagueDB:
    def __init__(self, db_name='premier_league.db'):
        import os
        tmp_path = os.path.join('/tmp', db_name)
        self.db_name = tmp_path if not os.access('.', os.W_OK) else db_name
        self.create_tables()

    def create_tables(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS standings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                position INTEGER,
                team_name TEXT,
                played INTEGER,
                wins INTEGER,
                draws INTEGER,
                losses INTEGER,
                goals_for INTEGER,
                goals_against INTEGER,
                goal_difference INTEGER,
                points INTEGER,
                scraped_at TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        print("[OK] Database tables created/verified")

    def standings_unchanged(self, standings_data):
        latest = self.get_latest_standings()
        if not latest:
            return False

        if len(latest) != len(standings_data):
            return False

        for existing, new in zip(latest, standings_data):
            if (existing[0] != new['position'] or
                existing[9] != new['points'] or
                existing[2] != new['played']):
                return False

        return True

    def save_standings(self, standings_data):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        scraped_at = datetime.now()

        for team in standings_data:
            cursor.execute('''
                INSERT INTO standings
                (position, team_name, played, wins, draws, losses,
                 goals_for, goals_against, goal_difference, points, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                team['position'],
                team['team_name'],
                team['played'],
                team['wins'],
                team['draws'],
                team['losses'],
                team['goals_for'],
                team['goals_against'],
                team['goal_difference'],
                team['points'],
                scraped_at
            ))

        conn.commit()
        conn.close()
        print(f"[OK] Saved {len(standings_data)} teams to database")

    def get_latest_standings(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT position, team_name, played, wins, draws, losses,
                   goals_for, goals_against, goal_difference, points, scraped_at
            FROM standings
            WHERE scraped_at = (SELECT MAX(scraped_at) FROM standings)
            ORDER BY position
        ''')

        results = cursor.fetchall()
        conn.close()

        return results
