import os
import requests
from datetime import date

BASE_URL = "https://calendarific.com/api/v2/holidays"

def fetch_day_speciality_from_api(date_obj, country="IN"):
    """
    Fetches official holiday/special day from Calendarific
    """
    api_key = os.environ.get("CALENDARIFIC_API_KEY")

    if not api_key:
        return None

    params = {
        "api_key": api_key,
        "country": country,
        "year": date_obj.year,
        "month": date_obj.month,
        "day": date_obj.day,
    }

    try:
        res = requests.get(BASE_URL, params=params, timeout=8)
        res.raise_for_status()
        data = res.json()

        holidays = data.get("response", {}).get("holidays", [])

        if not holidays:
            return None

        h = holidays[0]

        title = h.get("name")
        description = h.get("description", title)

        poster_hint = (
            f"Create a modern poster for {title}. "
            f"Theme: celebration, clean typography, festive colors."
        )

        return {
            "title": title,
            "description": description,
            "poster_hint": poster_hint,
        }

    except Exception:
        return None
