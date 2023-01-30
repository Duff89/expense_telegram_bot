FROM  python:3.11-slim

WORKDIR /home

ENV TELEGRAM_API_TOKEN=''
ENV HEROKU_APP_NAME = ''
ENV HEROKU_SECRET_TOKEN = ''

RUN apt-get update && apt-get install sqlite3
RUN pip install pip python-telegram-bot python-telegram-bot[job-queue]
COPY *.py ./
COPY expense.db ./

ENTRYPOINT ["python", "bot.py"]