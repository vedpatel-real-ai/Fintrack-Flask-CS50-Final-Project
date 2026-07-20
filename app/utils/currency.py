"""
Currency conversion helpers.

Wraps the exchangerate-api.com API. If no API key is configured, or the
request fails for any reason (network issue, invalid key, rate limit),
these functions fall back to a 1:1 rate instead of crashing a page --
a missing third-party API should degrade the app, not break it.
"""

import requests
from flask import current_app

SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "INR"]


def get_exchange_rates(base_currency="USD"):
    api_key = current_app.config.get("EXCHANGE_RATE_API_KEY")
    if not api_key:
        return {}

    base_url = current_app.config["EXCHANGE_RATE_BASE_URL"]
    url = f"{base_url}{api_key}/latest/{base_currency}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json().get("conversion_rates", {})
    except requests.RequestException:
        return {}


def get_conversion_rate(from_currency, to_currency):
    if from_currency == to_currency:
        return 1.0
    rates = get_exchange_rates(from_currency)
    return rates.get(to_currency, 1.0)


def convert_amount(amount, from_currency, to_currency):
    return float(amount) * get_conversion_rate(from_currency, to_currency)
