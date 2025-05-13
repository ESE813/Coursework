import logging
import os


def get_logger(file_name, log_file, level=logging.INFO):
    """Функция настройки логирования"""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = logging.getLogger(file_name)
    logger.setLevel(level)
    file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
    file_formatter = logging.Formatter("%(asctime)s - %(filename)s - %(funcName)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger
