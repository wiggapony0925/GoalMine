import requests
from core.log import get_logger

logger = get_logger("API.OpenMeteo")

# WMO Weather interpretation codes (https://open-meteo.com/en/docs)
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def get_forecast(lat, lon):
    """
    Fetches weather data from Open-Meteo (Free, No API Key).
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "hourly": "temperature_2m,relativehumidity_2m",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data.get("current_weather", {})
        elevation = data.get("elevation", 0)  # Open-Meteo returns elevation!
        weather_code = current.get("weathercode", -1)

        return {
            "avg_temp_c": current.get("temperature"),
            "condition": WMO_CODES.get(weather_code, f"Unknown (code {weather_code})"),
            "wind_kph": current.get("windspeed"),
            "elevation": elevation,
        }
    except Exception as e:
        logger.error(f"Error fetching Open-Meteo: {e}")
        # Fallback Mock
        return {
            "avg_temp_c": 20.0,
            "condition": "Unknown",
            "wind_kph": 10.0,
            "elevation": 0,
        }
