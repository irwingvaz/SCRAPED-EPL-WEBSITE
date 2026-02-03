"""
Automated tests for Premier League scrapers.
Run with: pytest tests/ -v
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers import scrape_top_scorers, scrape_fixtures, scrape_results
from test_scraper import scrape_premier_league_table


class TestStandingsScraper:
    """Tests for the main standings scraper."""

    def test_scrape_returns_list(self):
        """Scraper should return a list."""
        result = scrape_premier_league_table()
        assert isinstance(result, list)

    def test_scrape_returns_teams(self):
        """Scraper should return team data."""
        result = scrape_premier_league_table()
        assert len(result) > 0, "Should return at least one team"

    def test_team_has_required_fields(self):
        """Each team should have required fields."""
        result = scrape_premier_league_table()
        if result:
            team = result[0]
            required_fields = ['position', 'team_name', 'played', 'wins', 'draws',
                               'losses', 'goals_for', 'goals_against', 'goal_difference', 'points']
            for field in required_fields:
                assert field in team, f"Team should have '{field}' field"

    def test_position_is_integer(self):
        """Position should be an integer."""
        result = scrape_premier_league_table()
        if result:
            assert isinstance(result[0]['position'], int)

    def test_points_is_integer(self):
        """Points should be an integer."""
        result = scrape_premier_league_table()
        if result:
            assert isinstance(result[0]['points'], int)


class TestTopScorersScraper:
    """Tests for the top scorers scraper."""

    def test_scrape_returns_list(self):
        """Scraper should return a list."""
        result = scrape_top_scorers()
        assert isinstance(result, list)

    def test_scrape_returns_scorers(self):
        """Scraper should return scorer data."""
        result = scrape_top_scorers()
        assert len(result) > 0, "Should return at least one scorer"

    def test_scorer_has_required_fields(self):
        """Each scorer should have required fields."""
        result = scrape_top_scorers()
        if result:
            scorer = result[0]
            required_fields = ['rank', 'player_name', 'team', 'goals', 'assists', 'played']
            for field in required_fields:
                assert field in scorer, f"Scorer should have '{field}' field"

    def test_goals_is_integer(self):
        """Goals should be an integer."""
        result = scrape_top_scorers()
        if result:
            assert isinstance(result[0]['goals'], int)

    def test_rank_starts_at_one(self):
        """First scorer should have rank 1."""
        result = scrape_top_scorers()
        if result:
            assert result[0]['rank'] == 1


class TestFixturesScraper:
    """Tests for the fixtures scraper."""

    def test_scrape_returns_list(self):
        """Scraper should return a list."""
        result = scrape_fixtures()
        assert isinstance(result, list)

    def test_fixture_has_required_fields(self):
        """Each fixture should have required fields."""
        result = scrape_fixtures()
        if result:
            fixture = result[0]
            required_fields = ['home_team', 'away_team', 'time']
            for field in required_fields:
                assert field in fixture, f"Fixture should have '{field}' field"

    def test_teams_are_different(self):
        """Home and away teams should be different."""
        result = scrape_fixtures()
        for fixture in result:
            assert fixture['home_team'] != fixture['away_team'], "Home and away teams should differ"


class TestResultsScraper:
    """Tests for the results scraper."""

    def test_scrape_returns_list(self):
        """Scraper should return a list."""
        result = scrape_results()
        assert isinstance(result, list)

    def test_result_has_required_fields(self):
        """Each result should have required fields."""
        result = scrape_results()
        if result:
            match = result[0]
            required_fields = ['home_team', 'away_team', 'home_score', 'away_score']
            for field in required_fields:
                assert field in match, f"Result should have '{field}' field"

    def test_scores_are_integers(self):
        """Scores should be integers."""
        result = scrape_results()
        for match in result:
            assert isinstance(match['home_score'], int)
            assert isinstance(match['away_score'], int)

    def test_scores_are_non_negative(self):
        """Scores should be non-negative."""
        result = scrape_results()
        for match in result:
            assert match['home_score'] >= 0
            assert match['away_score'] >= 0


class TestDataIntegrity:
    """Tests for data integrity across scrapers."""

    def test_standings_has_20_teams(self):
        """Premier League should have 20 teams."""
        result = scrape_premier_league_table()
        assert len(result) == 20, f"Expected 20 teams, got {len(result)}"

    def test_positions_are_sequential(self):
        """Positions should be 1 through 20."""
        result = scrape_premier_league_table()
        positions = [team['position'] for team in result]
        expected = list(range(1, 21))
        assert positions == expected, "Positions should be sequential 1-20"

    def test_top_scorers_ordered_by_goals(self):
        """Top scorers should be ordered by goals descending."""
        result = scrape_top_scorers()
        if len(result) >= 2:
            for i in range(len(result) - 1):
                assert result[i]['goals'] >= result[i + 1]['goals'], \
                    "Scorers should be ordered by goals descending"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
