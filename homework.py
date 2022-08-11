import logging
import os
import sys
import time
from http import HTTPStatus
from typing import Any, Dict, List, Union

import requests
import telegram as tg
from telegram.ext import CommandHandler, Updater
from dotenv import load_dotenv

from exceptions import (EmptyAPIResponseError, GetAPIRequestError,
                        JSONAPIResponseError, StatusAPIResponseError,
                        UnknownHomeworkStatusError)

load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

EXC_INFO = False
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] (%(funcName)s) %(message)s'
))
logger.addHandler(handler)

RETRY_TIME = 60
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
KITTY_ENDPOINT = 'https://api.thecatapi.com/v1/images/search'


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class BotHandler(logging.StreamHandler):
    """Handler для отправки лога в ТГ чат."""

    def __init__(self, send: callable, bot: tg.Bot):
        """Init."""
        super().__init__()
        self.send = send
        self.bot = bot
        self.last_message = ''

    def emit(self, record: logging.LogRecord) -> None:
        """The emit method."""
        self.send(self.bot, self.format(record))


class NoRepeatFilter(logging.Filter):
    """Filter для исключения повторяющихся сообщений."""

    def __init__(self):
        """Init."""
        super().__init__()
        self.msg = None

    def filter(self, record: logging.LogRecord) -> bool:
        """The filter method."""
        allow = self.msg != record.msg
        self.msg = record.msg
        return allow


def get_new_image() -> str:
    """The get_new_image."""
    try:
        response = requests.get(KITTY_ENDPOINT)
    except Exception as error:
        logger.error(f'Ошибка при запросе к основному API: {error}')
        new_url = 'https://api.thedogapi.com/v1/images/search'
        response = requests.get(new_url)
    response = response.json()
    return response[0].get('url')


def new_cat(update, context) -> None:
    """The new_cat."""
    chat = update.effective_chat
    context.bot.send_photo(chat.id, get_new_image())


def wake_up(update, context) -> None:
    """The wake_up."""
    chat = update.effective_chat
    name = update.message.chat.first_name
    button = tg.ReplyKeyboardMarkup([['/newcat']], resize_keyboard=True)
    context.bot.send_message(
        chat_id=chat.id,
        text=f'Привет, {name}! Посмотри, какого котика я тебе нашёл!',
        reply_markup=button
    )
    context.bot.send_photo(chat.id, get_new_image())


def send_message(bot: tg.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат.
    Telegram чат, определяется переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра:
    экземпляр класса Bot и строку с текстом сообщения.
    """
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logger.error(
            'Ошибка отправки сообщения в чат %s: %s',
            TELEGRAM_CHAT_ID,
            error,
            exc_info=EXC_INFO
        )
    else:
        logger.info(
            'Сообщение "%s" отправлено в чат %s',
            message,
            TELEGRAM_CHAT_ID
        )


def get_api_answer(current_timestamp) -> Dict[str, Any]:
    """Делает запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    logger.info(
        'Отправлен запрос к эндпоинту %s с параметром %s', ENDPOINT, params
    )
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except Exception as error:
        message = (f'Ошибка запроса к API: Эндпоинт {ENDPOINT}; '
                   f'Исключение {error}')
        raise GetAPIRequestError(message)
    if homework_statuses.status_code != HTTPStatus.OK:
        message = (f'Ошибка запроса к API: Эндпоинт {ENDPOINT}; '
                   f'Код ответа {homework_statuses.status_code}')
        raise StatusAPIResponseError(message)
    try:
        answer = homework_statuses.json()
    except Exception as error:
        message = (f'Ошибка запроса к API: Эндпоинт {ENDPOINT}; '
                   f'Некорректный json {error}')
        raise JSONAPIResponseError(message)
    return answer


def check_response(response: Dict[str, Any]) -> List[str, Any]:
    """Проверяет ответ API на корректность. Возвращает список работ."""
    if not isinstance(response, dict):
        raise TypeError('В ответе API нет словаря.')
    homeworks = response.get('homeworks')
    if not homeworks:
        raise EmptyAPIResponseError('В ответе API нет ключа homeworks.')
    current_date = response.get('current_date')
    if not current_date:
        raise EmptyAPIResponseError('В ответе API нет ключа current_date.')
    if not isinstance(homeworks, list):
        raise TypeError('В ответе API homeworks не является списком.')
    return homeworks


def parse_status(homework: Dict[str, Union[str, int]]) -> str:
    """Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка
    домашних работ. В случае успеха, функция возвращает подготовленную для
    отправки в Telegram строку, содержащую один из вердиктов словаря
    HOMEWORK_STATUSES.
    """
    homework_name = homework.get('homework_name')
    if not homework_name:
        raise KeyError('В словаре отсутствует ключ homework_name.')
    homework_status = homework.get('status')
    if not homework_status:
        raise KeyError('В словаре отсутствует ключ status.')
    verdict = HOMEWORK_STATUSES.get(homework_status)
    if not verdict:
        raise UnknownHomeworkStatusError(
            'Недокументированный статус проверки работы.'
        )
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения.
    Если отсутствует хотя бы одна переменная окружения -
    функция должна вернуть False, иначе - True.
    """
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        message = ('Отсутствует обязательная переменная окружения. '
                   'Программа принудительно остановлена.')
        logger.critical(message)
        sys.exit(message)

    updater = Updater(token=TELEGRAM_TOKEN)

    updater.dispatcher.add_handler(CommandHandler('start', wake_up))
    updater.dispatcher.add_handler(CommandHandler('newcat', new_cat))

    updater.start_polling()

    bot = tg.Bot(token=TELEGRAM_TOKEN)

    bot_handler = BotHandler(send_message, bot)
    bot_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] (%(funcName)s) %(message)s'
    ))
    bot_handler.setLevel(logging.ERROR)
    bot_handler.addFilter(NoRepeatFilter())
    logger.addHandler(bot_handler)

    current_timestamp = int(time.time()) - RETRY_TIME * 6 * 24 * 60 * 60

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logger.info('Новые статусы отсутствуют')
            for homework in homeworks:
                send_message(bot, parse_status(homework))
            current_timestamp = response['current_date']
        except Exception as error:
            logger.error(
                'Сбой в работе программы: %s',
                error,
                exc_info=EXC_INFO
            )

        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
