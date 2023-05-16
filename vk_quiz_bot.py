import os
import time
import redis
import random
import logging
import telegram
import vk_api as vk

from dotenv import load_dotenv

from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import VkLongPoll, VkEventType

from telegram_logs_handler import TelegramLogsHandler

from result_saver import save_result
from questions_with_answers_miner import get_questions_with_answers


logger = logging.getLogger(__name__)


def get_score(event, vk_api, r, _):
    player_id = event.user_id
    guessed = f"Угадано {player_id}"
    unguessed = f"Не угадано {player_id}"
    guessed_score = r.get(guessed)
    unguessed_score = r.get(unguessed)
    if not guessed_score:
        guessed_score = 0
    if not unguessed_score:
        unguessed_score = 0
    message = f"Угадано: {guessed_score}   Не угадано: {unguessed_score}"
    show_keyboard(event, vk_api, message)


def handle_victory(event, vk_api, r, _):
    save_result(event.user_id, r, 1)
    message = "Правильно! Поздравляю! Для продолжения нажми «Новый вопрос»"
    show_keyboard(event, vk_api, message)


def handle_mistake(event, vk_api, r, _):
    save_result(event.user_id, r, 0)
    message = "Неправильно… Попробуешь ещё раз?"
    show_keyboard(event, vk_api, message)


def give_up(event, vk_api, r, _):
    player_id = event.user_id
    question = r.get(player_id)
    if question:
        answer = r.get(question)
        message = f"Правильный ответ: {answer}"
        save_result(player_id, r, 0)
    else:
        message = "Попробуешь ещё раз?"
    show_keyboard(event, vk_api, message)


def ask_next_question(event, vk_api, r, questions_with_answers):
    if r.get(event.user_id):
        save_result(event.user_id, r, 0)
        r.delete(event.user_id)
    question = random.choice(list(questions_with_answers.keys()))
    answer = questions_with_answers[question]
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

    timesleep = 0
    while True:
        try:
            vk_api.messages.send(
                user_id=event.user_id,
                message=message,
                random_id=get_random_id(),
                keyboard=keyboard.get_keyboard(),
            )
            return
        except Exception as error:
            logger.exception(error)
            time.sleep(timesleep)
            timesleep += 1
            continue


def launch_next_step(event, vk_api, r, questions_with_answers):
    last_input = event.text
    triggers = {
        "Новый вопрос": ask_next_question,
        "Сдаюсь": give_up,
        "Мой счёт": get_score,
        "Верный ответ": handle_victory,
        "Неверный ответ": handle_mistake,
    }
    asked_question = r.get(event.user_id)
    if asked_question:
        if last_input in r.get(asked_question):
            last_input = "Верный ответ"
        elif last_input not in triggers.keys():
            last_input = "Неверный ответ"
    trigger = triggers.get(last_input)
    if trigger:
        trigger(event, vk_api, r, questions_with_answers)
    else:
        start(event, vk_api)


def start(event, vk_api):
    message = "Привет, я бот для викторин!"
    show_keyboard(event, vk_api, message)


def main():
    load_dotenv()

    path_to_quiz_questions = os.getenv(
        "PATH_TO_QUIZ_QUESTIONS",
        "./quiz-questions/"
    )

    questions_with_answers = get_questions_with_answers (
        path_to_quiz_questions
    )

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
    r = redis.Redis(
        host=redis_pub_endpoint,
        port=redis_port,
        password=redis_password,
        decode_responses=True,
    )
    vk_api_token = os.getenv("VK_API_TOKEN")
    vk_session = vk.VkApi(token=vk_api_token)
    vk_api = vk_session.get_api()

    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            launch_next_step(
                event,
                vk_api,
                r,
                questions_with_answers
            )


if __name__ == '__main__':
    main()
