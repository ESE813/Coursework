import json
import logging
import os
from datetime import datetime
from datetime import timedelta

import pandas as pd
import requests
from dotenv import load_dotenv

from src.logger import get_logger

load_dotenv(".env")

input_file = os.path.abspath("./data/operations.xlsx")
user_settings_file = os.path.abspath("./data/user_settings.json")

logger = get_logger("utils", "../logs/utils.log", logging.INFO)


def get_greeting():
    """Функция для вывода приветствия в зависимости от времени входа в приложение"""
    now = datetime.now()
    if 6 <= now.hour < 12:
        return "Доброе утро"
    elif 12 <= now.hour < 18:
        return "Добрый день"
    elif 18 <= now.hour < 24:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_data_period(date_string, data_range="M"):
    """Функция для получения данных для анализа за выбранный период"""
    date_end = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    if data_range == "M":
        logging.info("Выбран диапазон для анализа данных: месяц")
        date_start = datetime(date_end.year, date_end.month, 1, 0, 0, 0)
    elif data_range == "W":
        logging.info("Выбран диапазон для анализа данных: неделя")
        day_of_week = date_end.weekday()
        date_start = date_end - timedelta(days=day_of_week)
        date_start = datetime(date_start.year, date_start.month, date_start.day, 0, 0, 0)
    elif data_range == "Y":
        logging.info("Выбран диапазон для анализа данных: год")
        date_start = datetime(date_end.year, 1, 1, 0, 0, 0)
    elif data_range == "ALL":
        logging.info("Выбран диапазон для анализа данных: до указанной даты")
        date_start = datetime.min
    else:
        logging.error("Недопустимый период")
        raise ValueError("Invalid period")

    logging.info("Получаем данные из файла Excel")
    df = pd.read_excel(input_file)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    try:
        logging.info("Фильтруем данные за указанный период")
        df = df[(date_start <= df["Дата операции"]) & (df["Дата операции"] <= date_end)]
        logging.info(f"Данные отфильтрованы за период c {date_start} по {date_end}")
    except FileNotFoundError:
        logging.error("Файл не найден")
        print(f"Файл {input_file} не найден")
        return None

    except pd.errors.ParserError:
        logging.error("Ошибка при чтении файла Excel")
        print("Ошибка при чтении файла Excel")
        return None
    return df


def get_exchange_rate(from_currency: str) -> float:
    """Функция позволяет получать текущий курс обмена валюты к рублю"""
    try:
        url = f"https://api.apilayer.com/exchangerates_data/convert?to=RUB&from={from_currency}&amount=1"
        headers = {"apikey": os.getenv("API_KEY_1")}

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        return data["result"]

    except requests.RequestException as e:
        logging.error(f"Ошибка при получении курса валют: {e}")
        raise


def convert_to_rubles(df):
    """Функция конвертации суммы платежей в рубли"""
    logging.info("Конвертируем суммы в рубли")

    df_converted = df.copy()  # Создаем копию DataFrame для избежания изменений оригинала
    df_converted.loc[df_converted["Валюта платежа"] != "RUB", "Сумма платежа"] = df_converted[
        df_converted["Валюта платежа"] != "RUB"
    ].apply(lambda row: row["Сумма платежа"] * get_exchange_rate(row["Валюта платежа"]), axis=1)

    df_converted["Валюта платежа"] = "RUB"  # Оставляем только рубли в столбце валюты

    return df_converted


def get_cards_data(df_convert_rub):
    """Функция выводит по каждой карте: последние 4 цифры карты; общая сумма расходов; кешбэк (1 рубль на каждые 100
    рублей)"""
    logging.info("Группируем расходы по картам")
    expenses = df_convert_rub[df_convert_rub["Сумма платежа"] < 0]
    grouped = expenses.groupby("Номер карты")["Сумма платежа"].sum().reset_index()

    grouped["last_digits"] = grouped["Номер карты"].apply(lambda x: f"{str(x)[-4:]}")
    grouped["total_spent"] = grouped["Сумма платежа"].abs()

    logging.info("Рассчитываем кешбэк (1 рубль на каждые 100 рублей)")
    grouped["cashback"] = (grouped["total_spent"].abs() / 100).astype(int)
    cards = grouped[["last_digits", "total_spent", "cashback"]].to_dict(orient="records")
    logging.info("Сформированы данные по каждой карте: сумма расходов и кэшбэк")
    return cards


def get_top_transactions(df_convert_rub):
    """Выводит топ 5 транзакций"""
    logging.info("Получаем топ-5 транзакций")
    top_transactions = df_convert_rub.sort_values(by="Сумма платежа", ascending=False).head(5)
    top_transactions = (
        top_transactions[["Дата операции", "Сумма платежа", "Категория", "Описание"]]
        .rename(
            columns={
                "Дата операции": "date",
                "Сумма платежа": "amount",
                "Категория": "category",
                "Описание": "description",
            }
        )
        .to_dict(orient="records")
    )
    for transaction in top_transactions:
        transaction["amount"] = round(transaction["amount"], 2)
        transaction["date"] = transaction["date"].strftime("%d.%m.%Y")
    logging.info("Определены топ-5 транзакций по сумме платежа")
    return top_transactions


def get_currency_rates(user_settings_file):
    """Функция для вывода актуальных курсов валют"""
    currency_rates = []
    try:
        with open(user_settings_file) as f:
            user_settings = json.load(f)
            user_currencies = user_settings.get("user_currencies", [])

        for currency in user_currencies:
            logging.debug(f"Запрос курса для валюты: {currency}")
            try:
                url_1 = f"https://api.apilayer.com/exchangerates_data/latest?symbols={currency}&base=RUB"
                headers = {"apikey": os.getenv("API_KEY_1")}
                response = requests.get(url_1, headers=headers)
                response.raise_for_status()

                # Добавляем проверку на None
                data = response.json()
                rates = data.get("rates")
                if rates:
                    rate = rates.get(currency)
                else:
                    rate = None

                currency_rates.append({"currency": currency, "rate": rate})

            except requests.RequestException as e:
                print(f"Ошибка при получении курса для {currency}: {e}")
                currency_rates.append({"currency": currency, "rate": None})

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Ошибка при чтении файла настроек пользователя: {e}")

    return currency_rates


def get_stock_prices(user_settings_file):
    stock_prices = []
    try:
        with open(user_settings_file) as f:
            user_settings = json.load(f)
            user_stocks = user_settings["user_stocks"]

            for stock in user_stocks:
                logging.debug(f"Запрос цены для акций: {stock}")
                try:
                    apikey = os.getenv("API_KEY_2")
                    url_2 = f"https://financialmodelingprep.com/api/v3/quote-short/{stock}?apikey={apikey}"
                    response = requests.get(url_2)
                    response.raise_for_status()
                    data = response.json()

                    # Проверка, что данные не пустые и имеют правильный формат
                    if isinstance(data, list) and data:
                        price = round(data[0]["price"], 2)
                        stock_prices.append({"stock": stock, "price": price})
                    else:
                        logging.warning(f"Некорректный формат данных для {stock}")
                except (KeyError, IndexError):
                    logging.error(f"Ошибка при получении цены для {stock}")
                    stock_prices.append({"stock": stock, "price": None})
                except requests.RequestException as e:
                    logging.error(f"Ошибка запроса для {stock}: {e}")
                    stock_prices.append({"stock": stock, "price": None})

    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logging.error(f"Ошибка при работе с файлом настроек: {e}")
        return []

    return stock_prices



