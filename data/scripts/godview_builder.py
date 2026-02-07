"""
God View JSON Builder
Centralized construction of the God View intelligence matrix.
Keeps orchestrator.py clean and makes the structure reusable.

The God View is the single source of truth for bet generation, follow-up Q&A,
and enterprise-grade analytics. Every field is documented and typed.
"""

from datetime import datetime
from core.log import get_logger

logger = get_logger("GodViewBuilder")

GOD_VIEW_SCHEMA_VERSION = "3.0"


def _compute_signal_convergence(logistics_data, tactics_data, market_data,
                                narrative_home, narrative_away):
    """
    Calculates how many agents agree on the same directional signal.
    Convergence of 4-5 = elite conviction. Convergence of 1-2 = caution.
    """
    signals = []

    # Tactics signal: which team has higher xG?
    xg_a = tactics_data.get("team_a_xg", 0) or 0
    xg_b = tactics_data.get("team_b_xg", 0) or 0
    if xg_a > xg_b:
        signals.append("home")
    elif xg_b > xg_a:
        signals.append("away")

    # Narrative signal: which team has better morale?
    home_score = narrative_home.get("score", 5) or 5
    away_score = narrative_away.get("score", 5) or 5
    if home_score > away_score + 1:
        signals.append("home")
    elif away_score > home_score + 1:
        signals.append("away")

    # Logistics signal: does fatigue penalize one side?
    fatigue = logistics_data.get("fatigue_score", 0) or 0
    if fatigue >= 6:
        signals.append("home")  # Away team fatigued = home advantage

    # Market signal: where is value?
    analysis = market_data.get("analysis", {})
    best_bet = analysis.get("best_bet", "")
    if best_bet:
        signals.append("home" if "home" in best_bet.lower() or "team a" in best_bet.lower() else "away")

    home_count = signals.count("home")
    away_count = signals.count("away")
    dominant = "home" if home_count >= away_count else "away"
    convergence = max(home_count, away_count)

    return {
        "dominant_direction": dominant,
        "agreeing_agents": convergence,
        "total_signals": len(signals),
        "conviction_level": (
            "Elite" if convergence >= 4 else
            "Strong" if convergence == 3 else
            "Moderate" if convergence == 2 else
            "Weak"
        ),
    }


