import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv


load_dotenv()


from exceptions import (
    ApiRequestError,
    HomeWorkApiError,
    InvalidTelegramToken,
    NoneEnvVariableError,
    WrongHTTPStatus,
)


PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s,'
    + '%(levelname)s, %(message)s, %(name)s, %(funcName)s, %(lineno)s'
)
handler.setFormatter(formatter)


def check_tokens():
    """Проверка доступности переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot: telegram.Bot, message):
    """Отправляет сообщения в Telegram."""
    logger.info('Попытка отправить сообщение в Telegram.')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f'Не удалось отправить сообщение в Telegram: {error}')
    else:
        logger.info('Удачная отправка сообщения в Telegram.')


def get_api_answer(timestamp):
    """Делает запрос к API."""
    logger.info('Отправка запроса к API.')
    try:
        response = requests.get(
            url=ENDPOINT, headers=HEADERS, params={"from_date": timestamp}
        )
    except requests.RequestException as error:
        logger.error(f"Получили ошибку при запросе {error}")
        raise ApiRequestError("Ошибка при запросе")
    if response.status_code != requests.codes.ok:
        logger.error("Мы получили плохой ответ")
        raise WrongHTTPStatus("Мы получили плохой ответ")
    return response.json()



def check_response(response):
    """
    Проверяет то, что ответ API был приведен к типу данных dict.
    а так же то, что в ответе имеется ключ homeworks типа данных list
    """
    logger.info('Проверка ответа API на корректность')
    if not isinstance(response, dict):
        raise TypeError("Response должен быть типом данных dict")
    if "homeworks" not in response or "current_date" not in response:
        raise TypeError("Неправильное наполнение ответа API")
    if not isinstance(response.get("homeworks"), list):
        raise TypeError("Значение homework должно быть типом данных list")
    return True


def parse_status(homework):
    """
    Получаем статус самой свежей проверки ДЗ.
    Проверяем что в ответе API есть имя и статус ДЗ.
    """
    logger.info('Статус проверки работы получен')
    homework_name = homework.get("homework_name", None)
    homework_status = homework.get("status", None)
    if homework_name is None or homework_status not in HOMEWORK_VERDICTS:
        raise HomeWorkApiError(
            "Неправильное наполнение словаря с результатами ДЗ"
        )
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise NoneEnvVariableError("Нет переменной окружения")
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
    except telegram.error.InvalidToken:
        raise InvalidTelegramToken("Некорректный token для бота")
    logger.debug("Запуск бота")
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homework_list = response.get("homeworks")
            if homework_list:
                send_message(bot, parse_status(homework_list[0]))
            else:
                logger.debug("Новых обновлений по ДЗ нет.")
            timestamp = response.get('current_date', timestamp)
        except Exception as error:
            logger.error(error)
            message = f"Сбой в работе программы: {error}"
            send_message(bot, message)

        finally:
            logger.debug("Засыпаем на 10 минут")
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
