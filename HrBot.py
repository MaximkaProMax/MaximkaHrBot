import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Настройка Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("hrbot-445217-f8c4763e4a93.json", scope)  # Загрузка учетных данных из файла JSON
client = gspread.authorize(creds)  # Авторизация клиента Google Sheets

# Открытие Google Таблицы
sheet = client.open("HR Data").sheet1  # Открытие таблицы "HR Data" и выбор первого листа

# Настройка бота
API_TOKEN = '8178570976:AAE59MagRIAC1ZSQtxhnQ4ol1IAdFHrbg6E'  # Токен API вашего Telegram бота
bot = telebot.TeleBot(API_TOKEN)  # Создание экземпляра бота с использованием API токена

user_data = {}  # Словарь для хранения данных пользователя

# Запросы данных у пользователя
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Введите ФИО:")  # Отправка сообщения с запросом ФИО
    bot.register_next_step_handler(message, get_name)  # Регистрация следующего шага для получения ФИО

def get_name(message):
    user_data['name'] = message.text  # Сохранение введенного ФИО в словарь
    bot.send_message(message.chat.id, "Введите номер телефона:")  # Запрос номера телефона
    bot.register_next_step_handler(message, get_phone)  # Регистрация следующего шага для получения номера телефона

def get_phone(message):
    user_data['phone'] = message.text  # Сохранение введенного номера телефона в словарь
    bot.send_message(message.chat.id, "Введите город:")  # Запрос города
    bot.register_next_step_handler(message, get_city)  # Регистрация следующего шага для получения города

def get_city(message):
    user_data['city'] = message.text  # Сохранение введенного города в словарь
    bot.send_message(message.chat.id, "Введите должность:")  # Запрос должности
    bot.register_next_step_handler(message, get_position)  # Регистрация следующего шага для получения должности

def get_position(message):
    user_data['position'] = message.text  # Сохранение введенной должности в словарь
    save_to_sheet()  # Вызов функции для сохранения данных в таблице
    bot.send_message(message.chat.id, "Спасибо! Ваши данные сохранены.")  # Подтверждение сохранения данных

def save_to_sheet():
    row = [user_data['name'], user_data['phone'], user_data['city'], user_data['position']]  # Создание строки данных из словаря
    sheet.append_row(row)  # Добавление строки данных в таблицу

def filter_data(criteria, value):
    data = sheet.get_all_records()  # Получение всех записей из таблицы
    df = pd.DataFrame(data)  # Преобразование данных в DataFrame
    filtered_df = df[df[criteria] == value]  # Фильтрация данных по заданному критерию и значению
    print(filtered_df)  # Печать отфильтрованных данных

# Обработчик команды фильтрации
@bot.message_handler(commands=['filter'])
def filter_command(message):
    bot.send_message(message.chat.id, "Введите критерий фильтрации (например, 'city'):")  # Запрос критерия фильтрации
    bot.register_next_step_handler(message, get_filter_criteria)  # Регистрация следующего шага для получения критерия

def get_filter_criteria(message):
    criteria = message.text  # Сохранение критерия фильтрации
    bot.send_message(message.chat.id, f"Введите значение для фильтрации по {criteria}:")  # Запрос значения для фильтрации
    bot.register_next_step_handler(message, lambda msg: apply_filter(msg, criteria))  # Регистрация следующего шага для применения фильтрации

def apply_filter(message, criteria):
    value = message.text  # Сохранение значения для фильтрации
    filter_data(criteria, value)  # Вызов функции для фильтрации данных
    bot.send_message(message.chat.id, "Фильтрация завершена. Проверьте вывод в консоли.")  # Подтверждение завершения фильтрации

bot.polling()  # Запуск бесконечного цикла для обработки сообщений бота