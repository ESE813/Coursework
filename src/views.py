import json
import os

from src.utils import get_cards_data
from src.utils import get_currency_rates
from src.utils import get_data_period
from src.utils import get_greeting
from src.utils import get_stock_prices
from src.utils import get_top_transactions

user_settings_file = os.path.abspath("./data/user_settings.json")


def main_page(date_string):
    """Основная функция для страницы Главная"""
    df = get_data_period(date_string)

    response = {
        "greeting": get_greeting(),
        "last_digits": get_cards_data(df),
        "top_transactions": get_top_transactions(df),
        "currency_rates": get_currency_rates(user_settings_file),
        "stock_prices": get_stock_prices(user_settings_file),
    }
    print(json.dumps(response, ensure_ascii=False, indent=4))
