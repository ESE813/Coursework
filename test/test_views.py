import json
import os
from unittest.mock import patch
import pandas as pd
import pytest
from src.views import main_page, user_settings_file


def test_main_page_valid_date(capsys):
    with (
        patch("src.views.get_data_period") as mock_get_data_period,
        patch("src.views.get_greeting") as mock_get_greeting,
        patch("src.views.get_cards_data") as mock_get_cards_data,
        patch("src.views.get_top_transactions") as mock_get_top_transactions,
        patch("src.views.get_currency_rates") as mock_get_currency_rates,
        patch("src.views.get_stock_prices") as mock_get_stock_prices,
    ):
        # Настраиваем макеты
        mock_get_data_period.return_value = pd.DataFrame()
        mock_get_greeting.return_value = "Приветствие"
        mock_get_cards_data.return_value = "****1234"
        mock_get_top_transactions.return_value = []
        mock_get_currency_rates.return_value = {"USD": 80, "EUR": 90}
        mock_get_stock_prices.return_value = {"AAPL": 200.0}

        main_page("2025-03-23")

        captured = capsys.readouterr()
        expected_json = {
            "greeting": "Приветствие",
            "last_digits": "****1234",
            "top_transactions": [],
            "currency_rates": {"USD": 80, "EUR": 90},
            "stock_prices": {"AAPL": 200.0},
        }
        assert json.loads(captured.out) == expected_json


# Тест с некорректной датой
def test_main_page_invalid_date():
    with patch("src.views.get_data_period") as mock_get_data_period:
        mock_get_data_period.side_effect = ValueError("Неверный формат даты")

    with pytest.raises(ValueError):
        main_page("некорректная_дата")


# Тест с отсутствующим файлом настроек
def test_main_page_missing_settings_file(capsys):
    original_content = None

    try:
        # Сохраняем содержимое файла, если он существует
        if os.path.exists(user_settings_file):
            with open(user_settings_file, "r") as f:
                original_content = f.read()

        # Удаляем файл только для теста
        if os.path.exists(user_settings_file):
            os.remove(user_settings_file)

        with (
            patch("src.views.get_data_period") as mock_get_data_period,
            patch("src.views.get_greeting") as mock_get_greeting,
            patch("src.views.get_cards_data") as mock_get_cards_data,
            patch("src.views.get_top_transactions") as mock_get_top_transactions,
            patch("src.views.get_currency_rates") as mock_get_currency_rates,
            patch("src.views.get_stock_prices") as mock_get_stock_prices,
        ):
            # Настраиваем макеты
            mock_get_data_period.return_value = pd.DataFrame()
            mock_get_greeting.return_value = "Приветствие"
            mock_get_cards_data.return_value = "****1234"
            mock_get_top_transactions.return_value = []
            mock_get_currency_rates.return_value = {"USD": 80, "EUR": 90}
            mock_get_stock_prices.return_value = {"AAPL": 200.0}

            main_page("2025-03-23")

            captured = capsys.readouterr()
            expected_json = {
                "greeting": "Приветствие",
                "last_digits": "****1234",
                "top_transactions": [],
                "currency_rates": {"USD": 80.0, "EUR": 90},
                "stock_prices": {"AAPL": 200.0},
            }
            assert json.loads(captured.out) == expected_json

    finally:
        # Восстанавливаем файл после теста
        if original_content is not None:
            with open(user_settings_file, "w") as f:
                f.write(original_content)