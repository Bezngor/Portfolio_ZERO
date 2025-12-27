import requests
from dotenv import load_dotenv
import os
load_dotenv()
CURRENCY_ACCESS_KEY = os.getenv("CURRENCY_ACCESS_KEY")


def get_current_rate(default: str = "RUB", currency: list[str] = ["USD", "EUR", "CNY"]):

    
    url = "https://api.exchangerate.host/live"
    params = {
        "access_key": CURRENCY_ACCESS_KEY,
        "source": default, 
        "currencies": ",".join(currency)
        }
    response = requests.get(url, params=params)
    data = response.json()
    return data


def convert_currency(amount: float, from_currency: str, to_currency: str):

    """ Конвертирует одну валюту в другую.
    Возвращает словарь с результатом конвертации.
    Пример:
    {'success': True, 'terms': 'https://currencylayer.com/terms', 'privacy': 'https://currencylayer.com/privacy', 'query': {'from': 'USD', 'to': 'RUB', 'amount': 100}, 'info': {'timestamp': 1766827266, 'quote': 79.007431}, 'result': 7900.7431}
    """

    url = "https://api.exchangerate.host/convert"
    params = {
        "access_key": CURRENCY_ACCESS_KEY,
        "from": from_currency,
        "to": to_currency,
        "amount": amount
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data


def get_all_supported_currencies():
    url = "https://api.exchangerate.host/list"
    params = {
        "access_key": CURRENCY_ACCESS_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data


if __name__ == "__main__":
    print(convert_currency(amount=100, from_currency="USD", to_currency="RUB"))