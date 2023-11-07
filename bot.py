import openai
import telebot
from pymongo import MongoClient

client = MongoClient('MONGO_TOKEN')
db = client.usersdb.users


definite = False


openai.api_key = 'OPENAI_TOKEN'
bot = telebot.TeleBot('TG_TOKEN')
mode = 0

phone = 0
# приветсвие, запрос номера
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, """\
Привет\
""")
    kb = telebot.types.ReplyKeyboardMarkup(True, True)
    kb.add(telebot.types.KeyboardButton('Отправить контакт', request_contact=True))
    bot.send_message(message.chat.id, text = "нажмите на кнопку, чтобы поделиться контактом",reply_markup=kb)


# обработка номера, отправка в таблицу
@bot.message_handler(content_types=['contact'])
def contact(message):
    if message.contact is not None:
        global phone, definite
        phone = str(message.contact.phone_number)
        user = db.find({'phone': str(message.contact.phone_number)})
        if user: 
        # if dict_user['phone'] == str(phone):
            bot.send_message(message.chat.id, text = "вы авторизовались, выберите режим")
            definite = True
            mode_selection(message)
        else:
            definite = False
            send_welcome(message)


# выбор режимов
@bot.message_handler(commands=['choise'])
def mode_selection(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    button1 = telebot.types.InlineKeyboardButton(text="по умолчанию", callback_data="button1")
    button2 = telebot.types.InlineKeyboardButton(text="Кнопка 2", callback_data="button2")
    button3 = telebot.types.InlineKeyboardButton(text="Кнопка 3", callback_data="button3")
    button4 = telebot.types.InlineKeyboardButton(text="Кнопка 4", callback_data="button4")
    keyboard.add(button1)
    keyboard.add(button2)
    keyboard.add(button3)
    keyboard.add(button4)
    bot.send_message(message.chat.id, text="Выберите режим", reply_markup=keyboard)
    # dict_user['messages'] = []
    db.update_one({'phone': phone}, {'$set': {'messages': []}})


# обработка режимов
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if not definite: return 0
    global mode
    if call.message:
        if call.data == "button1":
            mode = 0
            bot.send_message(call.message.chat.id, text="Вы выбрали первую роль")
        if call.data == "button2":
            mode = 1
            bot.send_message(call.message.chat.id, text="Вы выбрали вторую роль")
        if call.data == "button3":
            mode = 2
            bot.send_message(call.message.chat.id, text="Вы выбрали третью роль")
        if call.data == "button4":
            mode = 3
            bot.send_message(call.message.chat.id, text="Вы выбрали четвертую роль")


# запросы к чатгпт
@bot.message_handler(func = lambda _: True)
def handle_messeage(message):
    global mode, definite,phone
    if not definite: return 0
    dict_user['messages'].append({'role': 'user', 'content': message.text})
    db.update_one({'phone': phone}, {'$push': {'messages': {'role': 'user', 'content': message.text }}})
    # db.update_one({'phone': phone}, {'$push': {'messages': "{'role': 'user', 'content': '" + message.text + "'}"}})
    mode_bot = ['gtp-3.5-turbo'] * 4
    response = openai.ChatCompletion.create(
            model = mode_bot[mode],
            # messages = dict_user['messages'],
            messages = db.find_one({'phone': phone}, {'messages': 1, '_id': 0})['messages'],
            temperature = 0.5,
            max_tokens = 1000,
            top_p = 1.0,
            frequency_penalty = 0.5, 
            presence_penalty = 0.0,
    )
    if response and response.choices:
        reply = response.choices[0]['message']['content']
        dict_user['messages'].append({'role': 'assistant', 'content': reply})
        db.update_one({'phone': phone}, {'$push': {'messages': {'role': 'assistant', 'content': reply }}})
        # db.update_one({'phone': phone}, {'$push': {'messages': "{'role': 'assistant', 'content': '" + message.text + "'}"}})
    else:
        reply = 'Что-то не так'
    bot.send_message(chat_id = message.from_user.id, text = reply)
    # print(dict_user)

bot.polling()
