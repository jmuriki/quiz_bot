import os
import redis
import logging
import telegram
import vk_api as vk

from dotenv import load_dotenv
from contextlib import suppress

from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import VkLongPoll, VkEventType

from telegram_logs_handler import TelegramLogsHandler

from questions_with_answers_miner import get_question_with_answer


logger = logging.getLogger(__name__)


def get_score(event, vk_api, r):
    quiz = event.user_id
    guessed = f"Угадано {quiz}"
    unguessed = f"Не угадано {quiz}"
    guessed_score = r.get(guessed)
    unguessed_score = r.get(unguessed)
    if not guessed_score:
        guessed_score = 0
    if not unguessed_score:
        unguessed_score = 0
    message = f"Угадано: {guessed_score}   Не угадано: {unguessed_score}"
    show_keyboard(event, vk_api, message)


def take_into_account(event, vk_api, r, result):
    quiz = event.user_id
    question = r.get(quiz)
    guessed = f"Угадано {quiz}"
    unguessed = f"Не угадано {quiz}"
    guessed_score = r.get(guessed)
    unguessed_score = r.get(unguessed)
    if result:
        if guessed_score:
            r.set(guessed, str(int(guessed_score) + 1))
        else:
            r.set(guessed, "1")
    else:
        if unguessed_score:
            r.set(unguessed, str(int(unguessed_score) + 1))
        else:
            r.set(unguessed, "1")
    r.delete(question)
    r.delete(quiz)


def give_congratulations(event, vk_api, r):
    take_into_account(event, vk_api, r, 1)
    message = "Правильно! Поздравляю! Для продолжения нажми «Новый вопрос»"
    show_keyboard(event, vk_api, message)


def express_regret(event, vk_api, r):
    take_into_account(event, vk_api, r, 0)
    message = "Неправильно… Попробуешь ещё раз?"
    show_keyboard(event, vk_api, message)


def give_up(event, vk_api, r):
    quiz = event.user_id
    question = r.get(quiz)
    if question:
        answer = r.get(question)
        message = f"Правильный ответ: {answer}"
        take_into_account(event, vk_api, r, 0)
    else:
        message = "Попробуешь ещё раз?"
    show_keyboard(event, vk_api, message)


def ask_next_question(event, vk_api, r):
    if r.get(event.user_id):
        take_into_account(event, vk_api, r, 0)
        r.delete(event.user_id)
    question, answer = get_question_with_answer()
    r.set(question, answer)
    r.set(event.user_id, question)
    message = question
    show_keyboard(event, vk_api, message)


def show_keyboard(event, vk_api, message):
    keyboard = VkKeyboard(one_time=True)

    keyboard.add_button('Новый вопрос')
    keyboard.add_button('Сдаюсь')

    keyboard.add_line()  # Переход на вторую строку
    keyboard.add_button('Мой счёт')

    vk_api.messages.send(
        user_id=event.user_id,
        message=message,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
    )


def launch_next_step(event, vk_api, r):
    last_input = event.text
    triggers = {
        "Новый вопрос": {
            "next_func": ask_next_question,
        },
        "Сдаюсь": {
            "next_func": give_up,
        },
        "Мой счёт": {
            "next_func": get_score,
        },
        "Верный ответ": {
            "next_func": give_congratulations,
        },
        "Неверный ответ": {
            "next_func": express_regret,
        },
    }
    asked_question = r.get(event.user_id)
    if asked_question:
        if last_input in r.get(asked_question):
            last_input = "Верный ответ"
        elif last_input not in triggers.keys():
            last_input = "Неверный ответ"
    if triggers.get(last_input):
        triggers[last_input]["next_func"](event, vk_api, r)
    else:
        message = "Привет, я бот для викторин!"
        show_keyboard(event, vk_api, message)


def main():
    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(process)d %(levelname)s %(message)s",
    )

    telegram_notify_token = os.getenv("TELEGRAM_NOTIFY_TOKEN")
    chat_id = os.getenv("TELEGRAM_NOTIFY_CHAT_ID")
    if telegram_notify_token and chat_id:
        notify_bot = telegram.Bot(token=telegram_notify_token)
        logger.setLevel(logging.INFO)
        logger.addHandler(TelegramLogsHandler(notify_bot, chat_id))

    redis_pub_endpoint = os.getenv("REDIS_PUBLIC_ENDPOINT")
    redis_port = int(os.getenv("REDIS_PORT"))
    redis_password = os.getenv("REDIS_PASSWORD")
    try:
        r = redis.Redis(
            host=redis_pub_endpoint,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
        )
    except Exception as error:
        logger.exception(error)

    vk_api_token = os.getenv("VK_API_TOKEN")
    vk_session = vk.VkApi(token=vk_api_token)
    vk_api = vk_session.get_api()

    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            launch_next_step(event, vk_api, r)


if __name__ == '__main__':
    main()
