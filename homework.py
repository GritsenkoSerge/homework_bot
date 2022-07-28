from http import HTTPStatus
import os
import time
from typing import Any, Dict

import requests
from dotenv import load_dotenv

load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message) -> None:
    pass


def get_api_answer(current_timestamp) -> Dict[str, Any]:
    """Делает запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework_statuses.status_code != HTTPStatus.OK:
        print('Ошибка запроса к API.')
        raise Exception('Ошибка запроса к API.')  # TODO сделать свое искл.
    return homework_statuses.json()


def check_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Проверяет ответ API на корректность. Возвращает список работ."""
    print(type(response))
    if type(response) is not dict:
        raise TypeError('В ответе API нет словаря.')
    houmeworks = response.get('homeworks')
    current_date = response.get('current_date')
    if houmeworks is None:
        print('В ответе API нет ключа houmeworks.')
        raise Exception('В ответе API нет ключа houmeworks.')
    if current_date is None:
        print('В ответе API нет ключа current_date.')
        raise Exception('В ответе API нет ключа houmeworks.')
    if type(houmeworks) is not list:
        raise Exception('В ответе API houmeworks не является списком.')
    return houmeworks


def parse_status(homework):
    homework_name = ...
    homework_status = ...

    ...

    verdict = ...

    ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """
    Проверяет доступность переменных окружения,
    которые необходимы для работы программы.
    """
    if PRACTICUM_TOKEN is None:
        print('Не задан PRACTICUM_TOKEN')
        return False
    if TELEGRAM_TOKEN is None:
        print('Не задан TELEGRAM_TOKEN')
        return False
    if TELEGRAM_CHAT_ID is None:
        print('Не задан TELEGRAM_CHAT_ID')
        return False
    return True


def main():
    """Основная логика работы бота."""

    # ...

    # bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # current_timestamp = int(time.time())

    # ...

    # while True:
    #     try:
    #         response = ...

    #         ...

    #         current_timestamp = ...
    #         time.sleep(RETRY_TIME)

    #     except Exception as error:
    #         message = f'Сбой в работе программы: {error}'
    #         ...
    #         time.sleep(RETRY_TIME)
    #     else:
    #         ...


if __name__ == '__main__':
    main()
