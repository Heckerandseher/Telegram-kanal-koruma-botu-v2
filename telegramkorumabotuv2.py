import telebot
from telebot import types
import logging
import time
import json
import os
import re

logging.basicConfig(level=logging.INFO)

# ==========================
#    TOKENİNİ BURAYA YAZ
# ==========================
TOKEN = "8408810189:AAF9ORfuHXgdCPydUFKAE0hSlxfTWwGP4pY"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

APPROVED_FILE = "approved_users.json"

# ==========================
#   JSON YÖNETİMİ
# ==========================

def load_approved():
    if os.path.exists(APPROVED_FILE):
        with open(APPROVED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_approved(data):
    with open(APPROVED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

approved_users = load_approved()

# ==========================
#   YÜZELLİK FONKS.
# ==========================

def get_user_mention(user):
    return f"@{user.username}" if user.username else f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"

def is_creator(message):
    try:
        return bot.get_chat_member(message.chat.id, message.from_user.id).status == "creator"
    except:
        return False

# ==========================
#   MENÜ
# ==========================

def main_menu_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Bilgi", callback_data="info"),
        types.InlineKeyboardButton("Yardım", callback_data="help")
    )
    markup.add(types.InlineKeyboardButton("Komutlar", callback_data="commands"))
    markup.add(types.InlineKeyboardButton("Admin Paneli", callback_data="admin"))
    markup.add(types.InlineKeyboardButton("Gruba Ekle", url=f"https://t.me/{bot.get_me().username}?startgroup=0"))
    return markup

def back_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Geri", callback_data="back"))
    return markup

# ==========================
#   START
# ==========================

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type != "private": return
    bot.send_message(
        message.chat.id,
        "<b>Merhaba! Gelişmiş Grup Koruma Botu</b>\n\n"
        "Otomatik olarak:\n"
        "• Sticker siler\n"
        "• Mesaj düzenlemeyi siler\n"
        "• Küfürleri siler\n"
        "• Linkleri engeller\n"
        "• Flood yapanı susturur\n"
        "• Medya (gif/foto/video) engeller\n"
        "• Adminlere uyarı yollar\n"
        "• Otomatik hoş geldin mesajı gönderir\n"
        "• Sadece kurucu izin verebilir\n",
        reply_markup=main_menu_markup()
    )

# ==========================
#   CALLBACK
# ==========================

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.message.chat.type != "private": return

    menu = {
        "info": "<b>Bilgi</b>\nBu bot grubu korur ve otomatik filtre uygular.",
        "help": "<b>Yardım</b>\nBotu gruba ekle ve admin yetkisi ver.",
        "commands": (
            "<b>Komutlar (Sadece Kurucu)</b>\n"
            "/approve → Yanıt verilen kişiye izin verir.\n/unapprove → İzni kaldırır.\n/approved → Onaylı kullanıcıları listeler.\n"
            "/ban → kullanıcıyı yasaklar. \n/unban → kullanıcı yasağını kaldırır.\n/mute → kullanıyı sesini kapatır.\n/unmute → kullanıcı sesini açar. \n"
        ),
        "admin": (
            "<b>Admin Paneli</b>\n"
            "• Küfür filtresi aktif\n"
            "• Link engelleme aktif\n"
            "• Flood koruması aktif\n"
            "• Medya engelleme aktif\n"
            "• Sticker/edit koruma aktif"
        )
    }

    if call.data == "back":
        return bot.edit_message_text(
            "<b>Merhaba! Gelişmiş Menü</b>",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu_markup()
        )

    bot.edit_message_text(
        menu.get(call.data, "Hata."),
        call.message.chat.id,
        call.message.message_id,
        reply_markup=back_markup()
    )

# ==========================
#   ADMİN KOMUTLARI
# ==========================

@bot.message_handler(commands=['approve','unapprove','approved','ban','unban','mute','unmute'])
def admin(message):

    if message.chat.type == "private": return
    if not is_creator(message):
        return bot.reply_to(message, "Bu komutları sadece kurucu kullanabilir.")

    chat_id = str(message.chat.id)

    # ========== APPROVE ==========
    if message.text.startswith("/approve"):
        if not message.reply_to_message:
            return bot.reply_to(message, "Bir mesaja yanıt ver.")
        user = message.reply_to_message.from_user

        approved_users.setdefault(chat_id, [])

        if user.id not in approved_users[chat_id]:
            approved_users[chat_id].append(user.id)
            save_approved(approved_users)
            return bot.reply_to(message, f"{get_user_mention(user)} artık serbest!")
        else:
            return bot.reply_to(message, "Zaten onaylı.")

    # ========== UNAPPROVE ==========
    if message.text.startswith("/unapprove"):
        if not message.reply_to_message:
            return bot.reply_to(message, "Bir mesaja yanıt ver.")
        user = message.reply_to_message.from_user

        if chat_id in approved_users and user.id in approved_users[chat_id]:
            approved_users[chat_id].remove(user.id)
            save_approved(approved_users)
            return bot.reply_to(message, "İzin kaldırıldı.")
        return bot.reply_to(message, "Bu kişi onaylı değil.")

    # ========== APPROVED ==========
    if message.text.startswith("/approved"):
        if chat_id not in approved_users:
            return bot.reply_to(message, "Onaylı kimse yok.")
        text = "<b>Onaylılar:</b>\n\n"
        for uid in approved_users[chat_id]:
            u = bot.get_chat_member(message.chat.id, uid).user
            text += f"• {get_user_mention(u)}\n"
        return bot.reply_to(message, text)

    # ========== BAN ==========
    if message.text.startswith("/ban"):
        if not message.reply_to_message:
            return bot.reply_to(message, "Yanıt vererek kullan.")
        user = message.reply_to_message.from_user
        bot.ban_chat_member(message.chat.id, user.id)
        return bot.reply_to(message, f"{get_user_mention(user)} banlandı.")

    # ========== UNBAN ==========
    if message.text.startswith("/unban"):
        if not message.reply_to_message:
            return bot.reply_to(message, "Yanıt vererek kullan.")
        user = message.reply_to_message.from_user
        bot.unban_chat_member(message.chat.id, user.id)
        return bot.reply_to(message, f"{get_user_mention(user)} unban edildi.")

    # ========== MUTE ==========
    if message.text.startswith("/mute"):
        if not message.reply_to_message:
            return bot.reply_to(message, "Yanıt vererek kullan.") 
        user = message.reply_to_message.from_user
        mute = types.ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(message.chat.id, user.id, permissions=mute)
        return bot.reply_to(message, f"{get_user_mention(user)} susturuldu.")

    # ========== UNMUTE ==========
    if message.text.startswith("/unmute"):
        if not message.reply_to_message:
            return bot.reply_to(message, "Yanıt vererek kullan.")
        user = message.reply_to_message.from_user
        perm = types.ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True
        )
        bot.restrict_chat_member(message.chat.id, user.id, permissions=perm)
        return bot.reply_to(message, f"{get_user_mention(user)} artık konuşabilir.")

