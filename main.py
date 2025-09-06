import telebot
from telebot import types
import openpyxl
import os
import re

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

CHANNEL_USERNAME = "@Xamidjonov_Xusniddin"
EXCEL_FILE = "registratsiya.xlsx"
ADMIN_ID = 1302280468

# Excel fayl bo‘lmasa, yaratamiz
if not os.path.exists(EXCEL_FILE):
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Qatnashuvchilar"
    sheet.append(["Ism", "Familiya", "Sinf", "Telefon"])
    wb.save(EXCEL_FILE)

user_data = {}

# Obuna tekshirish
def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print("is_subscribed xatosi:", e)
        return False

# Validatsiya (ism/familiya)
def valid_name(text):
    return bool(re.match(r"^[A-Z][a-zA-Z'\- ]+$", text))

# START komandasi
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    if user_id == ADMIN_ID:
        # Admin uchun ro‘yxat ko‘rsatish
        if not os.path.exists(EXCEL_FILE):
            bot.send_message(user_id, "📂 Hali hech kim ro‘yxatdan o‘tmagan.")
            return

        wb = openpyxl.load_workbook(EXCEL_FILE)
        sheet = wb.active
        rows = list(sheet.iter_rows(values_only=True))[1:]

        if not rows:
            bot.send_message(user_id, "📂 Hali hech kim ro‘yxatdan o‘tmagan.")
        else:
            matn = "📋 *Ro‘yxatdan o‘tganlar:*\n\n"
            for idx, row in enumerate(rows, start=1):
                ism, familiya, sinf, tel = row
                matn += f"{idx}. {ism} {familiya}, {sinf}-sinf, 📞 {tel}\n"
            bot.send_message(user_id, matn, parse_mode="Markdown")

        with open(EXCEL_FILE, "rb") as f:
            bot.send_document(user_id, f)

    else:
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
    if not valid_name(message.text):
        bot.send_message(chat_id, "❌ Ism faqat lotin harflarida va bosh harf bilan yozilishi kerak.\nQaytadan kiriting:")
        bot.register_next_step_handler(message, get_name)
        return
    user_data[chat_id]["ism"] = message.text
    bot.send_message(chat_id, "Familiyangizni yozing:")
    bot.register_next_step_handler(message, get_surname)

# Familiya
def get_surname(message):
    chat_id = message.from_user.id
    if not valid_name(message.text):
        bot.send_message(chat_id, "❌ Familiya faqat lotin harflarida va bosh harf bilan yozilishi kerak.\nQaytadan kiriting:")
        bot.register_next_step_handler(message, get_surname)
        return
    user_data[chat_id]["familiya"] = message.text

    # 1–11 sinf tugmalari
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    rows = [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"], ["10", "11"]]
    for row in rows:
        markup.add(*[types.KeyboardButton(num) for num in row])

    bot.send_message(chat_id, "Nechanchi sinfda o‘qiysiz?", reply_markup=markup)
    bot.register_next_step_handler(message, get_class)

# Sinf
def get_class(message):
    chat_id = message.from_user.id
    text = message.text.strip()

    if not text.isdigit() or not (1 <= int(text) <= 11):
        bot.send_message(chat_id, "❌ Sinfni faqat 1 dan 11 gacha tanlang.")
        return get_surname(message)

    user_data[chat_id]["sinf"] = text

    # Telefon tugmasi
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn1 = types.KeyboardButton("📱 Raqamni yuborish", request_contact=True)
    markup.add(btn1)
    bot.send_message(chat_id, "Telefon raqamingizni yuboring:", reply_markup=markup)
    bot.register_next_step_handler(message, get_phone)

# Telefon
def get_phone(message):
    chat_id = message.from_user.id

    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text.strip()
        if not re.match(r"^\+?\d{9,15}$", phone):
            bot.send_message(chat_id, "❌ Telefon raqam noto‘g‘ri formatda. +998901234567 ko‘rinishida yuboring:")
            bot.register_next_step_handler(message, get_phone)
            return

    user_data[chat_id]["telefon"] = phone

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

    bot.send_message(chat_id, "✅ Siz muvaffaqiyatli ro'yxatdan o'tdingiz!", reply_markup=types.ReplyKeyboardRemove())

# Admin uchun fayl
@bot.message_handler(commands=['getfile'])
def send_file(message):
    if message.from_user.id == ADMIN_ID:
        with open(EXCEL_FILE, "rb") as f:
            bot.send_document(message.chat.id, f)
    else:
        bot.send_message(message.chat.id, "❌ Sizda ruxsat yo‘q.")

print("Bot ishlayapti...")
bot.infinity_polling()
