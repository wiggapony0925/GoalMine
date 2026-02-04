"""
God View JSON Builder
Centralized construction of the God View intelligence matrix.
Keeps orchestrator.py clean and makes the structure reusable.
"""

from datetime import datetime
from core.log import get_logger

logger = get_logger("GodViewBuilder")


def build_god_view(
    home_team: str,
    away_team: str,
    match_key: str,
    logistics_data: dict,
    tactics_data: dict,
    market_data: dict,
    narrative_home: dict,
    narrative_away: dict,
    quant_data: dict,
    final_xg_home: float,
    final_xg_away: float,
    base_xg_home: float,
    base_xg_away: float,
    narrative_adj_home: float,
    narrative_adj_away: float,
    logistics_penalty: float,
) -> dict:
    """
    Constructs the optimized God View JSON from agent outputs.

    Args:
        home_team: Home team name
        away_team: Away team name
        match_key: Cache key for the match
        logistics_data: Output from Logistics Agent
        tactics_data: Output from Tactics Agent
        market_data: Output from Market Agent
        narrative_home: Output from Narrative Agent (home team)
        narrative_away: Output from Narrative Agent (away team)
        quant_data: Output from Quant Engine
        final_xg_home: Final adjusted xG for home team
        final_xg_away: Final adjusted xG for away team
        base_xg_home: Base xG from Tactics (before adjustments)
        base_xg_away: Base xG from Tactics (before adjustments)
        narrative_adj_home: Narrative adjustment for home
        narrative_adj_away: Narrative adjustment for away
        logistics_penalty: Logistics fatigue penalty multiplier

    Returns:
        dict: Optimized God View JSON
    """

    god_view = {
        # === CORE IDENTIFICATION ===
        "match": f"{home_team} vs {away_team}",
        "timestamp": datetime.utcnow().isoformat(),
        # === AGENT INTELLIGENCE (Optimized - no duplicates) ===
        "logistics": {
            "branch": logistics_data.get("branch"),
            "route": logistics_data.get("route"),
            "distance_km": logistics_data.get("distance_km"),
            "tz_shift": logistics_data.get("tz_shift"),
            "fatigue_score": logistics_data.get("fatigue_score"),
            "risk": logistics_data.get("risk"),
            "stamina_impact": logistics_data.get("stamina_impact"),
            "summary": logistics_data.get("summary"),
            # Remove 'reasoning' to reduce payload (available in logs if needed)
        },
        "tactics": {
            "branch": tactics_data.get("branch"),
            "matchup_styles": tactics_data.get("matchup_styles"),
            "team_a_xg": tactics_data.get("team_a_xg"),
            "team_b_xg": tactics_data.get("team_b_xg"),
            "tactical_adjustments": tactics_data.get("tactical_adjustments"),
            "key_battle": tactics_data.get("key_battle"),
            "game_script": tactics_data.get("game_script"),
            # Remove verbose 'tactical_analysis' and 'reasoning' (in logs)
        },
        "market": {
            "branch": market_data.get("branch"),
            "best_odds": market_data.get("best_odds"),
            "market_math": {
                "vig": market_data.get("market_math", {}).get("vig"),
                "is_arbitrage": market_data.get("market_math", {}).get("is_arbitrage"),
                "fair_probs": market_data.get("market_math", {}).get("fair_probs"),
            },
            # Flatten analysis for better access
            "value_score": market_data.get("analysis", {}).get("value_score"),
            "edge_percentage": market_data.get("analysis", {}).get("edge_percentage"),
            "trap_alert": market_data.get("analysis", {}).get("trap_alert"),
        },
        "narrative": {
            "home": {
                "team": narrative_home.get("team"),
                "score": narrative_home.get("score"),
                "morale": narrative_home.get("morale"),
                "adjustment": narrative_home.get("adjustment"),
                "headline": narrative_home.get("headline"),
                "summary": narrative_home.get("summary"),
                # ✅ Removed raw_analysis duplicate
            },
            "away": {
                "team": narrative_away.get("team"),
                "score": narrative_away.get("score"),
                "morale": narrative_away.get("morale"),
                "adjustment": narrative_away.get("adjustment"),
                "headline": narrative_away.get("headline"),
                "summary": narrative_away.get("summary"),
                # ✅ Removed raw_analysis duplicate
            },
        },
        "quant": quant_data,  # Already optimized
        # === FINAL OUTPUTS ===
        "final_xg": {"home": round(final_xg_home, 2), "away": round(final_xg_away, 2)},
        # === METADATA (New - for performance tracking) ===
        "meta": {
            "agents_executed": {
                "logistics": logistics_data.get("status", "OK")
                if logistics_data.get("branch")
                else "FALLBACK",
                "tactics": tactics_data.get("status", "OK")
                if tactics_data.get("branch")
                else "FALLBACK",
                "market": market_data.get("status", "OK")
                if market_data.get("branch")
                else "FALLBACK",
                "narrative_home": narrative_home.get("status", "OK")
                if narrative_home.get("branch")
                else "FALLBACK",
                "narrative_away": narrative_away.get("status", "OK")
                if narrative_away.get("branch")
                else "FALLBACK",
            },
            "version": "2.0",  # Track God View schema version
            "cache_key": match_key,
            "xg_adjustment_chain": {
                "base_tactics": {
                    "home": round(base_xg_home, 2),
                    "away": round(base_xg_away, 2),
                },
                "narrative_adj": {
                    "home": round(narrative_adj_home, 2),
                    "away": round(narrative_adj_away, 2),
                },
                "logistics_penalty": round(logistics_penalty, 2),
                "final": {
                    "home": round(final_xg_home, 2),
                    "away": round(final_xg_away, 2),
                },
            },
        },
    }

    logger.debug(
        f"✅ God View built for {home_team} vs {away_team} (v{god_view['meta']['version']})"
    )

    return god_view
