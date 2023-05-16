import os
import redis
import random
import vk_api as vk

from dotenv import load_dotenv

from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import VkLongPoll, VkEventType

from general_module import set_db_result
from general_module import get_questions_with_answers


def get_score(event, vk_api, r, _):
    player_id = event.user_id
    guessed_score = r.get(f"Угадано {player_id}")
    unguessed_score = r.get(f"Не угадано {player_id}")
    if not guessed_score:
        guessed_score = 0
    if not unguessed_score:
        unguessed_score = 0
    message = f"Угадано: {guessed_score}   Не угадано: {unguessed_score}"
    show_keyboard(event, vk_api, message)


def handle_victory(event, vk_api, r, _):
    player_id = event.user_id
    set_db_result("Угадано", player_id, r)
    r.delete(player_id)
    message = "Правильно! Поздравляю! Для продолжения нажми «Новый вопрос»"
    show_keyboard(event, vk_api, message)


def handle_mistake(event, vk_api, r, _):
    player_id = event.user_id
    set_db_result("Не угадано", player_id, r)
    r.delete(player_id)
    message = "Неправильно… Попробуешь ещё раз?"
    show_keyboard(event, vk_api, message)


def give_up(event, vk_api, r, _):
    player_id = event.user_id
    answer = r.get(player_id)
    if answer:
        message = f"Правильный ответ: {answer}"
        set_db_result("Не угадано", player_id, r)
        r.delete(player_id)
    else:
        message = "Попробуешь ещё раз?"
    show_keyboard(event, vk_api, message)


def ask_next_question(event, vk_api, r, questions_with_answers):
    player_id = event.user_id
    if r.get(player_id):
        set_db_result("Не угадано", player_id, r)
        r.delete(player_id)
    question = random.choice(list(questions_with_answers.keys()))
    answer = questions_with_answers[question]
    r.set(player_id, answer)
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
    return


def launch_next_step(event, vk_api, r, questions_with_answers):
    last_input = event.text
    triggers = {
        "Новый вопрос": ask_next_question,
        "Сдаюсь": give_up,
        "Мой счёт": get_score,
        "Верный ответ": handle_victory,
        "Неверный ответ": handle_mistake,
    }
    answer = r.get(event.user_id)
    if answer:
        if last_input in answer:
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

    questions_with_answers = get_questions_with_answers(
        path_to_quiz_questions
    )

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
