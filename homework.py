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
    if homework_name is None:
        logger.error('Проект не найден')
        return 'Проект не найден'
    homework_status = homework.get('status')
    if homework_status is None:
        logger.error('Отсутствует статус')
        return 'Отсутствует статус'

    if homework_status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif homework_status == 'approved':
        verdict = (
            'Ревьюеру всё понравилось, '
            'можно приступать к следующему уроку.'
        )
    elif homework_status == 'reviewing':
        return (
            f'Руслан взял в работу {homework_name}, '
            'уЗбогойся, он знает что делает! :grin:'
        )
    else:
        verdict = 'Не известное решение. Уточните детали к ревьюера.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    current_timestamp = current_timestamp or int(time.time())
    data = {'from_date': current_timestamp}
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    try:
        homework_statuses = requests.get(
            API_PRAKTIKUM,
            params=data,
            headers=headers,
        )
        return homework_statuses.json()
    except requests.exceptions.RequestException:
        logger.error('Ошибка запроса API')
        send_message(('Напишите в поддержку, '
                      'что разрабам надо поправить адрес API'), bot_client)
    except ValueError:
        logger.error('Ошибка связанная с json')
        send_message(f'ошибка в json: {ValueError}', bot_client)
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
            send_message(f'Бот столкнулся с ошибкой: {e}', bot_client)
            time.sleep(5)


if __name__ == '__main__':
    main()
