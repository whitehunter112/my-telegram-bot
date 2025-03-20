import os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta
import logging
import random
import re
from apscheduler.schedulers.background import BackgroundScheduler

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

# Ваш Telegram ID (замените на свой)
ADMIN_ID = 792952595  # Например: 123456789

# Расширенная библиотека мотивационных сообщений
MOTIVATIONAL_MESSAGES = {
    "quotes": [
        "Успех — это способность идти от неудачи к неудаче, не теряя энтузиазма. — Уинстон Черчилль",
        "Единственный способ сделать великую работу — любить то, что ты делаешь. — Стив Джобс",
        "Не бойтесь отказываться от хорошего в пользу великого. — Джон Д. Рокфеллер",
        "Ваше время ограничено, не тратьте его, живя чужой жизнью. — Стив Джобс",
        "Сложнее всего начать действовать, все остальное зависит только от упорства. — Амелия Эрхарт",
    ],
    "phrases": [
        "Ты сильнее, чем думаешь!",
        "Каждый маленький шаг приближает тебя к большой цели.",
        "Сегодня — это новый шанс стать лучше.",
        "Ты можешь всё, если поверишь в себя.",
        "Не сдавайся, даже если трудно.",
        "Ты становишься только лучше!",
        "У тебя всё выйдет!",
        "Будь тем, кем хочется тебе!",
        "Не забывай, ради чего ты живешь!",
        "Сегодня будет лучше, чем вчера!",
        "Делай, что можешь, с тем, что ты имеешь, там, где ты есть!",
        "Всё, что ты видишь вокруг, — это результат твоего пути."
    ],
    "advice": [
        "Начни свой день с планирования. Запиши три главные задачи на сегодня.",
        "Учись чему-то новому каждый день. Знания — это сила.",
        "Окружай себя людьми, которые вдохновляют тебя.",
        "Не бойся ошибок. Они — часть пути к успеху.",
        "Делай перерывы. Отдых помогает сохранить энергию.",
    ],
    "stories": [
        "Томас Эдисон сделал 1000 неудачных попыток, прежде чем изобрел лампочку. Он сказал: 'Я не потерпел неудачу. Я просто нашел 1000 способов, которые не работают.'",
        "Джоан Роулинг получила отказ от 12 издательств, прежде чем 'Гарри Поттер' был опубликован. Сегодня она одна из самых успешных писательниц в мире.",
        "Стивен Спилберг был отвергнут киношколой три раза. Но он не сдался и стал одним из самых известных режиссеров.",
        "Опра Уинфри была уволена с первой работы на телевидении. Сегодня она медиамагнат и одна из самых влиятельных женщин в мире.",
        "Альберт Эйнштейн не говорил до четырех лет и считался трудным ребенком. Но он изменил мир своими открытиями.",
    ],
}

# Клавиатура с кнопками "Мотивация" и "Обновить дату"
motivation_keyboard = ReplyKeyboardMarkup([["Мотивация", "Обновить дату"]], resize_keyboard=True)

# Клавиатура для администратора
admin_keyboard = ReplyKeyboardMarkup(
    [
        ["Мотивация", "Обновить дату"],
        ["Проверить недели", "Рассылка текста"],
    ],
    resize_keyboard=True,
)

# Словарь для хранения данных пользователей
user_data = {}

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
    context.user_data.pop('birth_date', None)  # Сброс введённой даты

    await update.message.reply_text('Привет! Введите вашу дату рождения в формате ДД.ММ.ГГГГ (например, 01.01.2000):')

# Команда /admin (только для администратора)
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    
    if user.id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде!")
        return
    
    await update.message.reply_text('Панель администратора активирована.', reply_markup=admin_keyboard)

# Обновление количества прожитых дней
async def update_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'birth_date' not in context.user_data:
        await update.message.reply_text('Сначала введите вашу дату рождения с помощью команды /start.')
        return
    
    birth_date = context.user_data['birth_date']
    weeks, days, minutes, seconds = calculate_time_since_birth(birth_date)
    
    await update.message.reply_text(
        f'Вы прожили:\n'
        f'{weeks} недель,\n'
        f'{days} дней,\n'
        f'{int(minutes)} минут,\n'
        f'{int(seconds)} секунд.',
        reply_markup=motivation_keyboard  # Новая клавиатура
    )

