import os
import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import re

# Настройка прокси (если необходимо)
# os.environ['HTTP_PROXY'] = 'http://your-proxy:port'
# os.environ['HTTPS_PROXY'] = 'https://your-proxy:port'

# Настройка Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("hrbot-445217-f8c4763e4a93.json", scope)  # Загрузка учетных данных из файла JSON
client = gspread.authorize(creds)  # Авторизация клиента Google Sheets

# Открытие Google Таблицы
try:
    sheet = client.open("HR Data").sheet1  # Открытие таблицы "HR Data" и выбор первого листа
except Exception as e:
    print(f"Ошибка при подключении к Google Sheets: {e}")

# Настройка бота
API_TOKEN = '8178570976:AAE59MagRIAC1ZSQtxhnQ4ol1IAdFHrbg6E'  # Токен API вашего Telegram бота
bot = telebot.TeleBot(API_TOKEN, parse_mode=None, threaded=False)  # Создание экземпляра бота с использованием API токена

# Увеличение времени ожидания
bot.timeout = 120  # Установите большее время ожидания для соединений
bot.read_timeout = 120  # Установите большее время ожидания для чтения данных

# Функция для извлечения данных из текста
def extract_data_from_text(text):
    data = {
        'name': '---',
        'age': '---',
        'city': '---',
        'citizenship': '---',
        'phone': '---',
        'employment_type': '---',
        'start_date': '---',
        'note': '---'
    }

    # Регулярные выражения для поиска данных
    patterns = {
        'name': r'([А-ЯЁа-яё]+ [А-ЯЁа-яё]+ [А-ЯЁа-яё]+)',
        'age': r'(?:Возраст )?(\d+)',
        'city': r'(г\. [А-ЯЁа-яё]+|[А-ЯЁа-яё]+(-[А-ЯЁа-яё]+)?)',
        'citizenship': r'Гражданство ([А-ЯЁа-яё]+)',
        'phone': r'(\+?\д{1,3}?[\- ]?\(?\д{3}?\)?[\- ]?\д{3}[\- ]?\д{2}[\- ]?\д{2})',
        'employment_type': r'(полный|частичный|подработка|на постоянной основе)',
        'start_date': r'(?:готов приступать к работе )?(.+)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()

    # Обработка примечаний
    note_text = text
    used_data = set(data.values())
    for key, value in data.items():
        if value != '---' and value in used_data:
            note_text = note_text.replace(value, '').strip()
    data['note'] = note_text if note_text and note_text != text else '---'

    return data

# Запрос данных у пользователя
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Пожалуйста, введите ваши данные в любом порядке. Пример:\n"
        "Кирюшин Виктор Максимович\n"
        "Санкт-Петербург\n"
        "Девяткино Российское\n"
        "Возраст 29\n"
        "Рассмотрю любые варианты\n"
        "+7964991-18-89"
    )
    bot.register_next_step_handler(message, process_user_data)  # Регистрация следующего шага для обработки данных

def process_user_data(message):
    text = message.text
    data = extract_data_from_text(text)  # Извлечение данных из текста

    if any(data[key] != '---' for key in data.keys()):
        save_to_sheet(data)  # Вызов функции для сохранения данных в таблице
        bot.send_message(message.chat.id, "Спасибо! Ваши данные сохранены.")
    else:
        bot.send_message(message.chat.id, "Ошибка в данных. Пожалуйста, введите данные в правильном формате.")

# Функция для сохранения данных в таблице
def save_to_sheet(data):
    row = [
        data['name'],
        data['age'],
        data['city'],
        data['citizenship'],
        data['phone'],
        data['employment_type'],
        data['start_date'],
        data['note']
    ]  # Создание строки данных из словаря
    try:
        sheet.append_row(row)  # Добавление строки данных в таблицу
    except Exception as e:
        print(f"Ошибка при записи данных в Google Sheets: {e}")

# Обработка всех сообщений от пользователей
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    process_user_data(message)  # Обработка каждого сообщения

# Запуск бесконечного цикла для обработки сообщений бота с увеличенным временем ожидания
try:
    bot.polling(timeout=120, long_polling_timeout=120)
except Exception as e:
    print(f"Ошибка при подключении к Telegram API: {e}")

import pandas as pd

# Функция для разделения данных на отдельные столбцы
def split_data_into_columns():
    try:
        # Получение всех данных из таблицы
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        # Обновление таблицы
        df_expanded = df.fillna('---')
        sheet.clear()
        sheet.update([df_expanded.columns.values.tolist()] + df_expanded.values.tolist())
        print("Данные успешно разделены на столбцы и обновлены в таблице.")
    except Exception as e:
        print(f"Ошибка при разделении данных на столбцы: {e}")

# Вызов функции для разделения данных на столбцы
split_data_into_columns()