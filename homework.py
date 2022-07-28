from http import HTTPStatus
import logging
import os
import time
from typing import Any, Dict, Union

import requests
from dotenv import load_dotenv
import telegram as tg

load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

logging.basicConfig(
    format='%(asctime)s [%(levelname)s] %(message)s',
    level=logging.INFO)

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot: tg.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат.
    Telegram чат, определяется переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра:
    экземпляр класса Bot и строку с текстом сообщения.
    """
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


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
    homeworks = response.get('homeworks')
    current_date = response.get('current_date')
    if homeworks is None:
        print('В ответе API нет ключа houmeworks.')
        raise Exception('В ответе API нет ключа houmeworks.')
    if current_date is None:
        print('В ответе API нет ключа current_date.')
        raise Exception('В ответе API нет ключа houmeworks.')
    if type(homeworks) is not list:
        raise Exception('В ответе API houmeworks не является списком.')
    return homeworks


def parse_status(homework: Dict[str, Union[str, int]]) -> str:
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка
    домашних работ. В случае успеха, функция возвращает подготовленную для
    отправки в Telegram строку, содержащую один из вердиктов словаря
    HOMEWORK_STATUSES.
    """
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyError('В кловаре отсутствует ключ homework_name.')
    homework_status = homework.get('status')
    if homework_status is None:
        raise KeyError('В кловаре отсутствует ключ status.')
    verdict = HOMEWORK_STATUSES.get(homework_status)
    if verdict is None:
        raise Exception('Недокументированный статус проверки работы.')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения.
    Если отсутствует хотя бы одна переменная окружения -
    функция должна вернуть False, иначе - True.
    """
    if PRACTICUM_TOKEN is None:
        print('Не задана переменная окружения PRACTICUM_TOKEN')
        return False
    if TELEGRAM_TOKEN is None:
        print('Не задана переменная окружения TELEGRAM_TOKEN')
        return False
    if TELEGRAM_CHAT_ID is None:
        print('Не задана переменная окружения TELEGRAM_CHAT_ID')
        return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical(
            'Отсутствует обязательная переменная окружения.'
            'Программа принудительно остановлена.'
        )
        return

    bot = tg.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - RETRY_TIME

    # ...

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            for homework in homeworks:
                send_message(bot, parse_status(homework))
            current_timestamp = response['current_date']
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            time.sleep(RETRY_TIME)
        else:
            pass


if __name__ == '__main__':
    main()
