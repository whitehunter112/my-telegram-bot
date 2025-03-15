from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import logging
import random
from dateutil import parser  # Импортируем модуль для распознавания дат

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Список мотивирующих сообщений
MOTIVATIONAL_MESSAGES = [
    "Ты становишься только лучше!",
    "У тебя всё выйдет!",
    "Будь тем, кем хочется тебе!",
    "Не забывай, ради чего ты живешь!",
    "Сегодня будет лучше, чем вчера!",
    "Делай, что можешь, с тем, что ты имеешь, там, где ты есть!"
]

# Функция для расчета времени
def calculate_time_since_birth(birth_date):
    now = datetime.now()
    delta = now - birth_date
    weeks = delta.days // 7
    days = delta.days
    minutes = delta.total_seconds() // 60
    seconds = delta.total_seconds()
    return weeks, days, minutes, seconds

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Введите вашу дату рождения (например, 01.01.2000, 01/01/2000 или 01-01-2000):')

# Обработка введенной даты рождения
async def handle_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Используем dateutil.parser для распознавания даты в разных форматах
        birth_date = parser.parse(update.message.text, dayfirst=True)
        context.user_data['birth_date'] = birth_date
        weeks, days, minutes, seconds = calculate_time_since_birth(birth_date)
        await update.message.reply_text(f'Вы прожили:\n'
                                       f'{weeks} недель,\n'
                                       f'{days} дней,\n'
                                       f'{int(minutes)} минут,\n'
                                       f'{int(seconds)} секунд.')
        # Запуск задачи для уведомлений
        context.job_queue.run_repeating(notify_weekly, interval=604800, first=0, chat_id=update.message.chat_id)
    except (ValueError, parser.ParserError):
        # Если дата введена неправильно, передаем сообщение в handle_message
        await handle_message(update, context)

# Уведомление каждую неделю
async def notify_weekly(context: ContextTypes.DEFAULT_TYPE) -> None:
    birth_date = context.user_data.get('birth_date')
    if birth_date:
        weeks = calculate_time_since_birth(birth_date)[0]  # Считаем только недели
        await context.bot.send_message(context.job.chat_id, text=f'Прошла ещё одна неделя! Всё будет только лучше! Теперь вы прожили {weeks} недель.')

# Обработка любого другого сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Выбираем случайное мотивирующее сообщение
    message = random.choice(MOTIVATIONAL_MESSAGES)
    await update.message.reply_text(message)

# Основная функция
def main() -> None:
    # Вставьте сюда ваш токен
    application = Application.builder().token("8156357645:AAFF7YFPkw3d7-OI37y-Jg936JeYqq3G1A0").build()

    # Регистрируем обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_birthdate))
    
    # Обработка любых других сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()
