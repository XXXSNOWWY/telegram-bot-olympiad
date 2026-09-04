import os
import re
import openpyxl
import telebot
from telebot import types

# Token (Environment Variable)
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

# Kanallar ro'yxati (Username va taklif havolalari)
# Ikkinchi kanal nomini o'zingiznikiga o'zgartiring!
CHANNELS = [
    {"username": "@MATEMATIKA_Mingbuloq", "link": "https://t.me/MATEMATIKA_Mingbuloq"},
]

ADMIN_ID = 1302280468
EXCEL_FILE = "registratsiya.xlsx"
waiting_for_broadcast = False
user_data = {}

# Excel fayl yo‘q bo‘lsa, yaratamiz
if not os.path.exists(EXCEL_FILE):
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "Qatnashuvchilar"
    sheet.append(["Ism", "Familiya", "Sinf", "Telefon", "Telegram ID"])
    wb.save(EXCEL_FILE)

# Barcha kanallarga obunani tekshirish
def is_subscribed_all(user_id):
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch["username"], user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            print(f"{ch['username']} obuna tekshirishda xato:", e)
            return False
    return True

# START komandasi
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    if user_id == ADMIN_ID:
        send_registered_users(message)
        return

    user_data[user_id] = {}

    if is_subscribed_all(user_id):
        bot.send_message(user_id, "Assalomu alaykum! Ro'yxatdan o‘tishni boshlaymiz.\nIsmingizni yozing:")
        bot.register_next_step_handler(message, get_name)
    else:
        markup = types.InlineKeyboardMarkup()
        for i, ch in enumerate(CHANNELS, start=1):
            btn = types.InlineKeyboardButton(f"📢 {i}-kanalga qo‘shilish", url=ch["link"])
            markup.add(btn)
        
        check_button = types.InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")
        markup.add(check_button)
        bot.send_message(user_id, "Ro'yxatdan o'tish uchun quyidagi kanallarga obuna bo‘ling 👇", reply_markup=markup)

# Obunani tekshirish tugmasi
@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    user_id = call.from_user.id
    if is_subscribed_all(user_id):
        user_data[user_id] = {}
        bot.edit_message_text("✅ Obuna tasdiqlandi! Endi ro‘yxatdan o‘tamiz.\nIsmingizni yozing:",
                              chat_id=call.message.chat.id,
                              message_id=call.message.message_id)
        bot.register_next_step_handler(call.message, get_name)
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali barcha kanallarga obuna bo‘lmadingiz!", show_alert=True)

# Ism
def get_name(message):
    chat_id = message.from_user.id
    text = message.text.strip() if message.text else ""

    if not re.match(r'^[A-ZА-ЯЁO‘G‘a-zа-яёo‘g‘\'\- ]+$', text):
        bot.send_message(chat_id, "❌ Ism noto'g'ri kiritildi. Qaytadan kiriting:")
        bot.register_next_step_handler(message, get_name)
        return

    if chat_id not in user_data:
        user_data[chat_id] = {}

    user_data[chat_id]["ism"] = text
    bot.send_message(chat_id, "Familiyangizni yozing:")
    bot.register_next_step_handler(message, get_surname)

# Familiya
def get_surname(message):
    chat_id = message.from_user.id
    text = message.text.strip() if message.text else ""

    if not re.match(r'^[A-ZА-ЯЁO‘G‘a-zа-яёo‘g‘\'\- ]+$', text):
        bot.send_message(chat_id, "❌ Familiya noto'g'ri kiritildi. Qaytadan kiriting:")
        bot.register_next_step_handler(message, get_surname)
        return

    user_data[chat_id]["familiya"] = text

    # 1-11 sinflar uchun tugmalar
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row("1", "2", "3")
    markup.row("4", "5", "6")
    markup.row("7", "8", "9")
    markup.row("10", "11")
    
    bot.send_message(chat_id, "Nechanchi sinfda o‘qiysiz?", reply_markup=markup)
    bot.register_next_step_handler(message, get_class)