# Обработка даты рождения
async def handle_birthdate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Проверяем, была ли уже введена дата
    if 'birth_date' in context.user_data:
        await update.message.reply_text(
            "❌ Ошибка! Вы уже вводили дату. Используйте кнопку 'Мотивация', 'Обновить дату' или введите команду /start."
        )
        return
    
    text = update.message.text.strip()
    if not re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", text):
        await update.message.reply_text(
            "❌ Ошибка! Введите дату в формате ДД.ММ.ГГГГ (например, 01.01.2000)."
        )
        return
    
    try:
        birth_date = datetime.strptime(text, "%d.%m.%Y")
        if birth_date.year < 1900 or birth_date.year > datetime.now().year:
            await update.message.reply_text(
                "❌ Ошибка! Год должен быть между 1900 и текущим годом."
            )
            return
        if birth_date > datetime.now():
            await update.message.reply_text(
                "❌ Ошибка! Дата рождения не может быть в будущем."
            )
            return
        context.user_data['birth_date'] = birth_date
        user_data[update.message.chat_id] = birth_date
        weeks, days, minutes, seconds = calculate_time_since_birth(birth_date)
        
        await update.message.reply_text(
            f'Вы прожили:\n'
            f'{weeks} недель,\n'
            f'{days} дней,\n'
            f'{int(minutes)} минут,\n'
            f'{int(seconds)} секунд.',
            reply_markup=motivation_keyboard  # Новая клавиатура
        )
    except ValueError:
        await update.message.reply_text(
            "❌ Ошибка! Введите корректную дату в формате ДД.ММ.ГГГГ."
        )

# Обработчик кнопки "Мотивация"
async def motivation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Случайно выбираем категорию
    category = random.choice(list(MOTIVATIONAL_MESSAGES.keys()))
    # Случайно выбираем сообщение из выбранной категории
    message = random.choice(MOTIVATIONAL_MESSAGES[category])
    await update.message.reply_text(message)

# Обработчик кнопки "Проверить недели"
async def check_week_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде!")
        return

    if 'birth_date' not in context.user_data:
        await update.message.reply_text("⚠ Сначала введите свою дату рождения!")
        return
    
    birth_date = context.user_data['birth_date']
    now = datetime.now()
    weeks = (now - birth_date).days // 7

    await update.message.reply_text(f"Вы прожили **{weeks}** недель!")

# Обработчик кнопки "Рассылка текста"
async def broadcast_text_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде!")
        return
    
    await update.message.reply_text("Введите текст для рассылки:")

# Обработчик текста для рассылки
async def handle_broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ У вас нет доступа к этой команде!")
        return
    
    text = update.message.text
    
    # Рассылка текста всем пользователям
    for chat_id in user_data.keys():
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение пользователю {chat_id}: {e}")
    
    await update.message.reply_text("✅ Текст успешно отправлен всем пользователям!")

# Автоматическое обновление недель по понедельникам
def weekly_update():
    now = datetime.now()
    if now.weekday() == 0:  # Проверяем, понедельник ли сегодня
        for chat_id, birth_date in user_data.items():
            weeks = (now - birth_date).days // 7
            application.bot.send_message(chat_id=chat_id, text=f"Сегодня понедельник! Вы прожили **{weeks}** недель!")

# Обработчик некорректных сообщений
async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'birth_date' in context.user_data:
        await update.message.reply_text(
            "❌ Ошибка! Используйте кнопку 'Мотивация', 'Обновить дату' или введите команду /start."
        )
    else:
        await update.message.reply_text(
            "❌ Ошибка! Введите корректную дату в формате ДД.ММ.ГГГГ или нажмите /start."
        )

# Запуск бота
def run_bot():
    global application
    application = Application.builder().token("8156357645:AAFF7YFPkw3d7-OI37y-Jg936JeYqq3G1A0").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(MessageHandler(filters.Regex(r"^\d{2}\.\d{2}\.\d{4}$"), handle_birthdate))
    application.add_handler(MessageHandler(filters.Regex("^Мотивация$"), motivation))
    application.add_handler(MessageHandler(filters.Regex("^Обновить дату$"), update_date))
    application.add_handler(MessageHandler(filters.Regex("^Проверить недели$"), check_week_button))
    application.add_handler(MessageHandler(filters.Regex("^Рассылка текста$"), broadcast_text_button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast_text))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message))
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(weekly_update, 'cron', day_of_week='mon', hour=0)
    scheduler.start()
    
    application.run_polling()

# Поток для бота
def run():
    Thread(target=run_bot).start()

if __name__ == "__main__":
    run_bot()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
