"""
Tests for core/utils.py shared utility functions.
"""

import pytest
from unittest.mock import MagicMock
from core.utils import (
    clean_llm_json_response,
    extract_predictions_json,
    log_predictions_to_db,
    clean_markdown_json,
    DEFAULT_USER_AGENT,
    DEFAULT_HEADERS,
)


class TestCleanLlmJsonResponse:
    """Tests for clean_llm_json_response()."""

    def test_strips_json_block(self):
        response = 'Here are bets\n---\nAudit\nJSON_START [{"s": "h"}] JSON_END'
        result = clean_llm_json_response(response)
        assert "JSON_START" not in result
        assert "JSON_END" not in result
        assert "Here are bets" in result

    def test_removes_trailing_separator(self):
        response = 'Bet 1\n---\nBet 2\n---\nAudit\nJSON_START [] JSON_END'
        result = clean_llm_json_response(response)
        assert "Audit" not in result
        assert "Bet 1" in result

    def test_passthrough_no_markers(self):
        response = "Just a normal response"
        assert clean_llm_json_response(response) == response

    def test_empty_string(self):
        assert clean_llm_json_response("") == ""

    def test_only_json_start(self):
        response = "text JSON_START no end"
        assert clean_llm_json_response(response) == response

    def test_only_json_end(self):
        response = "text JSON_END no start"
        assert clean_llm_json_response(response) == response


class TestExtractPredictionsJson:
    """Tests for extract_predictions_json()."""

    def test_extracts_list(self):
        response = 'text JSON_START [{"selection": "home"}] JSON_END'
        result = extract_predictions_json(response)
        assert result == [{"selection": "home"}]

    def test_handles_double_braces(self):
        response = 'text JSON_START {{"key": "val"}} JSON_END'
        result = extract_predictions_json(response)
        assert result == {"key": "val"}

    def test_returns_none_no_markers(self):
        assert extract_predictions_json("normal text") is None

    def test_returns_none_invalid_json(self):
        response = "text JSON_START not json JSON_END"
        assert extract_predictions_json(response) is None


class TestLogPredictionsToDb:
    """Tests for log_predictions_to_db()."""

    def test_logs_each_prediction(self):
        db = MagicMock()
        predictions = [
            {"selection": "home", "odds": 1.5},
            {"selection": "draw", "odds": 3.2},
        ]
        log_predictions_to_db(db, "+1234", "match_1", predictions)
        assert db.log_bet_prediction.call_count == 2

    def test_skips_empty_predictions(self):
        db = MagicMock()
        log_predictions_to_db(db, "+1234", "match_1", [])
        db.log_bet_prediction.assert_not_called()

    def test_skips_no_phone(self):
        db = MagicMock()
        log_predictions_to_db(db, None, "match_1", [{"selection": "home"}])
        db.log_bet_prediction.assert_not_called()

    def test_skips_none_predictions(self):
        db = MagicMock()
        log_predictions_to_db(db, "+1234", "match_1", None)
        db.log_bet_prediction.assert_not_called()


class TestCleanMarkdownJson:
    """Tests for clean_markdown_json()."""

    def test_strips_json_code_block(self):
        md = '```json\n{"key": "val"}\n```'
        result = clean_markdown_json(md)
        assert result == '{"key": "val"}'

    def test_strips_plain_code_block(self):
        md = '```\n{"key": "val"}\n```'
        result = clean_markdown_json(md)
        assert result == '{"key": "val"}'

    def test_passthrough_clean_json(self):
        clean = '{"key": "val"}'
        assert clean_markdown_json(clean) == clean

    def test_strips_whitespace(self):
        md = '  ```json\n{"key": "val"}\n```  '
        result = clean_markdown_json(md)
        assert result == '{"key": "val"}'


class TestConstants:
    """Tests for shared constants."""

    def test_user_agent_format(self):
        assert "Mozilla" in DEFAULT_USER_AGENT
        assert "Chrome" in DEFAULT_USER_AGENT

    def test_headers_has_user_agent(self):
        assert "User-Agent" in DEFAULT_HEADERS
        assert DEFAULT_HEADERS["User-Agent"] == DEFAULT_USER_AGENT

    def test_headers_has_accept(self):
        assert DEFAULT_HEADERS["Accept"] == "application/json"
