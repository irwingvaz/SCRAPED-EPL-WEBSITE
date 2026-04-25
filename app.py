from flask import Flask, render_template, jsonify, Response
from database import PremierLeagueDB
from test_scraper import scrape_premier_league_table
from scrapers import scrape_top_scorers, scrape_fixtures, scrape_results
import csv
import io

app = Flask(__name__)

TEAM_LOGOS = {
    'arsenal': 'https://resources.premierleague.com/premierleague/badges/rb/t3.svg',
    'aston villa': 'https://resources.premierleague.com/premierleague/badges/rb/t7.svg',
    'villa': 'https://resources.premierleague.com/premierleague/badges/rb/t7.svg',
    'bournemouth': 'https://resources.premierleague.com/premierleague/badges/rb/t91.svg',
    'afc bournemouth': 'https://resources.premierleague.com/premierleague/badges/rb/t91.svg',
    'brentford': 'https://resources.premierleague.com/premierleague/badges/rb/t94.svg',
    'brighton': 'https://resources.premierleague.com/premierleague/badges/rb/t36.svg',
    'brighton & hove albion': 'https://resources.premierleague.com/premierleague/badges/rb/t36.svg',
    'brighton and hove albion': 'https://resources.premierleague.com/premierleague/badges/rb/t36.svg',
    'chelsea': 'https://resources.premierleague.com/premierleague/badges/rb/t8.svg',
    'crystal palace': 'https://resources.premierleague.com/premierleague/badges/rb/t31.svg',
    'palace': 'https://resources.premierleague.com/premierleague/badges/rb/t31.svg',
    'everton': 'https://resources.premierleague.com/premierleague/badges/rb/t11.svg',
    'fulham': 'https://resources.premierleague.com/premierleague/badges/rb/t54.svg',
    'ipswich': 'https://resources.premierleague.com/premierleague/badges/rb/t40.svg',
    'ipswich town': 'https://resources.premierleague.com/premierleague/badges/rb/t40.svg',
    'leeds': 'https://resources.premierleague.com/premierleague/badges/rb/t2.svg',
    'leeds united': 'https://resources.premierleague.com/premierleague/badges/rb/t2.svg',
    'leicester': 'https://resources.premierleague.com/premierleague/badges/rb/t13.svg',
    'leicester city': 'https://resources.premierleague.com/premierleague/badges/rb/t13.svg',
    'liverpool': 'https://resources.premierleague.com/premierleague/badges/rb/t14.svg',
    'manchester city': 'https://resources.premierleague.com/premierleague/badges/rb/t43.svg',
    'man city': 'https://resources.premierleague.com/premierleague/badges/rb/t43.svg',
    'manchester united': 'https://resources.premierleague.com/premierleague/badges/rb/t1.svg',
    'man utd': 'https://resources.premierleague.com/premierleague/badges/rb/t1.svg',
    'man united': 'https://resources.premierleague.com/premierleague/badges/rb/t1.svg',
    'newcastle': 'https://resources.premierleague.com/premierleague/badges/rb/t4.svg',
    'newcastle united': 'https://resources.premierleague.com/premierleague/badges/rb/t4.svg',
    'nottingham forest': 'https://resources.premierleague.com/premierleague/badges/rb/t17.svg',
    'nottm forest': 'https://resources.premierleague.com/premierleague/badges/rb/t17.svg',
    'forest': 'https://resources.premierleague.com/premierleague/badges/rb/t17.svg',
    'southampton': 'https://resources.premierleague.com/premierleague/badges/rb/t20.svg',
    'saints': 'https://resources.premierleague.com/premierleague/badges/rb/t20.svg',
    'tottenham': 'https://resources.premierleague.com/premierleague/badges/rb/t6.svg',
    'tottenham hotspur': 'https://resources.premierleague.com/premierleague/badges/rb/t6.svg',
    'spurs': 'https://resources.premierleague.com/premierleague/badges/rb/t6.svg',
    'west ham': 'https://resources.premierleague.com/premierleague/badges/rb/t21.svg',
    'west ham united': 'https://resources.premierleague.com/premierleague/badges/rb/t21.svg',
    'wolves': 'https://resources.premierleague.com/premierleague/badges/rb/t39.svg',
    'wolverhampton': 'https://resources.premierleague.com/premierleague/badges/rb/t39.svg',
    'wolverhampton wanderers': 'https://resources.premierleague.com/premierleague/badges/rb/t39.svg',
    'sunderland': 'https://resources.premierleague.com/premierleague/badges/rb/t56.svg',
}

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
    'nottm forest': '#DD0000',
    'southampton': '#D71920',
    'tottenham': '#132257',
    'tottenham hotspur': '#132257',
    'west ham': '#7A263A',
    'west ham united': '#7A263A',
    'wolves': '#FDB913',
    'wolverhampton': '#FDB913',
    'wolverhampton wanderers': '#FDB913',
    'sunderland': '#EB172B',
}

