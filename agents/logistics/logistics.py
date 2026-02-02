import math
import json
from datetime import datetime
from core.log import get_logger
from core.initializer.llm import query_llm
from data.scripts.data import get_venue_info

logger = get_logger("Logistics")

class LogisticsAgent:
    """
    PERSONA: The High-Performance Director
    ROLE: Calculates 'Physiological Load' based on travel, biological clocks, and biology.
    """
    def __init__(self):
        self.branch_name = "logistics"

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat/2) * math.sin(dLat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return round(R * c, 1)

    async def analyze(self, prev_venue_name, next_venue_name, days_rest=4):
        """
        Calculates fatigue index based on travel logistics between venues.
        """
        # 1. RETRIEVE HARD DATA
        v1_name, v1 = get_venue_info(prev_venue_name)
        v2_name, v2 = get_venue_info(next_venue_name)

        # 2. CALCULATE VECTORS
        distance = self._haversine(v1['lat'], v1['lon'], v2['lat'], v2['lon'])
        elev_diff = v2.get('elevation', 0) - v1.get('elevation', 0)
        tz_diff = v2.get('tz_offset', 0) - v1.get('tz_offset', 0)
        
        # 3. CIRCADIAN DIRECTIONALITY
        # Traveling East (+ hours deltas are harder)
        direction = "Westward (Easier)" if tz_diff < 0 else "Eastward (Harder)"
        if tz_diff == 0: direction = "Neutral"

        # 4. CLIMATE CONTEXT (Historical Norms for June)
        climate = v2.get('climate_june', {'temp': 25, 'desc': 'Average'})
        
        from prompts.system_prompts import LOGISTICS_PROMPT
        
        user_prompt = f"""
        # JOURNEY LOG
        Route: {v1_name} -> {v2_name}
        Distance: {distance} km
        Travel Direction: {direction} (Time Change: {tz_diff} hours)
        
        # DESTINATION CONDITIONS
        Altitude: {v2.get('elevation')}m (Delta: {elev_diff}m)
        Historical June Climate: {climate['temp']}°C, {climate['desc']}
        
        # RECOVERY CONTEXT
        Days since last match: {days_rest}
        """

        raw_response = await query_llm(LOGISTICS_PROMPT, user_prompt, config_key="logistics")
        
        # 6. PARSING CLEANUP (in case LLM includes markdown)
        clean_json = raw_response.replace("```json", "").replace("```", "").strip()
        
        # 7. PARSE & RETURN
        try:
            analysis_json = json.loads(clean_json)
        except Exception as e:
            logger.error(f"Failed to parse Logistics LLM response: {e}. Raw: {raw_response}")
            # Fallback if LLM creates malformed JSON
            analysis_json = {
                "fatigue_score": 5, 
                "primary_risk": "Unknown", 
                "analysis": "Error parsing detailed analysis. Defaulting to baseline fatigue."
            }

        return {
            "branch": self.branch_name,
            "route": f"{v1_name.split(',')[0]} > {v2_name.split(',')[0]}",
            "distance_km": distance,
            "tz_shift": tz_diff,
            "fatigue_score": analysis_json.get('fatigue_score', 5),
            "risk": analysis_json.get('primary_risk', 'None'),
            "stamina_impact": analysis_json.get('stamina_impact', 'Minimal'),
            "summary": analysis_json.get('analysis_summary', analysis_json.get('analysis', "N/A")),
            "reasoning": analysis_json.get('reasoning', "N/A")
        }
