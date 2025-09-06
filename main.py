import telebot
from telebot import types
import openpyxl
import os

# Tokenni Railway environment variables dan oladi
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

# Kanal username (faqat @ bilan)
CHANNEL_USERNAME = "@Xamidjonov_Xusniddin"

# Excel fayl nomi
EXCEL_FILE = "registratsiya.xlsx"

# Excel fayl yo‘q bo‘lsa, yaratamiz
if not os.path.exists(EXCEL_FILE):
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Qatnashuvchilar"
    sheet.append(["Ism", "Familiya", "Sinf", "Telefon"])
    wb.save(EXCEL_FILE)

user_data = {}

# Obuna bo‘lganligini tekshirish
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print("is_subscribed xatosi:", e)
        return False

# START komandasi
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = {}

    if is_subscribed(user_id):
        bot.send_message(user_id, "Assalomu alaykum! Ro'yxatdan o‘tishni boshlaymiz.\nIsmingizni yozing:")
        bot.register_next_step_handler(message, get_name)
    else:
        markup = types.InlineKeyboardMarkup()
        join_button = types.InlineKeyboardButton("📢 Kanalga qo‘shilish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
        check_button = types.InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")
        markup.add(join_button)
        markup.add(check_button)
        bot.send_message(user_id, "Avval kanalga obuna bo‘ling 👇", reply_markup=markup)

# Obunani tekshirish tugmasi
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    user_id = call.from_user.id
    if is_subscribed(user_id):
        bot.edit_message_text("✅ Obuna tasdiqlandi! Endi ro‘yxatdan o‘tamiz.\nIsmingizni yozing:",
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, get_name)
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali obuna bo‘lmadingiz!")

# Ism
def get_name(message):
    chat_id = message.from_user.id
    if message.text.startswith("/"):
        bot.send_message(chat_id, "❌ Iltimos, ismingizni yozing:")
        bot.register_next_step_handler(message, get_name)
        return
    user_data[chat_id]["ism"] = message.text
    bot.send_message(chat_id, "Familiyangizni yozing:")
    bot.register_next_step_handler(message, get_surname)

# Familiya
def get_surname(message):
    chat_id = message.from_user.id
    if message.text.startswith("/"):
        bot.send_message(chat_id, "❌ Iltimos, familiyangizni yozing:")
        bot.register_next_step_handler(message, get_surname)
        return
    user_data[chat_id]["familiya"] = message.text
    bot.send_message(chat_id, "Nechanchi sinfda o‘qiysiz?")
    bot.register_next_step_handler(message, get_class)

# Sinf
def get_class(message):
    chat_id = message.from_user.id
    if message.text.startswith("/"):
        bot.send_message(chat_id, "❌ Iltimos, sinfingizni yozing:")
        bot.register_next_step_handler(message, get_class)
        return
    user_data[chat_id]["sinf"] = message.text
    bot.send_message(chat_id, "Telefon raqamingizni yozing:")
    bot.register_next_step_handler(message, get_phone)

# Telefon
def get_phone(message):
    chat_id = message.from_user.id
    if message.text.startswith("/"):
        bot.send_message(chat_id, "❌ Iltimos, telefon raqamingizni yozing:")
        bot.register_next_step_handler(message, get_phone)
        return
    user_data[chat_id]["telefon"] = message.text

    # Excelga yozish
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

# Faqat admin Excel faylni ola oladi
ADMIN_ID = 1302280468

@bot.message_handler(commands=['getfile'])
def send_file(message):
    if message.from_user.id == ADMIN_ID:
        with open(EXCEL_FILE, "rb") as f:
            bot.send_document(message.chat.id, f)
    else:
        bot.send_message(message.chat.id, "❌ Sizda ruxsat yo‘q.")

print("Bot ishlayapti...")
bot.infinity_polling()