# ==========================
#   MEDYA ENGELLEME
# ==========================

@bot.message_handler(content_types=['photo','video','animation','audio','document'])
def block_media(message):
    chat_id = str(message.chat.id)
    if chat_id in approved_users and message.from_user.id in approved_users[chat_id]:
        return
    delete_and_notify(message, "medya gönderdiği için")

# ==========================
#   STICKER / EDIT
# ==========================

@bot.message_handler(content_types=['sticker'])
def sticker_block(message):
    chat_id = str(message.chat.id)
    if chat_id in approved_users and message.from_user.id in approved_users[chat_id]:
        return
    delete_and_notify(message, "sticker attığı için")

@bot.edited_message_handler(func=lambda m: True)
def edit_block(message):
    chat_id = str(message.chat.id)
    if chat_id in approved_users and message.from_user.id in approved_users[chat_id]:
        return
    delete_and_notify(message, "mesaj düzenlediği için")

# ==========================
#   KÜFÜR FİLTRESİ
# ==========================

KUFUR = ["amk","aq","yarrak","orospu","piç","sik","göt","sg","siktir"]

@bot.message_handler(func=lambda m: True)
def badword_filter(message):

    chat_id = str(message.chat.id)
    if message.chat.type == "private": return
    if chat_id in approved_users and message.from_user.id in approved_users[chat_id]:
        return

    text = message.text.lower() if message.text else ""

    if any(k in text for k in KUFUR):
        delete_and_notify(message, "küfür ettiği için")

# ==========================
#   LİNK ENGELLEME
# ==========================

LINK_REGEX = r"(t\.me|https?://|www\.)"

def detect_link(text):
    return bool(re.search(LINK_REGEX, text))

@bot.message_handler(func=lambda m: True)
def link_filter(message):

    if not message.text:
        return

    chat_id = str(message.chat.id)
    if chat_id in approved_users and message.from_user.id in approved_users[chat_id]:
        return

    if detect_link(message.text):
        delete_and_notify(message, "link attığı için")

# ==========================
#   FLOOD (SPAM) KORUMA
# ==========================

user_msgs = {}

@bot.message_handler(func=lambda m: True)
def flood(message):

    if message.chat.type == "private": return

    uid = message.from_user.id
    now = time.time()

    user_msgs.setdefault(uid, [])
    user_msgs[uid] = [t for t in user_msgs[uid] if now - t < 4]  # 4 saniye içinde

    user_msgs[uid].append(now)

    chat_id = str(message.chat.id)
    if chat_id in approved_users and uid in approved_users[chat_id]:
        return

    if len(user_msgs[uid]) > 5:
        mute = types.ChatPermissions(can_send_messages=False)
        bot.restrict_chat_member(message.chat.id, uid, permissions=mute)
        delete_and_notify(message, "flood yaptığı için (mute edildi)")

# ==========================
#   MESAJ SİL + ADMİNLERE BİLDİR
# ==========================

def delete_and_notify(message, reason):
    try:
        bot.delete_message(message.chat.id, message.message_id)

        warn = (
            f"<b>Mesaj Silindi</b>\n"
            f"<b>Kullanıcı:</b> {get_user_mention(message.from_user)}\n"
            f"<b>ID:</b> <code>{message.from_user.id}</code>\n"
            f"<b>Neden:</b> {reason}\n"
            f"<b>Grup:</b> {message.chat.title}\n"
            f"<b>Zaman:</b> {time.strftime('%H:%M %d.%m.%Y')}"
        )

        for admin in bot.get_chat_administrators(message.chat.id):
            try: bot.send_message(admin.user.id, warn)
            except: pass

    except Exception as e:
        logging.error(f"Delete err: {e}")

# ==========================
#   BOT ÇALIŞTIR
# ==========================

if __name__ == "__main__":
    print("BOT ÇALIŞIYOR...")
    while True:
        try:
            bot.infinity_polling()
        except Exception as e:
            print("Hata:", e)
            time.sleep(3)
