import math
import logging
from core.llm import query_llm
from .api.open_meteo import get_forecast

VENUES = {
    'Estadio Azteca, Mexico City': {'lat': 19.3029, 'lon': -99.1505},
    'Estadio Guadalajara, Guadalajara': {'lat': 20.6811, 'lon': -103.4504},
    'BC Place, Vancouver': {'lat': 49.2767, 'lon': -123.1119},
    'SoFi Stadium, Los Angeles': {'lat': 33.9534, 'lon': -118.3387},
    'BMO Field, Toronto': {'lat': 43.6333, 'lon': -79.4186},
    'Gillette Stadium, Boston': {'lat': 42.0909, 'lon': -71.2643},
    'MetLife Stadium, East Rutherford': {'lat': 40.8135, 'lon': -74.0745},
    'Levi\'s Stadium, San Francisco Bay Area': {'lat': 37.403, 'lon': -121.97},
    'Lincoln Financial Field, Philadelphia': {'lat': 39.9008, 'lon': -75.1675},
    'NRG Stadium, Houston': {'lat': 29.6847, 'lon': -95.4107},
    'AT&T Stadium, Dallas': {'lat': 32.7473, 'lon': -97.0945},
    'Estadio Monterrey, Monterrey': {'lat': 25.669, 'lon': -100.245},
    'Hard Rock Stadium, Miami': {'lat': 25.958, 'lon': -80.238},
    'Mercedes-Benz Stadium, Atlanta': {'lat': 33.755, 'lon': -84.401},
    'Lumen Field, Seattle': {'lat': 47.595, 'lon': -122.332}
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
        v1 = VENUES.get(venue1_key, VENUES['MetLife Stadium, East Rutherford'])
        v2 = VENUES.get(venue2_key, VENUES['Estadio Azteca, Mexico City'])
        
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
        # IDENTITY: GoalMine Mission Control (Logistics & Performance AI)
        
        # MISSION
        Synthesize geographic, environmental, and travel data to calculate the 'Physiological Toll' on professional athletes. Your analysis determines the hidden physical fatigue that standard betting markets often miss.

        # DATA SOURCE: {source}

        # OPERATIONAL FACTORS
        1. **ALTITUDE SHOCK**: 
           - Every 500m gain above sea level increases VO2 max strain.
           - Above 2,000m (e.g., Mexico City), unacclimatized teams face a -15% performance penalty in the final 20 minutes.
        2. **CIRCADIAN DISRUPTION (Jet Lag)**:
           - Flights crossing >2 time zones or >2,000km distances induce 'Heavy Legs' syndrome.
           - Eastward travel is harder to recover from than Westward.
        3. **THERMAL STRAIN**:
           - Temperatures >28°C (82°F) trigger metabolic cooling penalties.
           - High humidity (>70%) prevents evaporation—fatigue accumulates 2x faster.
        4. **WORKLOAD ACCUMULATION**:
           - High-density schedules (3 games in 10 days) lead to nonlinear injury risk spikes.

        # OUTPUT REQUIREMENTS
        - **Fatigue Score**: (Scale 0-10, where 10 is 'Exhausted/High Risk').
        - **Logistics Edge**: Who benefits from the travel/weather? (Home/Away/None).
        - **Operational Summary**: A sharp, technical brief on the primary environmental inhibitor.
        """
        
        user_prompt = f"""
        Route: {venue1_key} -> {venue2_key} ({distance:.1f} km).
        Elevation Delta: {alt_diff}m.
        Conditions: {weather_context}.
        Recent Workload: {cumulative_matches} matches / 2 weeks.
        """
        
        llm_insight = await query_llm(system_prompt.format(source=source), user_prompt)
        
        # Structured extraction of fatigue score
        fatigue_score = 5
        try:
            # Look for number in brackets or after colon
            import re
            score_match = re.search(r"Fatigue Score:\s*(\d+)", llm_insight)
            if score_match: fatigue_score = int(score_match.group(1))
        except: pass

        return {
            "branch": self.branch_name,
            "fatigue_score": fatigue_score,
            "travel_km": round(distance, 1),
            "altitude_change": round(alt_diff, 1),
            "weather_source": source,
            "recommendation": llm_insight[:200] + "...",
            "full_analysis": llm_insight
        }