# Sinf
def get_class(message):
    chat_id = message.from_user.id
    text = message.text.strip() if message.text else ""

    if not text.isdigit() or not (1 <= int(text) <= 11):
        bot.send_message(chat_id, "❌ Iltimos, sinfni tugmalardan tanlang yoki 1 dan 11 gacha raqam kiriting:")
        bot.register_next_step_handler(message, get_class)
        return

    user_data[chat_id]["sinf"] = text

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    btn1 = types.KeyboardButton("📱 Raqamni yuborish", request_contact=True)
    markup.add(btn1)
    bot.send_message(chat_id, "Telefon raqamingizni yuborish uchun pastdagi tugmani bosing:", reply_markup=markup)

# Telefon (kontakt orqali)
@bot.message_handler(content_types=['contact'])
def get_contact(message):
    chat_id = message.from_user.id

    if message.contact is not None:
        phone = message.contact.phone_number.strip()
        phone_clean = re.sub(r'\D', '', phone)

        user_data[chat_id]["telefon"] = "+" + phone_clean
        save_to_excel(chat_id)
        bot.send_message(chat_id, "✅ Siz muvaffaqiyatli ro'yxatdan o'tdingiz!", reply_markup=types.ReplyKeyboardRemove())

# Excelga yozish
def save_to_excel(chat_id):
    try:
        wb = openpyxl.load_workbook(EXCEL_FILE)
        sheet = wb.active
        sheet.append([
            user_data[chat_id].get("ism", ""),
            user_data[chat_id].get("familiya", ""),
            user_data[chat_id].get("sinf", ""),
            user_data[chat_id].get("telefon", ""),
            chat_id
        ])
        wb.save(EXCEL_FILE)
    except Exception as e:
        print("Excel yozishda xato:", e)

# Admin /sendall buyrug'i
@bot.message_handler(commands=['sendall'])
def send_all_command(message):
    global waiting_for_broadcast
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "✍️ Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:")
        waiting_for_broadcast = True
    else:
        bot.send_message(message.chat.id, "❌ Sizda ruxsat yo‘q.")

# Admin Excel faylni olish
@bot.message_handler(commands=['getfile'])
def send_file(message):
    if message.from_user.id == ADMIN_ID:
        if os.path.exists(EXCEL_FILE):
            with open(EXCEL_FILE, "rb") as f:
                bot.send_document(message.chat.id, f)
        else:
            bot.send_message(message.chat.id, "❌ Excel fayl topilmadi.")
    else:
        bot.send_message(message.chat.id, "❌ Sizda ruxsat yo‘q.")

# Admin ro'yxatni ko'rishi
def send_registered_users(message):
    if os.path.exists(EXCEL_FILE):
        wb = openpyxl.load_workbook(EXCEL_FILE)
        sheet = wb.active

        users = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row[0]:
                users.append(f"{row[0]} {row[1]}, {row[2]}-sinf, 📱 {row[3]}")

        if users:
            text = "\n".join(users)
            if len(text) > 4000:
                text = text[:4000] + "\n..."
            bot.send_message(message.chat.id, f"📋 Ro'yxatdan o'tganlar:\n\n{text}")
        else:
            bot.send_message(message.chat.id, "❌ Hali hech kim ro'yxatdan o'tmagan.")

        with open(EXCEL_FILE, "rb") as f:
            bot.send_document(message.chat.id, f)

# Xabarlarni tarqatish (Broadcast)
@bot.message_handler(func=lambda msg: waiting_for_broadcast and msg.from_user.id == ADMIN_ID)
def handle_broadcast(message):
    global waiting_for_broadcast
    broadcast_message = message.text

    if not os.path.exists(EXCEL_FILE):
        bot.send_message(message.chat.id, "❌ Foydalanuvchilar bazasi topilmadi.")
        waiting_for_broadcast = False
        return

    wb = openpyxl.load_workbook(EXCEL_FILE)
    sheet = wb.active

    count = 0
    for row in sheet.iter_rows(min_row=2, values_only=True):
        user_id = row[4]
        if user_id:
            try:
                bot.send_message(user_id, broadcast_message)
                count += 1
            except Exception as e:
                print(f"{user_id} ga xabar yuborilmadi:", e)

    bot.send_message(message.chat.id, f"✅ Xabar {count} ta foydalanuvchiga yuborildi.")
    waiting_for_broadcast = False

print("Bot ishlayapti...")
bot.infinity_polling()
