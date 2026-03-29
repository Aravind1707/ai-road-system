import requests

OSM_NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"


def reverse_geocode(lat: float, lon: float, zoom: int = 18, addressdetails: int = 1):
    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2",
        "zoom": zoom,
        "addressdetails": addressdetails
    }
    headers = {"User-Agent": "RoadAI/1.0"}
    r = requests.get(OSM_NOMINATIM_URL, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()


def get_road_name_from_gps(lat: float, lon: float):
    try:
        data = reverse_geocode(lat, lon)
        road = data.get("address", {}).get("road")
        if not road:
            road = data.get("address", {}).get("pedestrian")
        if not road:
            road = data.get("address", {}).get("highway")
        return road
    except Exception:
        return None
