import os
import redis
import logging
import telegram
import telegram.ext

from dotenv import load_dotenv
from contextlib import suppress
from telegram.ext import CallbackContext
from telegram import Update, ReplyKeyboardMarkup
from telegram_logs_handler import TelegramLogsHandler

from questions_with_answers_miner import get_question_with_answer


logger = logging.getLogger(__name__)


def get_the_score(update: Update, context: CallbackContext, r):
    quiz = update.effective_chat.id
    guessed = f"Угадано {quiz}"
    unguessed = f"Не угадано {quiz}"
    guessed_score = r.get(guessed)
    unguessed_score = r.get(unguessed)
    if not guessed_score:
        guessed_score = 0
    if not unguessed_score:
        unguessed_score = 0
    message = f"Угадано: {guessed_score}   Не угадано: {unguessed_score}"
    show_the_keyboard(update, context, message)


def take_into_account(update: Update, context: CallbackContext, r, result):
    quiz = update.effective_chat.id
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


def give_congratulations(update: Update, context: CallbackContext, r):
    take_into_account(update, context, r, 1)
    message = "Правильно! Поздравляю! Для продолжения нажми «Новый вопрос»"
    show_the_keyboard(update, context, message)


def express_regret(update: Update, context: CallbackContext, r):
    take_into_account(update, context, r, 0)
    message = "Неправильно… Попробуешь ещё раз?"
    show_the_keyboard(update, context, message)


def give_up(update: Update, context: CallbackContext, r):
    quiz = update.effective_chat.id
    question = r.get(quiz)
    if question:
        answer = r.get(question)
        message = f"Правильный ответ: {answer}"
        take_into_account(update, context, r, 0)
    else:
        message = "Попробуешь ещё раз?"
    show_the_keyboard(update, context, message)


def ask_next_question(update: Update, context: CallbackContext, r):
    if r.get(update.effective_chat.id):
        take_into_account(update, context, r, 0)
        r.delete(update.effective_chat.id)
    question, answer = get_question_with_answer()
    r.set(question, answer)
    r.set(update.effective_chat.id, question)
    message = question
    show_the_keyboard(update, context, message)


def show_the_keyboard(update: Update, context: CallbackContext, message):
    keyboard = [
        [
            telegram.KeyboardButton("Новый вопрос"),
            telegram.KeyboardButton("Сдаюсь")
        ],
        [telegram.KeyboardButton("Мой счёт")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=reply_markup,
    )


def launch_next_step(update: Update, context: CallbackContext, r):
    last_input = update.message.text
    triggers = {
        "Новый вопрос": {
            "next_func": ask_next_question,
        },
        "Сдаюсь": {
            "next_func": give_up,
        },
        "Мой счёт": {
            "next_func": get_the_score,
        },
        "Верный ответ": {
            "next_func": give_congratulations,
        },
        "Неверный ответ": {
            "next_func": express_regret,
        },
    }
    asked_question = r.get(update.effective_chat.id)
    if asked_question:
        if last_input in r.get(asked_question):
            last_input = "Верный ответ"
        elif last_input not in triggers.keys():
            last_input = "Неверный ответ"
    if triggers.get(last_input):
        triggers[last_input]["next_func"](update, context, r)


def start(update: Update, context: CallbackContext):
    message = "Привет, я бот для викторин!"
    show_the_keyboard(update, context, message)


def main():
    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format="%(process)d - %(levelname)s - %(message)s",
    )

    with suppress(KeyError):
        telegram_notify_token = os.environ["TELEGRAM_NOTIFY_TOKEN"]
        chat_id = os.environ["TELEGRAM_NOTIFY_CHAT_ID"]
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

    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    updater = telegram.ext.Updater(tg_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(telegram.ext.CommandHandler('start', start))
    dispatcher.add_handler(
        telegram.ext.MessageHandler(
            telegram.ext.Filters.text,
            lambda update, context: launch_next_step(update, context, r)
        )
    )
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
