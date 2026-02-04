"""
Unified Bet Generation Engine for GoalMine.
Uses COMPLETE God View intelligence + all data sources.
Shared by BOTH Button Flow and Conversational Flow.
"""

import json
from core.log import get_logger
from core.initializer.llm import query_llm
from core.initializer.database import Database
from data.scripts.data import BET_TYPES

logger = get_logger("BetGenerator")


async def generate_bet_recommendations(
    num_bets=3, user_phone=None, conversational_mode=False, user_question=None
):
    """
    UNIFIED BET GENERATION ENGINE

    Uses the complete God View intelligence matrix:
    - Logistics (fatigue, altitude, travel)
    - Tactics (xG, style matchups)
    - Market (odds, edges, value)
    - Narrative (morale, injuries, sentiment)
    - Quant (Kelly Criterion, top plays)

    Args:
        num_bets (int): Number of bet recommendations to generate
        user_phone (str): User's phone number to retrieve their god_view from DB
        conversational_mode (bool): If True, use strategic advisor style. If False, use strict format.
        user_question (str): Optional - specific question from user (e.g., "Should I parlay this?")

    Returns:
        str: Formatted bet recommendations or error message
    """
    if not user_phone:
        logger.error("❌ user_phone is required for bet generation")
        return "⚠️ System error: User identification required."

    # Load user's complete god_view from database
    db = Database()
    user_state = db.load_memory(user_phone)

    if not user_state or not user_state.get("god_view"):
        logger.warning(f"No god_view found in DB for {user_phone}")
        return "⚠️ No recent analysis found. Please analyze a match first."

    god_view = user_state["god_view"]
    match_title = god_view.get("match", "Unknown Match")

    # ========================================================================
    # BUILD COMPREHENSIVE INTELLIGENCE PACKAGE
    # ========================================================================

    intelligence_package = {
        # CORE GOD VIEW DATA
        "match": match_title,
        "final_xg": god_view.get("final_xg", {}),
        # AGENT OUTPUTS (Full Data)
        "logistics": god_view.get("logistics", {}),
        "tactics": god_view.get("tactics", {}),
        "market": god_view.get("market", {}),
        "narrative": god_view.get("narrative", {}),
        "quant": god_view.get("quant", {}),
        # METADATA
        "timestamp": god_view.get("timestamp"),
        "agents_status": god_view.get("agents_status", {}),
        # AVAILABLE BET TYPES
        "bet_catalog": BET_TYPES,
        # USER CONTEXT
        "user_budget": user_state.get("budget", 100),
        "requested_bets": num_bets,
    }

    # ========================================================================
    # SELECT PROMPT BASED ON MODE
    # ========================================================================

    from prompts.system_prompts import BET_GENERATOR_PROMPT, STRATEGIC_ADVISOR_PROMPT

    if conversational_mode and user_question:
        # User asked a specific strategy question
        system_prompt = STRATEGIC_ADVISOR_PROMPT.format(
            god_view=json.dumps(intelligence_package, indent=2)
        )
        user_prompt = user_question
        logger.info(f"💡 Strategic Advisor Mode: {user_question[:50]}...")

    else:
        # Standard bet generation (Button flow or simple "give me X bets")
        system_prompt = BET_GENERATOR_PROMPT.format(
            num_bets=num_bets, intelligence=json.dumps(intelligence_package, indent=2)
        )
        user_prompt = f"Generate {num_bets} high-value betting recommendations using ALL available intelligence."
        logger.info(f"🎯 Unified Bet Generator: {num_bets} bets requested")

    # ========================================================================
    # EXECUTE LLM GENERATION
    # ========================================================================

    try:
        response = await query_llm(
            system_prompt=system_prompt,
            user_content=user_prompt,
            config_key="closer",
            temperature=0.5,
        )

        # ========================================================================
        # EXTRACT & LOG PREDICTIONS FOR ROI AUDIT
        # ========================================================================
        clean_response = response
        if "JSON_START" in response and "JSON_END" in response:
            try:
                # Extract JSON block
                json_part = response.split("JSON_START")[1].split("JSON_END")[0].strip()
                predictions = json.loads(json_part)

                # Log each prediction to DB
                match_id = god_view.get("meta", {}).get("cache_key", "unknown_match")
                for p in predictions:
                    db.log_bet_prediction(user_phone, match_id, p)

                # Clean the response for WhatsApp (STRICT STRIP)
                clean_response = response.split("JSON_START")[0].strip()
                if "---" in clean_response:
                    # Remove the last separator and everything after it (the audit label)
                    clean_response = "---".join(
                        clean_response.split("---")[:-1]
                    ).strip()
            except Exception as pe:
                logger.error(f"Failed to parse/log structured predictions: {pe}")

        # Format output based on mode
        if conversational_mode:
            return clean_response
        else:
            return f"🎰 *Bet Recommendations for {match_title}*\n\n{clean_response}"

    except Exception as e:
        logger.error(f"Unified Bet Generator failed: {e}")
        return "⚠️ Failed to generate bets. Please try again."


async def generate_strategic_advice(user_phone, question):
    """
    Wrapper for conversational strategic questions.
    Uses the same unified engine with conversational mode enabled.

    Examples:
    - "Should I parlay this?"
    - "Give me 5 alternative bets"
    - "How should I split my $200 budget?"
    """
    return await generate_bet_recommendations(
        num_bets=3,  # Default, will be overridden by question context
        user_phone=user_phone,
        conversational_mode=True,
        user_question=question,
    )
