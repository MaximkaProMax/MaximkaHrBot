import os
import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
from geopy.geocoders import Nominatim

# Настройка прокси (если необходимо)
# os.environ['HTTP_PROXY'] = 'http://your-proxy:port'
# os.environ['HTTPS_PROXY'] = 'https://your-proxy:port'

# Настройка Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("hrbot-445217-f8c4763e4a93.json", scope)
client = gspread.authorize(creds)

# Открытие Google Таблицы
try:
    sheet = client.open("HR Data").sheet1
except Exception as e:
    print(f"Ошибка при подключении к Google Sheets: {e}")

# Настройка бота
API_TOKEN = '8178570976:AAE59MagRIAC1ZSQtxhnQ4ol1IAdFHrbg6E'
bot = telebot.TeleBot(API_TOKEN, parse_mode=None, threaded=False)

# Инициализация геокодера
geolocator = Nominatim(user_agent="hrbot")

# Функция для извлечения данных из текста на основе тегов
def extract_data_from_text(text):
    data = {
        'ФИО': '---',
        'Номер': '---',
        'Город': '---',
        'Метро': '---',
        'Гражданство': '---',
        'Возраст': '---',
        'Примечание один': '---',
        'Примечание два': '---'
    }

    patterns = {
        'ФИО': r'ФИО:\s*(.*)',
        'Номер': r'Номер:\s*(.*)',
        'Город': r'Город:\s*(.*)',
        'Метро': r'Метро:\s*(.*)',
        'Гражданство': r'Гражданство:\s*(.*)',
        'Возраст': r'Возраст:\s*(.*)',
        'Примечание один': r'Примечание один:\s*(.*)',
        'Примечание два': r'Примечание два:\s*(.*)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            data[key] = match.group(1).strip()

    # Использование geopy для поиска города
    city_match = data['Город']
    if city_match != '---':
        location = geolocator.geocode(city_match)
        if location:
            data['Город'] = location.address.split(",")[0]

    return data

# Запрос данных у пользователя
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Пожалуйста, введите ваши данные с использованием следующих тегов:\n"
        "ФИО, Номер, Город, Метро, Гражданство, Возраст, Примечание один, Примечание два.\n"
        "Пример:\n"
        "ФИО: Иванов Иван Иванович\n"
        "Номер: 8 800 555 35 55\n"
        "Город: Москва\n"
        "Метро: Маяковская\n"
        "Гражданство: РФ\n"
        "Возраст: 18\n"
        "Примечание один: Готов выйти на работу 01.01.2025\n"
        "Примечание два: Работа в коллективе"
    )
    bot.register_next_step_handler(message, process_user_data)

def process_user_data(message):
    text = message.text
    data = extract_data_from_text(text)

    if any(data[key] != '---' for key in data.keys()):
        save_to_sheet(data)
        bot.send_message(message.chat.id, "Спасибо! Ваши данные сохранены.")
    else:
        bot.send_message(message.chat.id, "Ошибка в данных. Пожалуйста, введите данные в правильном формате.")

# Функция для сохранения данных в таблице
def save_to_sheet(data):
    row = [
        data['ФИО'],
        data['Номер'],
        data['Город'],
        data['Метро'],
        data['Гражданство'],
        data['Возраст'],
        data['Примечание один'],
        data['Примечание два']
    ]
    try:
        sheet.append_row(row)
    except Exception as e:
        print(f"Ошибка при записи данных в Google Sheets: {e}")

# Обработка всех сообщений от пользователей
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    process_user_data(message)

# Запуск бесконечного цикла для обработки сообщений бота с увеличенным временем ожидания
try:
    bot.polling(timeout=120, long_polling_timeout=120)
except Exception as e:
    print(f"Ошибка при подключении к Telegram API: {e}")