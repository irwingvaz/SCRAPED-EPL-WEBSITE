from flask import Flask, render_template, jsonify, Response
from database import PremierLeagueDB
from test_scraper import scrape_premier_league_table
from scrapers import scrape_top_scorers, scrape_fixtures, scrape_results
import csv
import io

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

def get_teams_data():
    """Helper function to get standings as list of dictionaries."""
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
            'scraped_at': str(row[10]),
            'change': 0
        })
    return teams

# =============================================================================
# WEB ROUTES
# =============================================================================

@app.route('/')
def home():
    """Main page showing the standings"""
    teams = get_teams_data()
    return render_template('index.html', teams=teams)

@app.route('/top-scorers')
def top_scorers():
    """Page showing top scorers."""
    scorers = scrape_top_scorers()
    return render_template('top_scorers.html', scorers=scorers)

@app.route('/fixtures')
def fixtures():
    """Page showing upcoming fixtures."""
    fixture_list = scrape_fixtures()
    # Get team positions for display
    teams = get_teams_data()
    team_positions = {t['team_name'].lower(): t['position'] for t in teams}
    return render_template('fixtures.html', fixtures=fixture_list, team_positions=team_positions)

@app.route('/results')
def results():
    """Page showing recent results."""
    result_list = scrape_results()
    return render_template('results.html', results=result_list)

@app.route('/export/csv')
def export_csv():
    """Export standings to CSV file."""
    teams = get_teams_data()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow(['Position', 'Team', 'Played', 'Wins', 'Draws', 'Losses',
                     'Goals For', 'Goals Against', 'Goal Difference', 'Points'])

    # Data rows
    for team in teams:
        writer.writerow([
            team['position'], team['team_name'], team['played'], team['wins'],
            team['draws'], team['losses'], team['goals_for'], team['goals_against'],
            team['goal_difference'], team['points']
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=premier_league_standings.csv'}
    )

# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/api/standings')
def api_standings():
    """API endpoint: Get all standings."""
    teams = get_teams_data()
    return jsonify({
        'success': True,
        'count': len(teams),
        'data': teams
    })

@app.route('/api/teams/<team_id>')
def api_team(team_id):
    """API endpoint: Get a specific team by position or name."""
    teams = get_teams_data()

    # Try to find by position (if numeric)
    if team_id.isdigit():
        position = int(team_id)
        for team in teams:
            if team['position'] == position:
                return jsonify({'success': True, 'data': team})

    # Try to find by name (case-insensitive partial match)
    team_id_lower = team_id.lower().replace('-', ' ').replace('_', ' ')
    for team in teams:
        if team_id_lower in team['team_name'].lower():
            return jsonify({'success': True, 'data': team})

    return jsonify({'success': False, 'error': 'Team not found'}), 404

@app.route('/api/top-scorers')
def api_top_scorers():
    """API endpoint: Get top scorers."""
    scorers = scrape_top_scorers()
    return jsonify({
        'success': True,
        'count': len(scorers),
        'data': scorers
    })

@app.route('/api/fixtures')
def api_fixtures():
    """API endpoint: Get upcoming fixtures."""
    fixture_list = scrape_fixtures()
    return jsonify({
        'success': True,
        'count': len(fixture_list),
        'data': fixture_list
    })

@app.route('/api/results')
def api_results():
    """API endpoint: Get recent results."""
    result_list = scrape_results()
    return jsonify({
        'success': True,
        'count': len(result_list),
        'data': result_list
    })

# =============================================================================
# ERROR HANDLERS
# =============================================================================

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