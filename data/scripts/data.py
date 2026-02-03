"""
Centralized data loading module for GoalMine.
All JSON configuration files are loaded here to provide a single source of truth.
"""
import json
import os
from datetime import datetime
from core.log import get_logger

logger = get_logger("Data")

def load_json_file(filename, default=None):
    """
    Generic JSON file loader with error handling.
    
    Args:
        filename: Name of file in data/ directory
        default: Default value to return if file not found
    
    Returns:
        Parsed JSON data or default value
    """
    # Path goes up from data/scripts/ to data/
    path = os.path.join(os.path.dirname(__file__), '..', filename)
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"File not found: {filename}. Using default value.")
        return default if default is not None else {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filename}: {e}")
        return default if default is not None else {}
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        return default if default is not None else {}

# ============================================================================
# LOAD ALL DATA FILES
# ============================================================================

# Venue Database (Logistics Agent)
VENUES_DB = load_json_file('venues.json', default={})

# World Cup 2026 Schedule (Orchestrator)
SCHEDULE = load_json_file('schedule.json', default=[])

# Betting Market Types (Orchestrator)
BET_TYPES = load_json_file('bet_types.json', default={})

# Reddit Scraper Configuration (Narrative Agent)
REDDIT_CONFIG = load_json_file('reddit_config.json', default={
    "subreddits": ["soccer", "worldcup", "football"],
    "keywords": {
        "morale": ["toxic", "unhappy", "locker room"],
        "fitness": ["injury", "unfit", "knock"],
        "tactics": ["benched", "tactical", "exposed"]
    },
    "metadata": {"version": "1.2", "deep_scan_limit": 3}
})

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_days_rest(prev_match_date_iso, next_match_date_iso):
    """
    Calculate days of rest between two matches.
    
    Args:
        prev_match_date_iso: ISO format date string of previous match
        next_match_date_iso: ISO format date string of next match
    
    Returns:
        int: Number of days between matches
    """
    try:
        prev_date = datetime.fromisoformat(prev_match_date_iso)
        next_date = datetime.fromisoformat(next_match_date_iso)
        delta = next_date - prev_date
        return max(0, delta.days)
    except Exception as e:
        logger.warning(f"Error calculating days rest: {e}. Defaulting to 4 days.")
        return 4  # Default to 4 days if parsing fails

def get_venue_info(venue_name):
    """
    Get venue information with robust fuzzy matching.
    Handles multiple naming conventions:
    - "Estadio Azteca, Mexico City" (exact match)
    - "Azteca_Mexico" (legacy ID format)
    - "Azteca" (partial match)
    
    Args:
        venue_name: Full or partial venue name
    
    Returns:
        tuple: (matched_key, venue_data)
    """
    if not venue_name:
        fallback = 'MetLife Stadium, East Rutherford'
        return fallback, VENUES_DB.get(fallback, {})
    
    # Normalize input: remove underscores, convert to lowercase
    normalized_input = venue_name.replace("_", " ").lower().strip()
    
    # 1. Try exact match first (case-insensitive)
    for db_key in VENUES_DB.keys():
        if db_key.lower() == normalized_input:
            return db_key, VENUES_DB[db_key]
    
    # 2. Try matching the stadium name (first part before comma)
    search_key = normalized_input.split(",")[0].strip()
    
    for db_key, data in VENUES_DB.items():
        db_stadium_name = db_key.split(",")[0].lower()
        
        # Check if search key is in the stadium name or vice versa
        if search_key in db_stadium_name or db_stadium_name in search_key:
            logger.debug(f"Venue matched: '{venue_name}' -> '{db_key}'")
            return db_key, data
    
    # 3. Try partial match on any part of the venue name
    for db_key, data in VENUES_DB.items():
        if search_key in db_key.lower():
            logger.debug(f"Partial venue match: '{venue_name}' -> '{db_key}'")
            return db_key, data
    
    # 4. Fallback to default
    fallback = 'MetLife Stadium, East Rutherford'
    logger.warning(f"Venue '{venue_name}' not found in database. Using fallback: {fallback}")
    return fallback, VENUES_DB.get(fallback, {})


# ============================================================================
# DATA VALIDATION (Run on import)
# ============================================================================

# Data is loaded silently. Status is shown in the startup banner.
