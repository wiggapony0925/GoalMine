"""
Tests for agents/narrative/api/free_sports.py API functions.
"""

from unittest.mock import patch, MagicMock
from agents.narrative.api.free_sports import (
    fetch_team_wikipedia_summary,
    fetch_football_rankings,
)


class TestFetchTeamWikipediaSummary:
    """Tests for fetch_team_wikipedia_summary()."""

    @patch("agents.narrative.api.free_sports.requests.get")
    def test_successful_response(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "title": "Brazil national football team",
            "extract": "The Brazil national football team is...",
            "thumbnail": {"source": "https://example.com/thumb.jpg"},
        }
        mock_get.return_value = mock_resp

        result = fetch_team_wikipedia_summary("Brazil")

        assert result["source"] == "wikipedia"
        assert "Brazil" in result["title"]
        assert result["summary"] != ""
        assert result["thumbnail"] != ""

    @patch("agents.narrative.api.free_sports.requests.get")
    def test_fallback_on_404(self, mock_get):
        # First call returns 404, second returns 200
        mock_404 = MagicMock()
        mock_404.status_code = 404

        mock_200 = MagicMock()
        mock_200.status_code = 200
        mock_200.json.return_value = {
            "title": "Brazil",
            "extract": "Short summary",
            "thumbnail": {},
        }

        mock_get.side_effect = [mock_404, mock_200]

        result = fetch_team_wikipedia_summary("Brazil")
        assert result["source"] == "wikipedia"
        assert result["summary"] == "Short summary"

    @patch("agents.narrative.api.free_sports.requests.get")
    def test_network_error_returns_empty(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        result = fetch_team_wikipedia_summary("Brazil")
        assert result["source"] == "wikipedia"
        assert result["summary"] == ""


class TestFetchFootballRankings:
    """Tests for fetch_football_rankings()."""

    @patch("agents.narrative.api.free_sports.requests.get")
    def test_returns_standings(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"standings": [{"group": "A"}]}
        mock_get.return_value = mock_resp

        result = fetch_football_rankings()
        assert len(result) == 1

    @patch("agents.narrative.api.free_sports.requests.get")
    def test_api_failure_returns_empty(self, mock_get):
        mock_get.side_effect = Exception("Timeout")

        result = fetch_football_rankings()
        assert result == []
