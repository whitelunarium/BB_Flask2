# app/services/risk_service.py
# Responsibility: Risk assessment logic — fire, flood, and heat scoring from Open-Meteo.
# PPR ML COMPONENT: risk scoring algorithms are documented as the machine learning feature.
# ORCHESTRATOR: get_risk_assessment() — calls all three workers, assembles response.
# WORKERS: compute_fire_risk(), compute_flood_risk(), compute_heat_risk()

import time
import requests
from flask import current_app

# ─── Module-level cache (process-scoped, 30 min TTL) ─────────────────────────
_risk_cache = {
    'data': None,
    'expires_at': 0,
}


def get_risk_assessment():
    """
    Purpose: ORCHESTRATOR — return a cached risk assessment, refreshing if stale.
    @returns {dict} { fire_score, flood_score, heat_score, conditions, updated_at }
    Algorithm:
    1. Check if cache is still valid (TTL not expired)
    2. If valid: return cached result immediately
    3. If stale: fetch fresh conditions from Open-Meteo
    4. Compute all three risk scores
    5. Store in cache with new expiry and return
    """
    now = time.time()
    if _risk_cache['data'] and _risk_cache['expires_at'] > now:
        return _risk_cache['data']

    conditions = _fetch_poway_conditions()
    result = _assemble_risk_response(conditions)

    _risk_cache['data'] = result
    _risk_cache['expires_at'] = now + current_app.config.get('RISK_CACHE_SECONDS', 1800)
    return result


