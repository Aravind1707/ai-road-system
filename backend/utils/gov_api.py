import requests
from .config import AUTHORITY_EMAIL

# Endpoint placeholders for government integration
GOV_API_URL = "https://gov-portal.example.com/api/v1/road-complaints"


def send_gov_report(data: dict):
    try:
        response = requests.post(GOV_API_URL, json=data, timeout=12)
        response.raise_for_status()
        return True, response.json()
    except Exception as exc:
        return False, str(exc)
