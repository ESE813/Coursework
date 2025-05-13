import json
from src.services import investment_bank, read_transactions_from_excel
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import logging
from typing import List, Dict, Any


# Тест для ошибки отсутствия файла
def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        read_transactions_from_excel("non_existent_file.xlsx")


# Тест чтения пустого Excel файла
def test_read_excel_file():
    try:
        # Attempt to read the Excel file
        df = pd.read_excel("operations.xlsx")
        if df.empty:
            return "The Excel file is empty."
        return df
    except FileNotFoundError:
        return "File not found. Please check the file path."
    except Exception as e:
        return f"An error occurred: {e}"


# Тест с некорректным форматом месяца
def test_investment_bank_invalid_month():
    month = "2025/03"
    limit = 50
    transactions = []

    with pytest.raises(ValueError, match="Неверный формат данных"):
        investment_bank(month, transactions, limit)


# Тест с некорректной датой
def test_investment_bank_invalid_transactions():
    month = "2025-03"
    limit = 50
    transactions = [{"Неверная_дата": "20.03.2025 12:00:00", "Сумма операции": -1712.00}]

    with pytest.raises(KeyError):
        investment_bank(month, transactions, limit)




def test_investment_bank_zero_limit():
    month = "2025-03"
    limit = 0
    transactions = []

    with pytest.raises(ValueError) as exc_info:
        investment_bank(month, transactions, limit)
    assert str(exc_info.value) == "Лимит округления должен быть больше 0"


def test_investment_bank_negative_limit():
    month = "2025-03"
    limit = -50
    transactions = []

    with pytest.raises(ValueError, match="Лимит округления должен быть больше 0"):
        investment_bank(month, transactions, limit)