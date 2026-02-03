from flask import Flask, render_template
from database import PremierLeagueDB
from test_scraper import scrape_premier_league_table

app = Flask(__name__)

# Team colors mapping
TEAM_COLORS = {
    'arsenal': '#EF0107',
    'aston villa': '#95BFE5',
    'bournemouth': '#DA291C',
    'brentford': '#E30613',
    'brighton': '#0057B8',
    'brighton & hove albion': '#0057B8',
    'chelsea': '#034694',
    'crystal palace': '#1B458F',
    'everton': '#003399',
    'fulham': '#000000',
    'ipswich': '#0033A0',
    'ipswich town': '#0033A0',
    'leeds': '#FFCD00',
    'leeds united': '#FFCD00',
    'leicester': '#003090',
    'leicester city': '#003090',
    'liverpool': '#C8102E',
    'manchester city': '#6CABDD',
    'manchester united': '#DA291C',
    'newcastle': '#241F20',
    'newcastle united': '#241F20',
    'nottingham forest': '#DD0000',
    "nottm forest": '#DD0000',
    'southampton': '#D71920',
    'tottenham': '#132257',
    'tottenham hotspur': '#132257',
    'west ham': '#7A263A',
    'west ham united': '#7A263A',
    'wolves': '#FDB913',
    'wolverhampton': '#FDB913',
    'wolverhampton wanderers': '#FDB913',
}

@app.template_filter('team_color')
def team_color_filter(team_name):
    """Return the team's primary color or a default color."""
    return TEAM_COLORS.get(team_name.lower(), '#667eea')

@app.route('/')
def home():
    """Main page showing the standings"""
    db = PremierLeagueDB()
    standings = db.get_latest_standings()
    
    # Convert to list of dictionaries for easier template use
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
            'scraped_at': row[10],
            'change': 0  # Position change (not tracked yet)
        })
    
    return render_template('index.html', teams=teams)

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html',
                           error_code=404,
                           error_title="Page Not Found",
                           error_message="The page you're looking for doesn't exist."), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html',
                           error_code=500,
                           error_title="Server Error",
                           error_message="Something went wrong on our end. Please try again later."), 500

@app.errorhandler(Exception)
def handle_exception(e):
    return render_template('error.html',
                           error_code=500,
                           error_title="Oops! Something Went Wrong",
                           error_message="We couldn't load the standings. The scraper might be updating or there's a connection issue."), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Premier League Tracker Website")
    print("=" * 60)

    # Scrape latest data before starting the server
    print("\nScraping latest Premier League standings...")
    scrape_premier_league_table()

    print("\n" + "=" * 60)
    print("Open your browser and go to: http://localhost:8080")
    print("=" * 60)
    app.run(debug=True, port=8080)