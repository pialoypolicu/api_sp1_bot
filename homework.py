import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

API_PRAKTIKUM = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)
logger = logging.getLogger()

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
bot_client = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status == 'reviewing':
        return (
            f'Руслан взял в работу {homework_name}, '
            'уЗбогойся, он знает что делает! :grin:'
        )
    if homework_status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = (
            'Ревьюеру всё понравилось, '
            'можно приступать к следующему уроку.'
        )
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())
    data = {'from_date': current_timestamp}
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    homework_statuses = requests.get(
        API_PRAKTIKUM,
        params=data,
        headers=headers,
    )
    try:
        homework_statuses.raise_for_status()
        return homework_statuses.json()
    except requests.exceptions.HTTPError as error:
        message_error = homework_statuses.text
        logger.error(f'не правильный адрес : {message_error}')
        send_message((f'Бот столкнулся с ошибкой: {error}'), bot_client)
        return {}


def send_message(message, bot_client):
    logging.info('Отправляем сообщение')
    return bot_client.send_message(CHAT_ID, message)


def main():
    logging.debug('start bot')
    current_timestamp = int(time.time())
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]), bot_client)
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )
            time.sleep(1200)

        except Exception as e:
            send_message((f'Бот столкнулся с ошибкой: {e}'), bot_client)
            time.sleep(5)


if __name__ == '__main__':
    main()
