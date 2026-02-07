import asyncio
import re
import json
from core.log import get_logger
from core.initializer.llm import query_llm
from core.utils import clean_markdown_json
from .api.sportmonks import fetch_team_stats

logger = get_logger("Tactics")


class TacticsAgent:
    """
    PERSONA: The Tactical Architect (AI Analyst)
    ROLE: Merges 'Hard Data' (Baseline xG) with 'Soft Factors' (Tactical Mismatches).
    """

    def __init__(self):
        self.branch_name = "tactics"

    async def analyze(self, team_a_id, team_b_id):
        # 1. DATA ACQUISITION
        data_a, data_b = await self._fetch_data_safely(team_a_id, team_b_id)

        # 2. DETERMINISTIC MODEL (The "Hard" Baseline)
        # We calculate the 'Paper Expectation' before looking at tactics.
        # Formula: (Team A Attack Strength + Team B Defense Weakness) / 2
        base_xg_a = (
            data_a.get("xg_for_avg", 1.35) + data_b.get("xg_against_avg", 1.35)
        ) / 2
        base_xg_b = (
            data_b.get("xg_for_avg", 1.15) + data_a.get("xg_against_avg", 1.15)
        ) / 2

        # 3. TACTICAL CONTEXT INJECTION
        # We define specific styles to help the LLM visualize the game.
        style_a = data_a.get("style", "Balanced")
        style_b = data_b.get("style", "Balanced")

        from prompts.system_prompts import TACTICS_PROMPT

        user_prompt = f"""
        Analyze {data_a["name"]} vs {data_b["name"]}.
        
        Team A Lineup Notes: {data_a.get("key_players", "Standard")}
        Team B Lineup Notes: {data_b.get("key_players", "Standard")}
        
        Recent Form A: {data_a.get("form", "Unknown")}
        Recent Form B: {data_b.get("form", "Unknown")}
        """

        # 4. EXECUTE ANALYSIS
        formatted_sys = TACTICS_PROMPT.format(
            style_a=style_a, style_b=style_b, base_a=base_xg_a, base_b=base_xg_b
        )

        response = await query_llm(
            formatted_sys, user_prompt, config_key="tactics", json_mode=True
        )

        # 5. PARSE & SYNTHESIZE
        try:
            analysis = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed despite json_mode: {e}")
            analysis = self._parse_tactical_json(response)

        # Apply the tactical modifiers to the mathematical baseline
        adj_a = analysis.get("xg_adjustment_a", 0.0)
        adj_b = analysis.get("xg_adjustment_b", 0.0)
        final_xg_a = max(0.1, base_xg_a + adj_a)
        final_xg_b = max(0.1, base_xg_b + adj_b)

        return {
            "branch": self.branch_name,
            "matchup_styles": f"{style_a} vs {style_b}",
            "base_xg": {"a": round(base_xg_a, 2), "b": round(base_xg_b, 2)},
            "team_a_xg": round(final_xg_a, 2),
            "team_b_xg": round(final_xg_b, 2),
            "tactical_adjustments": {"a": adj_a, "b": adj_b},
            "tactical_analysis": analysis.get(
                "tactical_logic", analysis.get("tactical_summary", "N/A")
            ),
            "key_battle": analysis.get("key_battle", "N/A"),
            "game_script": analysis.get(
                "game_script", analysis.get("game_openness", "N/A")
            ),
            "reasoning": analysis.get("tactical_logic", "N/A"),
        }

    async def _fetch_data_safely(self, id_a, id_b):
        """Fetches data or returns 'League Average' defaults on failure."""
        try:
            raw_a = await asyncio.to_thread(fetch_team_stats, id_a)
            raw_b = await asyncio.to_thread(fetch_team_stats, id_b)
            return raw_a, raw_b
        except Exception as e:
            logger.warning(f"Tactics Data Fetch Failed: {e}. Using league averages.")
            # Fallback Data Structure
            default_a = {
                "name": id_a,
                "xg_for_avg": 1.35,
                "xg_against_avg": 1.35,
                "style": "Balanced",
                "form": "Average",
                "key_players": "Standard XI",
            }
            default_b = {
                "name": id_b,
                "xg_for_avg": 1.15,
                "xg_against_avg": 1.15,
                "style": "Balanced",
                "form": "Average",
                "key_players": "Standard XI",
            }
            return default_a, default_b

    def _parse_tactical_json(self, response_text):
        """
        Extracts JSON from LLM response using Regex to find the JSON block.
        Includes default fallbacks if the LLM ignores instructions.
        """
        # Default fallback
        data = {
            "tactical_summary": "Standard tactical matchup with balanced approaches.",
            "key_battle": "Midfield Control",
            "xg_adjustment_a": 0.0,
            "xg_adjustment_b": 0.0,
            "game_openness": "Standard",
        }

        try:
            # Clean markdown code blocks if present
            clean_text = clean_markdown_json(response_text)

            # Regex to find the JSON structure specifically
            match = re.search(r"\{.*\}", clean_text, re.DOTALL)
            if match:
                json_str = match.group(0)
                parsed = json.loads(json_str)
                data.update(parsed)
        except Exception as e:
            logger.warning(f"Failed to parse tactical JSON: {e}. Using fallback regex.")
            # If JSON parse fails, we can try a backup regex for specific numbers
            try:
                # Fallback: Find "xg_adjustment_a": 0.3 pattern
                adj_a = re.search(
                    r'"xg_adjustment_a":\s*([+-]?\d*\.?\d+)', response_text
                )
                if adj_a:
                    data["xg_adjustment_a"] = float(adj_a.group(1))

                adj_b = re.search(
                    r'"xg_adjustment_b":\s*([+-]?\d*\.?\d+)', response_text
                )
                if adj_b:
                    data["xg_adjustment_b"] = float(adj_b.group(1))
            except Exception as e2:
                logger.warning(f"Regex fallback also failed: {e2}. Using defaults.")

        return data
