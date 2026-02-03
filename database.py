import sqlite3
from datetime import datetime

class PremierLeagueDB:
    def __init__(self, db_name='premier_league.db'):
        """Initialize database connection"""
        self.db_name = db_name
        self.create_tables()
    
    def create_tables(self):
        """Create the tables if they don't exist"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Create standings table
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
                scraped_at TIMESTAMP,
                UNIQUE(team_name, scraped_at)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✓ Database tables created/verified")
    
    def save_standings(self, standings_data):
        """Save standings data to database"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        scraped_at = datetime.now()
        
        for team in standings_data:
            cursor.execute('''
                INSERT OR IGNORE INTO standings 
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
        print(f"✓ Saved {len(standings_data)} teams to database")
    
    def get_latest_standings(self):
        """Retrieve the most recent standings"""
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