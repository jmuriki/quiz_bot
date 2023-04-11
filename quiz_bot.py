import os
import telegram
import telegram.ext

from pathlib import Path
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


def is_system_file(filename):
    system_files_extentions = [".DS_Store"]
    return any(extention in filename for extention in system_files_extentions)


def collect_questions_with_answers():
    quiz_questions_path = Path("../quiz-questions").resolve()
    filepaths = []
    for root, _, filenames in os.walk(quiz_questions_path):
        for filename in filenames:
            if not is_system_file(filename):
                filepath = os.path.join(root, filename)
                filepaths.append(filepath)
    questions_with_answers = {}
    for filepath in filepaths:
        with open(filepath, encoding="KOI8-R") as file:
            text = file.read()
        paragraphs = [text_part.strip() for text_part in text.split("\n\n")]
        question = None
        while paragraphs:
            paragraph = paragraphs.pop(0)
            if paragraph.startswith("Вопрос"):
                question = paragraph.split(":\n")[-1]
            elif paragraph.startswith("Ответ"):
                questions_with_answers[question] = paragraph.split(":\n")[-1]


def start(update: telegram.Update, context: telegram.ext.CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Здравствуйте!',
    )


def echo(update, context):
    update.message.reply_text(update.message.text)


def main():
    load_dotenv()
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    updater = Updater(tg_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text, echo))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
