import requests
from core.log import get_logger

logger = get_logger("API.OpenMeteo")


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
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        current = data.get("current_weather", {})
        elevation = data.get("elevation", 0)  # Open-Meteo returns elevation!

        return {
            "avg_temp_c": current.get("temperature"),
            "condition": "Code "
            + str(
                current.get("weathercode")
            ),  # Weather codes need mapping, simple for now
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
