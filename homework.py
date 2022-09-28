import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

from exceptions import EasyError, EmptyKeyError

load_dotenv()

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляем сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Сообщение отправлено')
    except telegram.error.TelegramError as error:
        message = f'Ошибка при отправке сообщения {error}'
        logger.debug(message)


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except requests.ConnectionError as error:
        raise Exception(
            'Ошибка при запросе к эндпоинту API-сервиса') from error
    if response.status_code != 200:
        raise Exception(
            f'Неожиданный ответ сервера: {response.status_code}')
    return response.json()


def check_response(response):
    """Проверка ответа API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('Тип ответа API не является словарем')
    if 'homeworks' not in response:
        raise EmptyKeyError('Отсутствует поле homeworks в ответе API')
    homeworks = response['homeworks']
    if 'current_date' not in response:
        raise EmptyKeyError('Отсутствует поле current_date в ответе API')
    if isinstance(homeworks, list):
        return homeworks
    raise TypeError('Домашки пришли не в виде списка')


def parse_status(homework):
    """Получение статуса домашней работы."""
    if 'homework_name' not in homework:
        message = 'Отсутствует поле homework_name в ответе API'
        raise KeyError(message)
    if 'status' not in homework:
        message = 'Отсутствует поле status в ответе API'
        raise KeyError(message)
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        message = 'Неизвестный статус'
        raise Exception(message)
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка переменных окружения."""
    return all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        sys.exit(
            'Отсутствует одна(или более) из обязательных переменных окружения')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                status = parse_status(homeworks[0])
                send_message(bot, status)
            else:
                logger.debug('Новые статусы отсутвуют')

            current_timestamp = response.get('current_date', int(time.time()))
            error_message = ''

        except EasyError as error:
            logger.error(error)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(f'{message}')
            if message != error_message:
                bot.send_message(TELEGRAM_CHAT_ID, message)
                error_message = message

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
