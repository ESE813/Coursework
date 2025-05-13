import datetime
import json
import logging
import os
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

from src.logger import get_logger

logger = get_logger("utils", "../logs/utils.log", logging.INFO)


def report_saver(filename: str = None):
    """Декоратор для записи отчета в файл"""

    def wrapper(func):
        def inner(*args, **kwargs):
            df = func(*args, **kwargs)

            logging.info("Присваиваем имя файлу")
            if filename is None:
                default_filename = f"{datetime.datetime.now().strftime('%Y%m%d')}.json"
                file_path = f"../reports/{default_filename}"
            else:
                file_path = f"../reports/{filename}"
            os.makedirs("../reports", exist_ok=True)
            logging.info(f"Записываем данные отчета в файл в {file_path}")

            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(df.to_dict(orient="records"), file, ensure_ascii=False, indent=4)

            print(f"Отчет успешно сохранен в файл: {file_path}")
            return df

        return inner

    return wrapper


@report_saver()
def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """Функция для получения трат по категории"""

    logging.info("Устанавливаем дату окончания периода")
    try:
        transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S")
        if date is None:
            date_end = pd.to_datetime(datetime.datetime.now())
        else:
            date_end = pd.to_datetime(date)

        logging.info("Устанавливаем дату начала периода (3 месяца назад)")
        date_start = date_end - relativedelta(months=3)
        # Фильтруем транзакции по категории расходов и периоду
        logging.debug("Фильтруем данные по тратам по указанной категории за 3 месяца")

        transactions = transactions[
            (transactions["Сумма операции"] < 0)
            & (transactions["Категория"].str.lower() == category.lower())
            & (transactions["Дата операции"] >= date_start)
            & (transactions["Дата операции"] <= date_end)
        ]
        logging.debug(f"Данные отфильтрованы за период c {date_start} по {date_end}")

        category_spending = transactions.groupby("Категория")["Сумма операции"].sum().abs().reset_index()
        category_spending = category_spending[["Категория", "Сумма операции"]].rename(
            columns={"Категория": "Категория", "Сумма операции": "Сумма трат за 3 месяца"}
        )
        logging.debug(f"Рассчитана сумма трат по категории {category} за 3 месяца c {date_start} по" f" {date_end}")
        return category_spending

    except Exception as e:
        print(f"Ошибка при формировании отчета: {e}")
        return pd.DataFrame()
