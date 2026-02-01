import math
import logging
from core.llm import query_llm
from .api.open_meteo import get_forecast

VENUES = {
    'MetLife_NY': {'lat': 40.8135, 'lon': -74.0745},
    'Azteca_Mexico': {'lat': 19.3029, 'lon': -99.1505},
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
        
        weather_context = "Data Unavailable"
        alt_diff = 0
        source = "LIVE_METEO"
        
        try:
            weather_v2 = get_forecast(v2['lat'], v2['lon'])
            weather_v1 = get_forecast(v1['lat'], v1['lon'])
            alt_diff = weather_v2['elevation'] - weather_v1['elevation']
            weather_context = f"Temp: {weather_v2['avg_temp_c']}°C, Cond: {weather_v2['condition']}, Elev: {weather_v2['elevation']}m"
        except Exception:
            source = "GEOGRAPHIC_ESTIMATE"
            weather_context = "Live Weather Offline. Estimate based on June Averages for this Latitude."

        system_prompt = """
        IDENTITY: You are 'Mission Control' for Logistics & Performance.
        MISSION: Calculate the physiological toll of travel and environment on the athletes.
        
        DATA SOURCE: {source}
        
        FACTORS TO WEIGH:
        1. **Altitude Shock**: Every 500m gain = significant aerobic penalty.
        2. **Travel Fatigue**: >2000km flights = circadian disruption.
        3. **Heat Stress**: If temp > 28C, performance drops 15%.
        
        OUTPUT:
        - Fatigue Score (0-10)
        - Strategic Advice: (e.g., "Home team advantage magnified by altitude.")
        """
        
        user_prompt = f"""
        Route: {venue1_key} -> {venue2_key} ({distance:.1f} km).
        Elevation Delta: {alt_diff}m.
        Conditions: {weather_context}.
        Recent Workload: {cumulative_matches} matches / 2 weeks.
        """
        
        llm_insight = await query_llm(system_prompt.format(source=source), user_prompt)
        
        return {
            "branch": self.branch_name,
            "travel_km": round(distance, 1),
            "altitude_change": round(alt_diff, 1),
            "weather_source": source,
            "recommendation": llm_insight[:200] + "...",
            "full_analysis": llm_insight
        }
