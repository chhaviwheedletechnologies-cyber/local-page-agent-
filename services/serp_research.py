import os
import requests
from dotenv import load_dotenv

load_dotenv()

SERP_API_KEY = os.getenv("SERP_API_KEY")
SERP_URL = "https://serpapi.com/search.json"


def search_serp(keyword: str, location: str):

    if not SERP_API_KEY:
        return {
            "status": "not_configured",
            "keyword": keyword,
            "location": location,
            "results": [],
            "total_results": 0,
            "error": "SERP_API_KEY is not configured"
        }

    params = {
        "engine": "google",
        "q": keyword,
        "location": location,
        "api_key": SERP_API_KEY,
        "num": 10
    }

    try:
        response = requests.get(
            SERP_URL,
            params=params,
            timeout=30
        )

        # IMPORTANT:
        # Do not retry 429 repeatedly.
        if response.status_code == 429:
            try:
                data = response.json()
                error_message = data.get(
                    "error",
                    "SerpAPI rate limit or search quota exceeded"
                )
            except Exception:
                error_message = (
                    "SerpAPI returned HTTP 429. "
                    "Hourly limit or search quota may be exceeded."
                )

            return {
                "status": "rate_limited",
                "keyword": keyword,
                "location": location,
                "results": [],
                "total_results": 0,
                "error": error_message,
                "http_status": 429
            }

        response.raise_for_status()

        data = response.json()

        if data.get("error"):
            return {
                "status": "error",
                "keyword": keyword,
                "location": location,
                "results": [],
                "total_results": 0,
                "error": data.get("error")
            }

        organic_results = data.get("organic_results", [])

        results = []

        for item in organic_results[:10]:
            results.append({
                "position": item.get("position"),
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet")
            })

        return {
            "status": "success",
            "keyword": keyword,
            "location": location,
            "results": results,
            "total_results": len(results),
            "error": None
        }

    except requests.exceptions.Timeout:
        return {
            "status": "timeout",
            "keyword": keyword,
            "location": location,
            "results": [],
            "total_results": 0,
            "error": "SERP API request timed out"
        }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "keyword": keyword,
            "location": location,
            "results": [],
            "total_results": 0,
            "error": str(e)
        }

    except ValueError as e:
        return {
            "status": "error",
            "keyword": keyword,
            "location": location,
            "results": [],
            "total_results": 0,
            "error": "Invalid JSON response: " + str(e)
        }

    except Exception as e:
        return {
            "status": "error",
            "keyword": keyword,
            "location": location,
            "results": [],
            "total_results": 0,
            "error": str(e)
        }