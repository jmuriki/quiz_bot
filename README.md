# quiz_bot

Бот для игры в викторину. Обладает обширной базой вопросов. Ведёт учёт результативности для каждого отдельного чата в облачной базе данных.

Поиграть можно в [VK](https://vk.com/club219903049) и в [Telegram](https://t.me/DevmanQuizBot)

## Локальная установка

Скачайте код:
```sh
git clone https://github.com/jmuriki/quiz_bot.git
```

Перейдите в каталог проекта:
```sh
cd quiz_bot
```

[Установите Python](https://www.python.org/), если ещё не успели.

Проверьте, что `python` установлен и корректно настроен. Запустите в командной строке:
```sh
python --version
```
Код написан на версии 3.8.

Возможно, вместо команды `python` здесь и в остальных инструкциях этого README придётся использовать `python3`. Это зависит от операционной системы и от того, установлен ли у вас `python2`. 

В каталоге проекта создайте виртуальное окружение:
```sh
python -m venv venv
```
Активируйте его. На разных операционных системах это делается разными командами:

- Windows: `.\venv\Scripts\activate`
- MacOS/Linux: `source venv/bin/activate`

Установите зависимости в виртуальное окружение:
```sh
pip install -r requirements.txt
```

### Переменные окружения

Определите переменные окружения:
- `TELEGRAM_BOT_TOKEN` - токен вашего telegram бота
- `TELEGRAM_NOTIFY_TOKEN` - токен вашего вспомогательного бота для логов (опционально)
- `TELEGRAM_NOTIFY_CHAT_ID` - id вашего telegram чата для логов (опционально)
- `VK_API_TOKEN` - токен вашего сообщества vk
- `REDIS_PASSWORD` - пароль аккаунта [Redis](https://redis.com) (бесплатно)
- `REDIS_PUBLIC_ENDPOINT` - public endpoint вашей БД [Redis](https://redis.com)
- `REDIS_PORT` - порт вашей БД [Redis](https://redis.com)


Создайте файл `.env` в каталоге `quiz_bot/` и положите туда такой код, заполнив значения переменных:
```sh

TELEGRAM_BOT_TOKEN=
VK_API_TOKEN=
REDIS_PUBLIC_ENDPOINT=
REDIS_PORT=
REDIS_PASSWORD=

TELEGRAM_NOTIFY_TOKEN=
TELEGRAM_NOTIFY_CHAT_ID=

```
### База вопросов и ответов

Скачайте [архив](https://dvmn.org/media/modules_dist/quiz-questions.zip) с вопросами и распакуйте его в предварительно созданную папку `quiz_bot/quiz-question/`.

## Запуск

### vk_quiz_bot.py

Находясь в директории проекта, откройте с помощью python файл `vk_quiz_bot.py`

```sh
python vk_quiz_bot.py
```
### tg_quiz_bot.py

Находясь в директории проекта, откройте с помощью python файл `tg_quiz_bot.py`

```sh
python tg_quiz_bot.py
```
### telegram_logs_handler.py

Это вспомогательный файл, содержащий класс telegram для обработки логов/исключений.

## Цели проекта

Код написан в учебных целях — это урок в курсе по Python и веб-разработке на сайте [Devman](https://dvmn.org).