def _fetch_poway_conditions():
    """
    Purpose: WORKER — retrieve current weather conditions for Poway from Open-Meteo.
    @returns {dict} Parsed conditions dict, or fallback defaults on error
    Algorithm:
    1. Build Open-Meteo API URL with Poway coordinates
    2. Request current + daily fields
    3. Parse response into a flat conditions dict
    4. Return fallback on any exception
    """
    lat = current_app.config.get('POWAY_LAT', 32.9628)
    lon = current_app.config.get('POWAY_LON', -117.0359)
    url = current_app.config.get('OPEN_METEO_URL', 'https://api.open-meteo.com/v1/forecast')

    params = {
        'latitude':  lat,
        'longitude': lon,
        'current':   'temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation',
        'daily':     'precipitation_sum',
        'temperature_unit': 'fahrenheit',
        'wind_speed_unit':  'mph',
        'precipitation_unit': 'inch',
        'forecast_days': 8,
        'timezone': 'America/Los_Angeles',
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return _parse_open_meteo_response(resp.json())
    except Exception:
        return _fallback_conditions()


def _parse_open_meteo_response(data):
    """
    Purpose: WORKER — extract relevant fields from the Open-Meteo JSON response.
    @param {dict} data - Raw Open-Meteo API response dict
    @returns {dict} Flat conditions dict with temp_f, humidity, wind_mph, precip_in, rain_7d_in
    Algorithm:
    1. Pull current weather values
    2. Sum last 7 days of precipitation from daily array
    3. Return normalized dict
    """
    current = data.get('current', {})
    daily   = data.get('daily', {})

    temp_f   = current.get('temperature_2m', 72)
    humidity = current.get('relative_humidity_2m', 50)
    wind_mph = current.get('wind_speed_10m', 0)
    precip   = current.get('precipitation', 0)

    # Sum of last 7 days precipitation (indices 0–6)
    daily_precip = daily.get('precipitation_sum', [])
    rain_7d = sum(v for v in daily_precip[:7] if v is not None)

    return {
        'temp_f':    round(temp_f, 1),
        'humidity':  round(humidity, 1),
        'wind_mph':  round(wind_mph, 1),
        'precip_in': round(precip, 2),
        'rain_7d_in': round(rain_7d, 2),
    }


def _fallback_conditions():
    """Return safe default conditions used when the API call fails."""
    return {'temp_f': 72, 'humidity': 50, 'wind_mph': 5, 'precip_in': 0, 'rain_7d_in': 0}


def compute_fire_risk(conditions):
    """
    Purpose: WORKER — compute a 0–10 fire risk score from current conditions.
    @param {dict} conditions - Flat conditions dict from _parse_open_meteo_response
    @returns {int} Fire risk score 0–10
    Algorithm:
    PPR ML SCORING — additive risk factor model:
    - Temperature > 90°F:  +3 points (high heat dries vegetation)
    - Humidity < 20%:      +3 points (low humidity raises ignition probability)
    - Wind > 25 mph:       +2 points (wind spreads fire rapidly)
    - No rain 7 days:      +2 points (dry fuel accumulation)
    Score is clamped to [0, 10].
    """
    score = 0
    if conditions['temp_f'] > 90:
        score += 3
    if conditions['humidity'] < 20:
        score += 3
    if conditions['wind_mph'] > 25:
        score += 2
    if conditions['rain_7d_in'] < 0.1:
        score += 2
    return min(score, 10)


def compute_flood_risk(conditions):
    """
    Purpose: WORKER — compute a 0–10 flood risk score from current conditions.
    @param {dict} conditions - Flat conditions dict
    @returns {int} Flood risk score 0–10
    Algorithm:
    PPR ML SCORING — additive risk factor model:
    - Current precip > 0.5 in/hr: +4 points (active heavy rain)
    - 7-day total > 1 inch:       +3 points (saturated ground)
    - Temperature near freezing:  +1 point  (impervious frozen ground)
    Score is clamped to [0, 10].
    """
    score = 0
    if conditions['precip_in'] > 0.5:
        score += 4
    if conditions['rain_7d_in'] > 1.0:
        score += 3
    if conditions['temp_f'] <= 35:
        score += 1
    return min(score, 10)


def compute_heat_risk(conditions):
    """
    Purpose: WORKER — compute a heat index score from temperature and humidity.
    @param {dict} conditions - Flat conditions dict
    @returns {dict} { heat_index_f, score } where score is 0–10
    Algorithm:
    PPR ML SCORING — simplified Rothfusz heat index formula:
    HI = -42.379 + 2.049*T + 10.142*RH - 0.225*T*RH - 0.006837*T² - 0.0548*RH²
         + 0.001228*T²*RH + 0.0008528*T*RH² - 0.000001991*T²*RH²
    Score: HI < 80 → 0, 80–90 → 3, 90–103 → 6, > 103 → 9
    """
    T  = conditions['temp_f']
    RH = conditions['humidity']

    hi = (-42.379
          + 2.04901523 * T
          + 10.14333127 * RH
          - 0.22475541 * T * RH
          - 0.00683783 * T * T
          - 0.05481717 * RH * RH
          + 0.00122874 * T * T * RH
          + 0.00085282 * T * RH * RH
          - 0.00000199 * T * T * RH * RH)

    hi = max(hi, T)  # heat index can't be lower than actual temp

    if hi >= 103:
        score = 9
    elif hi >= 90:
        score = 6
    elif hi >= 80:
        score = 3
    else:
        score = 0

    return {'heat_index_f': round(hi, 1), 'score': score}


def _assemble_risk_response(conditions):
    """
    Purpose: ORCHESTRATOR — call all three risk workers and assemble the final response dict.
    @param {dict} conditions - Parsed weather conditions
    @returns {dict} Complete risk assessment payload
    Algorithm:
    1. Compute fire, flood, and heat scores
    2. Label each with human-readable severity
    3. Return combined dict with conditions and timestamp
    """
    fire_score  = compute_fire_risk(conditions)
    flood_score = compute_flood_risk(conditions)
    heat_data   = compute_heat_risk(conditions)

    return {
        'fire_score':    fire_score,
        'fire_level':    _score_label(fire_score),
        'flood_score':   flood_score,
        'flood_level':   _score_label(flood_score),
        'heat_score':    heat_data['score'],
        'heat_level':    _score_label(heat_data['score']),
        'heat_index_f':  heat_data['heat_index_f'],
        'conditions':    conditions,
        'updated_at':    int(time.time()),
    }


def _score_label(score):
    """Map a 0–10 score to a human-readable severity label."""
    if score <= 2:
        return 'LOW'
    if score <= 4:
        return 'MODERATE'
    if score <= 7:
        return 'HIGH'
    return 'CRITICAL'
