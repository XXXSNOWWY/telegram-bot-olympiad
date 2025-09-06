import os
import telebot
import openpyxl

# TOKEN endi Railway Variables’dan olinadi
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

CHANNEL_USERNAME = "https://t.me/Mingbulak_SPC"  # kanal username

# Excel fayl nomi
EXCEL_FILE = "registratsiya.xlsx"

# Agar fayl mavjud bo'lmasa, yangisini yaratamiz
if not os.path.exists(EXCEL_FILE):
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Qatnashuvchilar"
    sheet.append(["Ism", "Familiya", "Sinf", "Telefon"])  # ustun nomlari
    wb.save(EXCEL_FILE)

user_data = {}

# Foydalanuvchi kanalga azo bo'lganini tekshirish
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_data[user_id] = {}
    if is_subscribed(user_id):
        bot.send_message(user_id, "Assalomu alaykum! Ro'yxatdan o‘tishni boshlaymiz.\nIsmingizni yozing:")
        bot.register_next_step_handler(message, get_name)
    else:
        bot.send_message(user_id, f"Avval {CHANNEL_USERNAME} kanaliga obuna bo‘ling va /start ni qayta yuboring.")

def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]["ism"] = message.text
    bot.send_message(chat_id, "Familiyangizni yozing:")
    bot.register_next_step_handler(message, get_surname)

def get_surname(message):
    chat_id = message.chat.id
    user_data[chat_id]["familiya"] = message.text
    bot.send_message(chat_id, "Nechanchi sinfda o‘qiysiz?")
    bot.register_next_step_handler(message, get_class)

def get_class(message):
    chat_id = message.chat.id
    user_data[chat_id]["sinf"] = message.text
    bot.send_message(chat_id, "Telefon raqamingizni yozing:")
    bot.register_next_step_handler(message, get_phone)

def get_phone(message):
    chat_id = message.chat.id
    user_data[chat_id]["telefon"] = message.text

    # Excel faylga yozish
    wb = openpyxl.load_workbook(EXCEL_FILE)
    sheet = wb.active
    sheet.append([
        user_data[chat_id]["ism"],
        user_data[chat_id]["familiya"],
        user_data[chat_id]["sinf"],
        user_data[chat_id]["telefon"]
    ])
    wb.save(EXCEL_FILE)

    bot.send_message(chat_id, "✅ Siz muvaffaqiyatli ro'yxatdan o'tdingiz! Imtihon vaqti haqida keyinroq xabar beramiz.")

# Admin Excel faylni yuklab olishi uchun
ADMIN_ID = 1302280468   # bu yerga o'zingizning Telegram ID raqamingizni yozing

@bot.message_handler(commands=['getfile'])
def send_file(message):
    if message.chat.id == ADMIN_ID:   # faqat admin ko'ra oladi
        with open(EXCEL_FILE, "rb") as f:
            bot.send_document(message.chat.id, f)
    else:
        bot.send_message(message.chat.id, "❌ Sizda ruxsat yo‘q.")

print("Bot ishga tushdi (Railway)...")
bot.polling(none_stop=True)

