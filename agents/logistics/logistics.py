import math
import logging
from core.llm import query_llm
from .weather_api import get_forecast

VENUES = {
    'MetLife_NY': {'lat': 40.8135, 'lon': -74.0745, 'altitude': 2},
    'Azteca_Mexico': {'lat': 19.3029, 'lon': -99.1505, 'altitude': 2240},
}

class LogisticsAgent:
    """
    PERSONA: Logistics AI Agent
    ROLE: Analyzes flight data, weather patterns, and physiological impact.
    """
    def __init__(self):
        self.branch_name = "logistics"

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        R = 6371
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat/2) * math.sin(dLat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c

    async def analyze(self, venue1_key, venue2_key, cumulative_matches=1):
        v1 = VENUES.get(venue1_key, VENUES['MetLife_NY'])
        v2 = VENUES.get(venue2_key, VENUES['Azteca_Mexico'])
        
        distance = self.haversine_distance(v1['lat'], v1['lon'], v2['lat'], v2['lon'])
        alt_diff = v2['altitude'] - v1['altitude']
        
        # Use API to get context
        weather = get_forecast(v2['lat'], v2['lon'])
        weather_context = f"Avg Temp: {weather['avg_temp_c']}°C, Condition: {weather['condition']}, Altitude: {v2['altitude']}m"
        
        system_prompt = """
        You are the Logistics Expert for a sports analytics firm.
        Assess the impact of travel and environment on a professional soccer team.
        Consider: Distance traveled, Time Zones, Altitude, and Temperature.
        Output a 'Fatigue Score' (0-10) and a brief strategic advice.
        """
        
        user_prompt = f"""
        Travel: {distance:.1f} km.
        Altitude Change: {alt_diff}m.
        Target Conditions: {weather_context}.
        Previous Matches in 2 weeks: {cumulative_matches}.
        """
        
        llm_insight = await query_llm(system_prompt, user_prompt)
        
        return {
            "branch": self.branch_name,
            "travel_km": round(distance, 1),
            "altitude_change": alt_diff,
            "recommendation": llm_insight[:200] + "...",
            "full_analysis": llm_insight
        }
