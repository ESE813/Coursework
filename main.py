import logging
import pandas as pd
from src.reports import spending_by_category
from src.services import investment_bank, read_transactions_from_excel
from src.views import main_page


def main():
    """
    Основная функция для запуска всех модулей проекта
    """
    logging.basicConfig(level=logging.INFO)

    try:
        # 1. Главная страница
        run_main_page()

        # 2. Сервис инвесткопилки
        run_investment_bank()

        # 3. Отчеты по категориям
        run_category_reports()

    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
        raise


def run_main_page():
    logging.info("Запуск модуля ГЛАВНАЯ")
    date_string = input('Введите дату в формате "YYYY-MM-DD HH:MM:SS": ')
    result = main_page(date_string)
    print(f"\nРезультат расчета накоплений: {result}\n")


def run_investment_bank():
    logging.info("Запуск модуля СЕРВИСЫ.ИНВЕСТКОПИЛКА")
    month = input('Введите месяц в формате "YYYY-MM": ')
    limit = get_valid_limit()
    transactions = read_transactions_from_excel("data/operations.xlsx")
    result = investment_bank(month, transactions, limit)
    print(f"\nРезультат расчета накоплений: {result}\n")


def run_category_reports():
    logging.info("Запуск модуля ОТЧЕТЫ.ТРАТЫ ПО КАТЕГОРИЯМ")
    category = input("Выберите категорию для расчета трат за 3 месяца: ").lower()
    end_date = input('Введите конечную дату периода в формате "YYYY-MM-DD": ')
    transactions_df = pd.read_excel("data/operations.xlsx")
    result = spending_by_category(transactions_df, category, end_date)
    print(f"\nОтчет по тратам: {result}\n")


def get_valid_limit() -> int:
    """
    Валидация ввода для предела округления
    """
    while True:
        try:
            limit = int(input("Введите предел округления (10, 50 или 100): "))
            if limit in [10, 50, 100]:
                return limit
            else:
                print("Пожалуйста, введите допустимое значение (10, 50 или 100)")
        except ValueError:
            print("Пожалуйста, введите число")


if __name__ == "__main__":
    main()