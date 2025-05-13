import os
import pandas as pd
import pytest
import tempfile
from unittest.mock import patch
from datetime import datetime
from src.utils import get_greeting, get_data_period, get_cards_data, get_top_transactions


# Тест функции get_greeting
@patch("src.utils.datetime")
def test_day_greeting(mock_datetime):
    mock_datetime.now.return_value = datetime(2025, 3, 23, 15, 10, 0)
    assert get_greeting() == "Добрый день"


@patch("src.utils.datetime")
def test_evening_greeting(mock_datetime):
    mock_datetime.now.return_value = datetime(2025, 3, 23, 20, 15, 0)
    assert get_greeting() == "Добрый вечер"


@patch("src.utils.datetime")
def test_night_greeting(mock_datetime):
    mock_datetime.now.return_value = datetime(2025, 3, 23, 3, 25, 0)
    assert get_greeting() == "Доброй ночи"


# Тест функции get_data_period
@pytest.fixture
def test_data():
    return {
        "Дата операции": [
            "01.01.2025 00:00:00",
            "02.01.2025 00:00:00",
            "03.01.2025 00:00:00",
            "04.01.2025 00:00:00",
            "05.01.2025 00:00:00",
            "06.01.2025 00:00:00",
            "07.01.2025 00:00:00",
            "08.01.2025 00:00:00",
            "09.01.2025 00:00:00",
            "10.01.2025 00:00:00",
            "11.01.2025 00:00:00",
            "12.01.2025 00:00:00",
            "13.01.2025 00:00:00",
            "14.01.2025 00:00:00",
            "15.01.2025 12:00:00",
            "01.02.2025 12:00:00",
            "15.02.2025 12:00:00",
            "01.03.2025 12:00:00",
        ],
        "Сумма операции": [100, 200, 300, 400, 500, 600, 700, 800, 900, 750, 320, 850, 120, 1200, 940, 710, 300, 400],
    }
