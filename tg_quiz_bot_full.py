import os
import time
import redis
import logging
import telegram
import telegram.ext

from dotenv import load_dotenv
from telegram.ext import CallbackContext
from telegram import Update, ReplyKeyboardMarkup
from telegram_logs_handler import TelegramLogsHandler

from general_module import set_db_result
from general_module import get_question_with_answer


logger = logging.getLogger(__name__)


def get_score(update: Update, context: CallbackContext, r, _):
    player_id = update.effective_chat.id
    guessed_score = r.get(f"Угадано {player_id}")
    unguessed_score = r.get(f"Не угадано {player_id}")
    if not guessed_score:
        guessed_score = 0
    if not unguessed_score:
        unguessed_score = 0
    message = f"Угадано: {guessed_score}   Не угадано: {unguessed_score}"
    show_keyboard(update, context, message)


def handle_victory(update: Update, context: CallbackContext, r, _):
    player_id = update.effective_chat.id
    set_db_result("Угадано", player_id, r)
    r.delete(player_id)
    message = "Правильно! Поздравляю! Для продолжения нажми «Новый вопрос»"
    show_keyboard(update, context, message)


def handle_mistake(update: Update, context: CallbackContext, r, _):
    player_id = update.effective_chat.id
    set_db_result("Не угадано", player_id, r)
    r.delete(player_id)
    message = "Неправильно… Попробуешь ещё раз?"
    show_keyboard(update, context, message)


def give_up(update: Update, context: CallbackContext, r, _):
    player_id = update.effective_chat.id
    answer = r.get(player_id)
    if answer:
        message = f"Правильный ответ: {answer}"
        set_db_result("Не угадано", player_id, r)
        r.delete(player_id)
    else:
        message = "Попробуешь ещё раз?"
    show_keyboard(update, context, message)


def ask_next_question(
        update: Update,
        context: CallbackContext,
        r,
        path_to_quiz_questions):
    player_id = update.effective_chat.id
    if r.get(player_id):
        set_db_result("Не угадано", player_id, r)
        r.delete(player_id)
    question, answer = get_question_with_answer(
        path_to_quiz_questions
    )
    r.set(player_id, answer)
    message = question
    show_keyboard(update, context, message)


def show_keyboard(update: Update, context: CallbackContext, message):
    keyboard = [
        [
            telegram.KeyboardButton("Новый вопрос"),
            telegram.KeyboardButton("Сдаюсь")
        ],
        [telegram.KeyboardButton("Мой счёт")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)

    timesleep = 0
    while True:
        try:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                reply_markup=reply_markup,
            )
            return
        except telegram.error.NetworkError as error:
            logger.error(error)
            time.sleep(1)
        except Exception as error:
            logger.exception(error)
            time.sleep(timesleep)
            timesleep += 1
            continue


def launch_next_step(
        update: Update,
        context: CallbackContext,
        r,
        path_to_quiz_questions):
    last_input = update.message.text
    triggers = {
        "Новый вопрос": ask_next_question,
        "Сдаюсь": give_up,
        "Мой счёт": get_score,
        "Верный ответ": handle_victory,
        "Неверный ответ": handle_mistake,
    }
    answer = r.get(update.effective_chat.id)
    if answer:
        if last_input in answer:
            last_input = "Верный ответ"
        elif last_input not in triggers.keys():
            last_input = "Неверный ответ"
    trigger = triggers.get(last_input)
    if trigger:
        trigger(update, context, r, path_to_quiz_questions)
    else:
        start(update, context)


def start(update: Update, context: CallbackContext):
    message = "Привет, я бот для викторин!"
    show_keyboard(update, context, message)


def main():
    load_dotenv()

    path_to_quiz_questions = os.getenv(
        "PATH_TO_QUIZ_QUESTIONS",
        "./quiz-questions/"
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(process)d - %(levelname)s - %(message)s",
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
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    updater = telegram.ext.Updater(tg_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(telegram.ext.CommandHandler('start', start))
    dispatcher.add_handler(
        telegram.ext.MessageHandler(
            telegram.ext.Filters.text,
            lambda update, context: launch_next_step(
                update,
                context,
                r,
                path_to_quiz_questions
            )
        )
    )
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
