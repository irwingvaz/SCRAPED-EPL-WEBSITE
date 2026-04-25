from flask import Flask, render_template
from database import PremierLeagueDB

app = Flask(__name__)

@app.route('/')
def home():
    db = PremierLeagueDB()
    standings = db.get_latest_standings()

    teams = []
    for row in standings:
        teams.append({
            'position': row[0],
            'team_name': row[1],
            'played': row[2],
            'wins': row[3],
            'draws': row[4],
            'losses': row[5],
            'goals_for': row[6],
            'goals_against': row[7],
            'goal_difference': row[8],
            'points': row[9],
            'scraped_at': row[10]
        })

    return render_template('index.html', teams=teams)

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Premier League Tracker Website")
    print("Open your browser and go to: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True)
