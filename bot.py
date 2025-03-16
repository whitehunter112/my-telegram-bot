from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import logging
import random
from dateutil import parser  

app = Flask(__name__)

@app.route('/')
def index():
    return "Бот работает!"

# Логирование
logging.basicConfig(
    filename='bot.log',  
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO  
)
logger = logging.getLogger(__name__)

# Мотивационные сообщения
MOTIVATIONAL_MESSAGES = [
    "Ты становишься только лучше!",
    "У тебя всё выйдет!",
    "Будь тем, кем хочется тебе!",
    "Не забывай, ради чего ты живешь!",
    "Сегодня будет лучше, чем вчера!",
    "Делай, что можешь, с тем, что ты имеешь, там, где ты есть!",
    "Всё, что ты видишь вокруг, — это результат твоего пути."
]

# Расчёт времени с момента рождения
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
    user = update.message.from_user
    logger.info(f"Пользователь {user.first_name} (id: {user.id}) начал взаимодействие с ботом.")
    await update.message.reply_text('Привет! Введите вашу дату рождения (например, 01.01.2000, 01/01/2000 или 01-01-2000):')

# Обработка даты рождения
async def handle_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        birth_date = parser.parse(update.message.text, dayfirst=True)
        context.user_data['birth_date'] = birth_date
        weeks, days, minutes, seconds = calculate_time_since_birth(birth_date)
        await update.message.reply_text(f'Вы прожили:\n'
                                       f'{weeks} недель,\n'
                                       f'{days} дней,\n'
                                       f'{int(minutes)} минут,\n'
                                       f'{int(seconds)} секунд.')
        context.job_queue.run_repeating(notify_weekly, interval=604800, first=0, chat_id=update.message.chat_id)
    except (ValueError, parser.ParserError):
        await handle_message(update, context)

# Уведомление каждую неделю
async def notify_weekly(context: ContextTypes.DEFAULT_TYPE) -> None:
    birth_date = context.user_data.get('birth_date')
    if birth_date:
        weeks = calculate_time_since_birth(birth_date)[0]
        await context.bot.send_message(context.job.chat_id, text=f'Прошла ещё одна неделя! Теперь вы прожили {weeks} недель.')

# Обработка других сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = random.choice(MOTIVATIONAL_MESSAGES)
    await update.message.reply_text(message)

# Запуск бота
def run_bot():
    application = Application.builder().token("8156357645:AAFF7YFPkw3d7-OI37y-Jg936JeYqq3G1A0").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_birthdate))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

# Поток для бота
def run():
    Thread(target=run_bot).start()

if __name__ == "__main__":
    run()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
