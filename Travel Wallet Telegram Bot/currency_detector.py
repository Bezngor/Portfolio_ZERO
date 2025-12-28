"""
Currency detection helper
Helps find currency codes for countries using API
"""

import requests
import os
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

CURRENCY_ACCESS_KEY = os.getenv("CURRENCY_ACCESS_KEY")


def get_all_currencies() -> Dict[str, str]:
    """Get all supported currencies from API"""
    try:
        url = "https://api.exchangerate.host/list"
        params = {"access_key": CURRENCY_ACCESS_KEY}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('success'):
            return data.get('currencies', {})
        return {}
    except Exception as e:
        logger.error(f"Error fetching currencies: {e}")
        return {}


def find_currency_by_country(country_name: str) -> Optional[str]:
    """
    Try to find currency code by country name
    Uses common patterns and API currency list
    """
    country_lower = country_name.lower().strip()
    
    # Common country-currency mappings
    common_mappings = {
        # Базовые популярные страны
        'россия': 'RUB', 'russia': 'RUB',
        'сша': 'USD', 'usa': 'USD', 'америка': 'USD', 'america': 'USD',
        'великобритания': 'GBP', 'uk': 'GBP', 'англия': 'GBP', 'england': 'GBP',
        'европа': 'EUR', 'europe': 'EUR', 'ес': 'EUR', 'eu': 'EUR',
        'германия': 'EUR', 'germany': 'EUR',
        'франция': 'EUR', 'france': 'EUR',
        'италия': 'EUR', 'italy': 'EUR',
        'испания': 'EUR', 'spain': 'EUR',
        'китай': 'CNY', 'china': 'CNY',
        'япония': 'JPY', 'japan': 'JPY',
        'южная корея': 'KRW', 'south korea': 'KRW', 'корея': 'KRW', 'korea': 'KRW',
        'таиланд': 'THB', 'thailand': 'THB',
        'вьетнам': 'VND', 'vietnam': 'VND',
        'турция': 'TRY', 'turkey': 'TRY',
        'оаэ': 'AED', 'uae': 'AED', 'дубай': 'AED', 'dubai': 'AED',
        'индия': 'INR', 'india': 'INR',
        'бразилия': 'BRL', 'brazil': 'BRL',
        'канада': 'CAD', 'canada': 'CAD',
        'австралия': 'AUD', 'australia': 'AUD',
        'швейцария': 'CHF', 'switzerland': 'CHF',
        'мексика': 'MXN', 'mexico': 'MXN',
        'сингапур': 'SGD', 'singapore': 'SGD',
        'польша': 'PLN', 'poland': 'PLN',
        'чехия': 'CZK', 'czech republic': 'CZK', 'прага': 'CZK', 'prague': 'CZK',
        'швеция': 'SEK', 'sweden': 'SEK',
        'норвегия': 'NOK', 'norway': 'NOK',
        'дания': 'DKK', 'denmark': 'DKK',
        # Expanding the list with more countries
        'шри ланка': 'LKR', 'sri lanka': 'LKR', 'шри-ланка': 'LKR',
        'индонезия': 'IDR', 'indonesia': 'IDR',
        'малайзия': 'MYR', 'malaysia': 'MYR',
        'филиппины': 'PHP', 'philippines': 'PHP',
        'пакистан': 'PKR', 'pakistan': 'PKR',
        'бангладеш': 'BDT', 'bangladesh': 'BDT',
        'аргентина': 'ARS', 'argentina': 'ARS',
        'чили': 'CLP', 'chile': 'CLP',
        'колумбия': 'COP', 'colombia': 'COP',
        'перу': 'PEN', 'peru': 'PEN',
        'египет': 'EGP', 'egypt': 'EGP',
        'марокко': 'MAD', 'morocco': 'MAD',
        'тунис': 'TND', 'tunisia': 'TND',
        'кения': 'KES', 'kenya': 'KES',
        'южная африка': 'ZAR', 'south africa': 'ZAR', 'юар': 'ZAR',
        'нигерия': 'NGN', 'nigeria': 'NGN',
        'израиль': 'ILS', 'israel': 'ILS',
        'иордания': 'JOD', 'jordan': 'JOD',
        'ливан': 'LBP', 'lebanon': 'LBP',
        'саудовская аравия': 'SAR', 'saudi arabia': 'SAR',
        'катар': 'QAR', 'qatar': 'QAR',
        'кувейт': 'KWD', 'kuwait': 'KWD',
        'оман': 'OMR', 'oman': 'OMR',
        'бахрейн': 'BHD', 'bahrain': 'BHD',
        'иран': 'IRR', 'iran': 'IRR',
        'ирак': 'IQD', 'iraq': 'IQD',
        'новая зеландия': 'NZD', 'new zealand': 'NZD',
        'фиджи': 'FJD', 'fiji': 'FJD',
        'гонконг': 'HKD', 'hong kong': 'HKD',
        'макао': 'MOP', 'macau': 'MOP', 'macao': 'MOP',
        'тайвань': 'TWD', 'taiwan': 'TWD',
        'монголия': 'MNT', 'mongolia': 'MNT',
        'непал': 'NPR', 'nepal': 'NPR',
        'мьянма': 'MMK', 'myanmar': 'MMK', 'бирма': 'MMK', 'burma': 'MMK',
        'камбоджа': 'KHR', 'cambodia': 'KHR',
        'лаос': 'LAK', 'laos': 'LAK',
        'бруней': 'BND', 'brunei': 'BND',
        'мальдивы': 'MVR', 'maldives': 'MVR',
        'сейшелы': 'SCR', 'seychelles': 'SCR',
        'маврикий': 'MUR', 'mauritius': 'MUR',
        'исландия': 'ISK', 'iceland': 'ISK',
        'грузия': 'GEL', 'georgia': 'GEL',
        'армения': 'AMD', 'armenia': 'AMD',
        'азербайджан': 'AZN', 'azerbaijan': 'AZN',
        'казахстан': 'KZT', 'kazakhstan': 'KZT',
        'узбекистан': 'UZS', 'uzbekistan': 'UZS',
        'кыргызстан': 'KGS', 'kyrgyzstan': 'KGS',
        'таджикистан': 'TJS', 'tajikistan': 'TJS',
        'туркменистан': 'TMT', 'turkmenistan': 'TMT',
        'беларусь': 'BYN', 'belarus': 'BYN', 'белоруссия': 'BYN',
        'украина': 'UAH', 'ukraine': 'UAH',
        'молдова': 'MDL', 'moldova': 'MDL', 'молдавия': 'MDL',
        'румыния': 'RON', 'romania': 'RON',
        'болгария': 'BGN', 'bulgaria': 'BGN',
        'сербия': 'RSD', 'serbia': 'RSD',
        'хорватия': 'HRK', 'croatia': 'HRK',
        'босния': 'BAM', 'bosnia': 'BAM',
        'албания': 'ALL', 'albania': 'ALL',
        'македония': 'MKD', 'macedonia': 'MKD',
        'греция': 'EUR', 'greece': 'EUR',
        'кипр': 'EUR', 'cyprus': 'EUR',
        'мальта': 'EUR', 'malta': 'EUR',
        'венгрия': 'HUF', 'hungary': 'HUF',
        'словакия': 'EUR', 'slovakia': 'EUR',
        'словения': 'EUR', 'slovenia': 'EUR',
        'эстония': 'EUR', 'estonia': 'EUR',
        'латвия': 'EUR', 'latvia': 'EUR',
        'литва': 'EUR', 'lithuania': 'EUR',
        'финляндия': 'EUR', 'finland': 'EUR',
        'нидерланды': 'EUR', 'netherlands': 'EUR', 'голландия': 'EUR',
        'бельгия': 'EUR', 'belgium': 'EUR',
        'люксембург': 'EUR', 'luxembourg': 'EUR',
        'австрия': 'EUR', 'austria': 'EUR',
        'португалия': 'EUR', 'portugal': 'EUR',
        'ирландия': 'EUR', 'ireland': 'EUR',
    }
    
    if country_lower in common_mappings:
        return common_mappings[country_lower]
    
    # Try to detect from common patterns (e.g., "Шри Ланка" -> LKR)
    # This is a fallback for partial matches
    for key, value in common_mappings.items():
        if key in country_lower or country_lower in key:
            return value
    
    return None


def detect_currency_with_api(country_name: str) -> Optional[str]:
    """
    Detect currency for a country
    First checks common mappings, then validates with API
    """
    # Try common mappings first
    currency = find_currency_by_country(country_name)
    
    if currency:
        # Validate that currency exists in API
        all_currencies = get_all_currencies()
        if currency in all_currencies:
            return currency
    
    return None

