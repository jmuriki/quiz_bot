import os
import random
import logging
import telegram
import vk_api as vk

from dotenv import load_dotenv
from vk_api.longpoll import VkLongPoll, VkEventType
from telegram_logs_handler import TelegramLogsHandler


logger = logging.getLogger(__name__)


def echo(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        message=event.text,
        random_id=random.randint(1,1000)
    )
    logger.info("vk_quiz_bot: АУ... Ау... ay...")


def main():
    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(process)d %(levelname)s %(message)s",
    )

    telegram_notify_token = os.environ["TELEGRAM_NOTIFY_TOKEN"]
    chat_id = os.environ["TELEGRAM_NOTIFY_CHAT_ID"]
    notify_bot = telegram.Bot(token=telegram_notify_token)
    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler(notify_bot, chat_id))

    vk_api_token = os.getenv("VK_API_TOKEN")
    vk_session = vk.VkApi(token=vk_api_token)
    vk_api = vk_session.get_api()

    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            echo(event, vk_api)


if __name__ == '__main__':
    main()