@app.template_filter('team_color')
def team_color_filter(team_name):
    return TEAM_COLORS.get(team_name.lower(), '#667eea')

@app.template_filter('team_logo')
def team_logo_filter(team_name):
    return TEAM_LOGOS.get(team_name.lower())

def get_team_form(team_name, results_list, limit=5):
    form = []
    team_lower = team_name.lower()

    for result in results_list:
        home = result['home_team'].lower()
        away = result['away_team'].lower()

        if team_lower in home or home in team_lower:
            if result['home_score'] > result['away_score']:
                form.append('W')
            elif result['home_score'] < result['away_score']:
                form.append('L')
            else:
                form.append('D')
        elif team_lower in away or away in team_lower:
            if result['away_score'] > result['home_score']:
                form.append('W')
            elif result['away_score'] < result['home_score']:
                form.append('L')
            else:
                form.append('D')

        if len(form) >= limit:
            break

    return form

def get_teams_data():
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

@app.route('/')
def home():
    teams = get_teams_data()
    results_list = scrape_results()
    for team in teams:
        team['form'] = get_team_form(team['team_name'], results_list)
    return render_template('index.html', teams=teams)

@app.route('/top-scorers')
def top_scorers():
    scorers = scrape_top_scorers()
    return render_template('top_scorers.html', scorers=scorers)

@app.route('/fixtures')
def fixtures():
    fixture_list = scrape_fixtures()
    teams = get_teams_data()
    team_positions = {t['team_name'].lower(): t['position'] for t in teams}
    return render_template('fixtures.html', fixtures=fixture_list, team_positions=team_positions)

@app.route('/results')
def results():
    result_list = scrape_results()
    return render_template('results.html', results=result_list)

@app.route('/team/<team_name>')
def team_detail(team_name):
    teams = get_teams_data()
    results_list = scrape_results()
    fixture_list = scrape_fixtures()

    team_name_clean = team_name.replace('-', ' ').replace('_', ' ').lower()
    team = None
    for t in teams:
        if team_name_clean in t['team_name'].lower() or t['team_name'].lower() in team_name_clean:
            team = t
            break

    if not team:
        return render_template('error.html',
                               error_code=404,
                               error_title="Team Not Found",
                               error_message=f"Could not find team: {team_name}"), 404

    team['form'] = get_team_form(team['team_name'], results_list)

    team_results = []
    team_lower = team['team_name'].lower()
    for result in results_list:
        if team_lower in result['home_team'].lower() or team_lower in result['away_team'].lower():
            team_results.append(result)
        if len(team_results) >= 5:
            break

    team_fixtures = []
    for fixture in fixture_list:
        if team_lower in fixture['home_team'].lower() or team_lower in fixture['away_team'].lower():
            team_fixtures.append(fixture)
        if len(team_fixtures) >= 5:
            break

    if team['played'] > 0:
        team['win_rate'] = round((team['wins'] / team['played']) * 100, 1)
        team['ppg'] = round(team['points'] / team['played'], 2)
    else:
        team['win_rate'] = 0
        team['ppg'] = 0

    return render_template('team_detail.html',
                           team=team,
                           team_results=team_results,
                           team_fixtures=team_fixtures)

@app.route('/export/csv')
def export_csv():
    teams = get_teams_data()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['Position', 'Team', 'Played', 'Wins', 'Draws', 'Losses',
                     'Goals For', 'Goals Against', 'Goal Difference', 'Points'])

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

@app.route('/api/standings')
def api_standings():
    teams = get_teams_data()
    return jsonify({'success': True, 'count': len(teams), 'data': teams})

@app.route('/api/teams/<team_id>')
def api_team(team_id):
    teams = get_teams_data()

    if team_id.isdigit():
        position = int(team_id)
        for team in teams:
            if team['position'] == position:
                return jsonify({'success': True, 'data': team})

    team_id_lower = team_id.lower().replace('-', ' ').replace('_', ' ')
    for team in teams:
        if team_id_lower in team['team_name'].lower():
            return jsonify({'success': True, 'data': team})

    return jsonify({'success': False, 'error': 'Team not found'}), 404

@app.route('/api/top-scorers')
def api_top_scorers():
    scorers = scrape_top_scorers()
    return jsonify({'success': True, 'count': len(scorers), 'data': scorers})

@app.route('/api/fixtures')
def api_fixtures():
    fixture_list = scrape_fixtures()
    return jsonify({'success': True, 'count': len(fixture_list), 'data': fixture_list})

@app.route('/api/results')
def api_results():
    result_list = scrape_results()
    return jsonify({'success': True, 'count': len(result_list), 'data': result_list})

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

    print("\nScraping latest Premier League standings...")
    scrape_premier_league_table()

    print("\n" + "=" * 60)
    print("Open your browser and go to: http://localhost:8080")
    print("=" * 60)
    app.run(debug=True, port=8080)
