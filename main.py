import telebot
from telebot import types
import os

# Tokeningizni Railway variables ga qo'ygan bo'lishingiz kerak
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

# ❗ Kanal username yoki ID
# Agar public kanal bo'lsa:
CHANNEL_USERNAME = "@Xamidjonov_Xusniddin"  
# Agar private kanal bo'lsa:
# CHANNEL_USERNAME = -1001234567890  

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print("is_subscribed xatosi:", e)
        return False

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if is_subscribed(user_id):
        bot.send_message(user_id, "✅ Xush kelibsiz! Siz kanalga obuna bo‘lgansiz.")
    else:
        markup = types.InlineKeyboardMarkup()
        join_btn = types.InlineKeyboardButton("📢 Kanalga qo‘shilish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}" if isinstance(CHANNEL_USERNAME, str) else None)
        check_btn = types.InlineKeyboardButton("✅ Obunani tekshirish", callback_data="check_sub")
        markup.add(join_btn)
        markup.add(check_btn)
        bot.send_message(user_id, "❗ Avval kanalga obuna bo‘ling 👇", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_subscription(call):
    user_id = call.from_user.id
    if is_subscribed(user_id):
        bot.edit_message_text("✅ Obuna tasdiqlandi!", chat_id=call.message.chat.id, message_id=call.message.message_id)
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali obuna bo‘lmadingiz!")

print("Bot ishga tushdi...")
bot.infinity_polling()
