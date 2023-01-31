import datetime
import logging
import os
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import filters, MessageHandler, ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
import strings
import db
from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

TELEGRAM_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
PORT = int(os.environ.get('PORT', '8443'))
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')
HEROKU_SECRET_TOKEN = os.getenv('HEROKU_SECRET_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start"""
    user_id = update.effective_user.id
    user_name = update.effective_user.username
    # context.user_data['user_id'] = user_id
    db.create_user(user_id=user_id, user_name=user_name)
    await update.message.reply_text(strings.START_MSG)
    await update.message.reply_text(strings.INFO_MSG)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help"""
    await update.message.reply_text(strings.INFO_MSG)


async def set_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавляет новую категорию"""
    category_name = update.message.text.split()
    if len(category_name) > 1:
        answer = db.create_category(category_name[1], user_id=update.effective_user.id)
    else:
        answer = strings.ADD_CATEGORY_NOT_FULL
    await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)


async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображает все категории в виде кнопок"""
    _all_category = db.get_all_name_category(user_id=update.effective_user.id)
    if not _all_category:
        await update.message.reply_text(strings.CATEGORY_NOT_EXIST)
    else:
        keyboard = [[KeyboardButton(category)] for category in _all_category]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(strings.ALL_CATEGORY, reply_markup=reply_markup)


async def all_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Вывод клавиатуры для добавления записи и выбора дат"""

    message = update.message.text
    # если это был выбор категории
    if message in db.get_all_name_category(user_id=update.effective_user.id):
        context.user_data['category'] = message  # назначаем текущую категорию
        _all_date = db.get_date(category_name=message, user_id=update.effective_user.id)
        if _all_date:  # выводим даты в которых были расходы
            keyboard = ([[KeyboardButton(date)] for date in _all_date])
            keyboard.append([KeyboardButton('Добавить запись'), ])
            keyboard.append([KeyboardButton('/categories'), ])
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text(strings.CATEGORY_EXPENSE_DATE, reply_markup=reply_markup)
        else:
            keyboard = [[KeyboardButton('Добавить запись'), ]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text(strings.CATEGORY_EMPTY, reply_markup=reply_markup)
    else:
        await update.message.reply_text(strings.COMMAND_UNKNOWN)


async def add_expense_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Нажатие на кнопку 'Добавить запись'"""
    await context.bot.send_message(chat_id=update.effective_chat.id, text=strings.EXPENSE_ADD)


async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавляет новую запись"""
    # вырезаем число, если нужно
    _value = re.findall(pattern='\d+', string=update.message.text)[0]
    _category = context.user_data.get('category', None)
    if _category:
        db.add_expense(value=_value, category=_category, user_id=update.effective_user.id)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=strings.EXPENSE_ADD_SUCCESS)


async def del_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    _expense_value = query.data
    _category = context.user_data['category']
    db.del_expense(value=_expense_value, category=_category, user_id=update.effective_user.id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=strings.EXPENSE_DEL)


async def show_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает расходы на конкретную дату"""
    _date = update.message.text
    _category = context.user_data['category']
    _expense_by_date = db.get_expense(date=_date, category=_category, user_id=update.effective_user.id)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=strings.EXPENSE_BY_DATE)
    if _expense_by_date:  # есть ли такие даты
        for expense in _expense_by_date:
            keyboard = [[InlineKeyboardButton("Удалить", callback_data=expense)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(expense, reply_markup=reply_markup)


async def statistic(context: ContextTypes.DEFAULT_TYPE):
    """Статистика за день"""
    _all_user_id = db.get_all_user_id()
    for _user_id in _all_user_id:
        _statistic = db.statistic(user_id=_user_id)
        daily_expense = 0
        await context.bot.send_message(chat_id=_user_id, text=strings.EXPENSE_TOTAL_DAYLE_LABEL)
        for record in _statistic:
            daily_expense += record[1]
            await context.bot.send_message(chat_id=_user_id, text=f"{record[0]}: {record[1]}")
        await context.bot.send_message(chat_id=_user_id, text=f"{strings.EXPENSE_TOTAL_DAYLY}{daily_expense}")


async def total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает все расходы"""
    _total = db.total_expense(user_id=update.effective_user.id)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{strings.EXPENSE_TOTAL}{_total}")


if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    job_queue = application.job_queue
    job_minute = job_queue.run_daily(statistic, time=datetime.time(hour=21, minute=59))

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help))
    application.add_handler(CommandHandler('set_category', set_category))
    application.add_handler(CommandHandler('categories', get_category))
    application.add_handler(CommandHandler('total', total))
    application.add_handler(MessageHandler(filters.Regex(pattern=r'\d{4}-\d{2}-\d{2}'), show_expense))
    application.add_handler(MessageHandler(filters.Regex(pattern=r'\d+'), add_expense))
    application.add_handler(MessageHandler(filters.Regex(pattern=r'Добавить запись'), add_expense_button))
    application.add_handler(MessageHandler(filters.TEXT, all_text_message))
    application.add_handler(CallbackQueryHandler(del_expense))
    # application.run_polling() # если нужно запустить в polling-режиме (закомментируй код ниже)
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        secret_token=HEROKU_SECRET_TOKEN,
        webhook_url=f"https://{HEROKU_APP_NAME}.herokuapp.com/"
    )
