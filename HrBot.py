import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Настройка Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("hrbot-445217-f8c4763e4a93.json", scope)
client = gspread.authorize(creds)

# Открытие Google Таблицы
sheet = client.open("HR Data").sheet1

# Настройка бота
API_TOKEN = '8178570976:AAE59MagRIAC1ZSQtxhnQ4ol1IAdFHrbg6E'  # Ваш API токен
bot = telebot.TeleBot(API_TOKEN)

user_data = {}

# Запросы данных у пользователя
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Введите ФИО:")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    user_data['name'] = message.text
    bot.send_message(message.chat.id, "Введите номер телефона:")
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    user_data['phone'] = message.text
    bot.send_message(message.chat.id, "Введите город:")
    bot.register_next_step_handler(message, get_city)

def get_city(message):
    user_data['city'] = message.text
    bot.send_message(message.chat.id, "Введите должность:")
    bot.register_next_step_handler(message, get_position)

def get_position(message):
    user_data['position'] = message.text
    save_to_sheet()
    bot.send_message(message.chat.id, "Спасибо! Ваши данные сохранены.")

def save_to_sheet():
    row = [user_data['name'], user_data['phone'], user_data['city'], user_data['position']]
    sheet.append_row(row)

def filter_data(criteria, value):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    filtered_df = df[df[criteria] == value]
    print(filtered_df)

# Обработчик команды фильтрации
@bot.message_handler(commands=['filter'])
def filter_command(message):
    bot.send_message(message.chat.id, "Введите критерий фильтрации (например, 'city'):")
    bot.register_next_step_handler(message, get_filter_criteria)

def get_filter_criteria(message):
    criteria = message.text
    bot.send_message(message.chat.id, f"Введите значение для фильтрации по {criteria}:")
    bot.register_next_step_handler(message, lambda msg: apply_filter(msg, criteria))

def apply_filter(message, criteria):
    value = message.text
    filter_data(criteria, value)
    bot.send_message(message.chat.id, "Фильтрация завершена. Проверьте вывод в консоли.")

bot.polling()