def test_monthly_range(test_data):
    date_string = "2025-01-15 12:00:00"
    expected_start = pd.Timestamp(2025, 1, 1, 0, 0, 0)
    expected_end = pd.to_datetime(date_string)

    df = pd.DataFrame(test_data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    with patch("pandas.read_excel", return_value=df):
        result = get_data_period(date_string, "M")

    assert len(result) == 15
    assert result["Дата операции"].min() == expected_start
    assert result["Дата операции"].max() == expected_end


def test_yearly_range(test_data):
    date_string = "2025-01-15 12:00:00"
    expected_start = pd.Timestamp(2025, 1, 1, 0, 0, 0)
    expected_end = pd.to_datetime(date_string)

    df = pd.DataFrame(test_data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    with patch("pandas.read_excel", return_value=df):
        result = get_data_period(date_string, "Y")

    assert len(result) == 15
    assert result["Дата операции"].min() == expected_start
    assert result["Дата операции"].max() == expected_end


def test_weekly_range(test_data):
    date_string = "2025-01-15 12:00:00"
    expected_start = pd.Timestamp(2025, 1, 13, 0, 0, 0)  # Понедельник недели
    expected_end = pd.to_datetime(date_string)

    df = pd.DataFrame(test_data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    with patch("pandas.read_excel", return_value=df):
        result = get_data_period(date_string, "W")

    assert len(result) == 3
    assert result["Дата операции"].min() == expected_start
    assert result["Дата операции"].max() == expected_end


def test_all_range(test_data):
    date_string = "2025-01-15 12:00:00"
    expected_end = pd.to_datetime(date_string)

    df = pd.DataFrame(test_data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    with patch("pandas.read_excel", return_value=df):
        result = get_data_period(date_string, "ALL")

    assert len(result) == 15
    assert result["Дата операции"].max() == expected_end
    assert result["Дата операции"].min() == pd.Timestamp(2025, 1, 1, 0, 0, 0)
    assert (result["Дата операции"] <= expected_end).all()


def test_invalid_period():
    date_string = "2025-01-15 12:00:00"
    invalid_range = "INVALID"

    with pytest.raises(ValueError, match="Invalid period"):
        get_data_period(date_string, invalid_range)


def test_invalid_date_format():
    invalid_date_string = "2025-01-15"  # Неверный формат даты

    with pytest.raises(ValueError, match="time data"):
        get_data_period(invalid_date_string)


def test_parser_error():
    date_string = "2025-01-15 12:00:00"

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(b"invalid excel content")

    with pytest.raises(ValueError) as exc_info:
        get_data_period(date_string, tmp.name)

    os.remove(tmp.name)
    assert "Invalid period" in str(exc_info.value)



# Тест функции get_cards_data
def test_get_cards_data_empty_df():
    # Создаем пустой DataFrame с нужными колонками
    empty_df = pd.DataFrame(columns=["Номер карты", "Сумма платежа"])
    result = get_cards_data(empty_df)
    assert result == []


def test_get_cards_data_single_card():
    # Создаем DataFrame с одной картой и несколькими транзакциями
    data = {"Номер карты": [4276123456789012, 4276123456789012], "Сумма платежа": [-1000, -2000]}
    df = pd.DataFrame(data)
    expected = [{"last_digits": "9012", "total_spent": 3000, "cashback": 30}]
    result = get_cards_data(df)
    assert result == expected


def test_get_cards_data_multiple_cards():
    # Создаем DataFrame с несколькими картами
    data = {
        "Номер карты": [4276123456789012, 5469123456789012, 4276123456789012],
        "Сумма платежа": [-1000, -500, -2000],
    }
    df = pd.DataFrame(data)
    expected = [
        {"last_digits": "9012", "total_spent": 3000, "cashback": 30},
        {"last_digits": "9012", "total_spent": 500, "cashback": 5},
    ]
    result = get_cards_data(df)
    assert sorted(result, key=lambda x: x["last_digits"]) == sorted(expected, key=lambda x: x["last_digits"])


def test_get_cards_data_no_negative_transactions():
    # Создаем DataFrame без отрицательных транзакций
    data = {"Номер карты": [4276123456789012, 4276123456789012], "Сумма платежа": [1000, 2000]}
    df = pd.DataFrame(data)
    result = get_cards_data(df)
    assert result == []



# тест функции get_top_transactions
@pytest.fixture
def test_df():
    data = {
        "Дата операции": pd.to_datetime(
            ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04", "2025-01-05", "2025-01-06"]
        ),
        "Сумма платежа": [1000.567, 500.123, 1500.789, 200.999, 1200.456, 800.111],
        "Категория": ["Продукты", "Транспорт", "Продукты", "Развлечения", "Продукты", "Транспорт"],
        "Описание": [
            "Покупка в магазине",
            "Оплата проезда",
            "Покупка продуктов",
            "Кинотеатр",
            "Супермаркет",
            "Автобус",
        ],
    }
    return pd.DataFrame(data)
def test_get_top_transactions(test_df):
    result = get_top_transactions(test_df)

    # Проверяем формат результата
    assert isinstance(result, list)
    assert len(result) == 5

    for transaction in result:
        assert set(transaction.keys()) == {"date", "amount", "category", "description"}
        assert isinstance(transaction["date"], str)
        assert isinstance(transaction["amount"], float)
        assert isinstance(transaction["category"], str)
        assert isinstance(transaction["description"], str)

    # Проверяем сортировку и округление
    expected_amounts = [1500.79, 1200.46, 1000.57, 800.11, 500.12]
    assert [transaction["amount"] for transaction in result] == expected_amounts

    # Проверяем формат даты
    expected_dates = ["03.01.2025", "05.01.2025", "01.01.2025", "06.01.2025", "02.01.2025"]
    assert [transaction["date"] for transaction in result] == expected_dates


def test_get_top_transactions_less_than_5(test_df):
    # Берем только 3 транзакции
    small_df = test_df.head(3)
    result = get_top_transactions(small_df)

    # Проверяем количество результатов
    assert len(result) == 3


def test_get_top_transactions_empty_df():
    empty_df = pd.DataFrame(columns=["Дата операции", "Сумма платежа", "Категория", "Описание"])
    result = get_top_transactions(empty_df)

    # Проверяем результат
    assert result == []