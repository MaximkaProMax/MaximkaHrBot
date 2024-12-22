import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import re

# Настройка Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("hrbot-445217-f8c4763e4a93.json", scope)  # Загрузка учетных данных из файла JSON
client = gspread.authorize(creds)  # Авторизация клиента Google Sheets

# Открытие Google Таблицы
sheet = client.open("HR Data").sheet1  # Открытие таблицы "HR Data" и выбор первого листа

# Настройка бота
API_TOKEN = '8178570976:AAE59MagRIAC1ZSQtxhnQ4ol1IAdFHrbg6E'  # Токен API вашего Telegram бота
bot = telebot.TeleBot(API_TOKEN)  # Создание экземпляра бота с использованием API токена

# Функция для извлечения данных из текста
def extract_data_from_text(text):
    data = {
        'name': None,
        'phone': None,
        'city': None,
        'position': None,
        'note': None
    }

    # Регулярные выражения для поиска данных
    patterns = {
        'name': r'(?:ФИО\s*)?([А-ЯЁа-яё]+\s[А-ЯЁа-яё]+\s[А-ЯЁа-яё]+)',
        'phone': r'(?:Телефон\s*)?(\+?\d{1,3}[-\s]?\(?\d{3}\)?[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}|\d{10})',
        'city': r'(?:город\s*)?(Санкт-Петербург|Москва|Мурино|Всеволожск|[А-ЯЁа-яё]+(-[А-ЯЁа-яё]+)?)',
        'position': r'(?:должность\s*)?(Программист|Менеджер|Подработка|На постоянной|Рассмотрю любые варианты|.+)',
        'note': r'(?:примечание\s*)?([\s\S]*)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()

    return data

# Запрос данных у пользователя
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Пожалуйста, введите ваши данные в любом порядке. Пример:\n"
        "Кирюшин Виктор Максимович\n"
        "Санкт-Петербург\n"
        "Девяткино\n"
        "Российское\n"
        "29\n"
        "Рассмотрю любые варианты\n"
        "+7964991-18-89"
    )
    bot.register_next_step_handler(message, process_user_data)  # Регистрация следующего шага для обработки данных

def process_user_data(message):
    text = message.text
    data = extract_data_from_text(text)  # Извлечение данных из текста

    if data['name'] and data['phone'] and data['city'] and data['position']:
        save_to_sheet(data)  # Вызов функции для сохранения данных в таблице
        bot.send_message(message.chat.id, "Спасибо! Ваши данные сохранены.")
    else:
        bot.send_message(message.chat.id, "Ошибка в данных. Пожалуйста, введите данные в правильном формате.")

def save_to_sheet(data):
    note = data['note'] or ''  # Обработка примечания
    row = [
        data['name'],
        data['phone'],
        data['city'],
        data['position'],
        note.replace(data['name'], '').replace(data['phone'], '').replace(data['city'], '').replace(data['position'], '').strip()
    ]  # Создание строки данных из словаря
    sheet.append_row(row)  # Добавление строки данных в таблицу

bot.polling()  # Запуск бесконечного цикла для обработки сообщений бота