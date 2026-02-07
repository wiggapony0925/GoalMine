"""
Shared utility functions for GoalMine.
Consolidates duplicate logic used across generate_bets.py and orchestrator.py.
"""

import json
from core.log import get_logger

logger = get_logger("Utils")

# Shared User-Agent for all HTTP requests (avoids duplication across API modules)
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "application/json",
}


def clean_llm_json_response(response: str) -> str:
    """
    Strips JSON audit blocks (JSON_START/JSON_END) from LLM responses
    so the user-facing text is clean for WhatsApp delivery.

    Args:
        response: Raw LLM response that may contain embedded JSON blocks.

    Returns:
        str: Cleaned response text without JSON audit data.
    """
    if "JSON_START" not in response or "JSON_END" not in response:
        return response

    clean = response.split("JSON_START")[0].strip()
    if "---" in clean:
        clean = "---".join(clean.split("---")[:-1]).strip()
    return clean


def extract_predictions_json(response: str) -> list | None:
    """
    Extracts structured prediction data from LLM responses
    containing JSON_START/JSON_END markers.

    Args:
        response: Raw LLM response with embedded JSON block.

    Returns:
        list: Parsed predictions list, or None if extraction fails.
    """
    if "JSON_START" not in response or "JSON_END" not in response:
        return None

    try:
        json_part = response.split("JSON_START")[1].split("JSON_END")[0].strip()
        json_part = json_part.replace("{{", "{").replace("}}", "}")
        return json.loads(json_part)
    except Exception as e:
        logger.error(f"Failed to extract predictions JSON: {e}")
        return None


def log_predictions_to_db(db, user_phone: str, match_id: str, predictions: list):
    """
    Logs each prediction to the database for ROI audit tracking.

    Args:
        db: Database instance.
        user_phone: User's phone number.
        match_id: Unique match identifier.
        predictions: List of prediction dicts from LLM.
    """
    if not user_phone or not predictions:
        return

    for p in predictions:
        db.log_bet_prediction(user_phone, match_id, p)


def clean_markdown_json(response: str) -> str:
    """
    Removes markdown code block wrappers from LLM JSON responses.

    Args:
        response: Raw LLM response that may be wrapped in ```json blocks.

    Returns:
        str: Clean JSON string.
    """
    return response.replace("```json", "").replace("```", "").strip()
