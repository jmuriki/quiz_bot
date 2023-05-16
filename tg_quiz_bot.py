import os
import redis
import random
import telegram
import telegram.ext

from dotenv import load_dotenv
from telegram.ext import CallbackContext
from telegram import Update, ReplyKeyboardMarkup

from result_saver import save_result
from questions_with_answers_miner import get_questions_with_answers


def get_score(update: Update, context: CallbackContext, r, _):
    player_id = update.effective_chat.id
    guessed = f"Угадано {player_id}"
    unguessed = f"Не угадано {player_id}"
    guessed_score = r.get(guessed)
    unguessed_score = r.get(unguessed)
    if not guessed_score:
        guessed_score = 0
    if not unguessed_score:
        unguessed_score = 0
    message = f"Угадано: {guessed_score}   Не угадано: {unguessed_score}"
    show_keyboard(update, context, message)


def handle_victory(update: Update, context: CallbackContext, r, _):
    save_result(update.effective_chat.id, r, 1)
    message = "Правильно! Поздравляю! Для продолжения нажми «Новый вопрос»"
    show_keyboard(update, context, message)


def handle_mistake(update: Update, context: CallbackContext, r, _):
    save_result(update.effective_chat.id, r, 0)
    message = "Неправильно… Попробуешь ещё раз?"
    show_keyboard(update, context, message)


def give_up(update: Update, context: CallbackContext, r, _):
    player_id = update.effective_chat.id
    question = r.get(player_id)
    if question:
        answer = r.get(question)
        message = f"Правильный ответ: {answer}"
        save_result(player_id, r, 0)
    else:
        message = "Попробуешь ещё раз?"
    show_keyboard(update, context, message)


def ask_next_question(
        update: Update,
        context: CallbackContext,
        r,
        questions_with_answers):
    if r.get(update.effective_chat.id):
        save_result(update.effective_chat.id, r, 0)
        r.delete(update.effective_chat.id)
    question = random.choice(list(questions_with_answers.keys()))
    answer = questions_with_answers[question]
    r.set(question, answer)
    r.set(update.effective_chat.id, question)
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

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=reply_markup,
    )
    return


def launch_next_step(
        update: Update,
        context: CallbackContext,
        r,
        questions_with_answers):
    last_input = update.message.text
    triggers = {
        "Новый вопрос": ask_next_question,
        "Сдаюсь": give_up,
        "Мой счёт": get_score,
        "Верный ответ": handle_victory,
        "Неверный ответ": handle_mistake,
    }
    asked_question = r.get(update.effective_chat.id)
    if asked_question:
        if last_input in r.get(asked_question):
            last_input = "Верный ответ"
        elif last_input not in triggers.keys():
            last_input = "Неверный ответ"
    trigger = triggers.get(last_input)
    if trigger:
        trigger(update, context, r, questions_with_answers)
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
                questions_with_answers
            )
        )
    )
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