def _compute_data_quality(logistics_data, tactics_data, market_data,
                          narrative_home, narrative_away):
    """
    Scores the completeness and reliability of each agent's output.
    Returns a quality grade that tells consumers how much to trust this God View.
    """
    scores = {}

    # Check each agent for key fields
    logistics_keys = ["fatigue_score", "risk", "stamina_impact", "summary"]
    logistics_present = sum(1 for k in logistics_keys if logistics_data.get(k) is not None)
    scores["logistics"] = round(logistics_present / len(logistics_keys), 2)

    tactics_keys = ["team_a_xg", "team_b_xg", "key_battle", "game_script"]
    tactics_present = sum(1 for k in tactics_keys if tactics_data.get(k) is not None)
    scores["tactics"] = round(tactics_present / len(tactics_keys), 2)

    market_keys = ["best_odds", "market_math"]
    market_present = sum(1 for k in market_keys if market_data.get(k) is not None)
    analysis_keys = ["value_score", "edge_percentage", "trap_alert"]
    analysis = market_data.get("analysis", {})
    analysis_present = sum(1 for k in analysis_keys if analysis.get(k) is not None)
    scores["market"] = round((market_present + analysis_present) / (len(market_keys) + len(analysis_keys)), 2)

    narrative_keys = ["score", "morale", "headline", "summary"]
    home_present = sum(1 for k in narrative_keys if narrative_home.get(k) is not None)
    away_present = sum(1 for k in narrative_keys if narrative_away.get(k) is not None)
    scores["narrative"] = round((home_present + away_present) / (len(narrative_keys) * 2), 2)

    overall = round(sum(scores.values()) / len(scores), 2)
    grade = (
        "A" if overall >= 0.9 else
        "B" if overall >= 0.7 else
        "C" if overall >= 0.5 else
        "D"
    )

    return {
        "agent_scores": scores,
        "overall_completeness": overall,
        "grade": grade,
    }


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
        dict: Enterprise-grade God View JSON
    """

    signal_convergence = _compute_signal_convergence(
        logistics_data, tactics_data, market_data, narrative_home, narrative_away
    )
    data_quality = _compute_data_quality(
        logistics_data, tactics_data, market_data, narrative_home, narrative_away
    )

    god_view = {
        # === CORE IDENTIFICATION ===
        "match": f"{home_team} vs {away_team}",
        "home_team": home_team,
        "away_team": away_team,
        "timestamp": datetime.utcnow().isoformat(),

        # === AGENT INTELLIGENCE ===
        "logistics": {
            "branch": logistics_data.get("branch"),
            "route": logistics_data.get("route"),
            "distance_km": logistics_data.get("distance_km"),
            "tz_shift": logistics_data.get("tz_shift"),
            "fatigue_score": logistics_data.get("fatigue_score"),
            "risk": logistics_data.get("risk"),
            "stamina_impact": logistics_data.get("stamina_impact"),
            "summary": logistics_data.get("summary"),
        },

        "tactics": {
            "branch": tactics_data.get("branch"),
            "matchup_styles": tactics_data.get("matchup_styles"),
            "team_a_xg": tactics_data.get("team_a_xg"),
            "team_b_xg": tactics_data.get("team_b_xg"),
            "tactical_adjustments": tactics_data.get("tactical_adjustments"),
            "key_battle": tactics_data.get("key_battle"),
            "game_script": tactics_data.get("game_script"),
        },

        "market": {
            "branch": market_data.get("branch"),
            "best_odds": market_data.get("best_odds"),
            "market_math": {
                "vig": market_data.get("market_math", {}).get("vig"),
                "is_arbitrage": market_data.get("market_math", {}).get("is_arbitrage"),
                "fair_probs": market_data.get("market_math", {}).get("fair_probs"),
            },
            "value_score": market_data.get("analysis", {}).get("value_score"),
            "edge_percentage": market_data.get("analysis", {}).get("edge_percentage"),
            "trap_alert": market_data.get("analysis", {}).get("trap_alert"),
            "sharp_signal": market_data.get("analysis", {}).get("sharp_signal"),
            "best_bet": market_data.get("analysis", {}).get("best_bet"),
        },

        "narrative": {
            "home": {
                "team": narrative_home.get("team"),
                "score": narrative_home.get("score"),
                "morale": narrative_home.get("morale"),
                "adjustment": narrative_home.get("adjustment"),
                "headline": narrative_home.get("headline"),
                "summary": narrative_home.get("summary"),
            },
            "away": {
                "team": narrative_away.get("team"),
                "score": narrative_away.get("score"),
                "morale": narrative_away.get("morale"),
                "adjustment": narrative_away.get("adjustment"),
                "headline": narrative_away.get("headline"),
                "summary": narrative_away.get("summary"),
            },
        },

        "quant": quant_data,

        # === FINAL OUTPUTS ===
        "final_xg": {
            "home": round(final_xg_home, 2),
            "away": round(final_xg_away, 2),
            "total": round(final_xg_home + final_xg_away, 2),
            "differential": round(final_xg_home - final_xg_away, 2),
        },

        # === SIGNAL INTELLIGENCE ===
        "convergence": signal_convergence,

        # === METADATA ===
        "meta": {
            "schema_version": GOD_VIEW_SCHEMA_VERSION,
            "cache_key": match_key,
            "generated_at": datetime.utcnow().isoformat(),
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
            "data_quality": data_quality,
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
        f"✅ God View built for {home_team} vs {away_team} "
        f"(v{GOD_VIEW_SCHEMA_VERSION}, quality={data_quality['grade']}, "
        f"convergence={signal_convergence['conviction_level']})"
    )

    return god_view
