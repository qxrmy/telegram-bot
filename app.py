import sqlite3
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, BotCommand
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

TOKEN = '6795856308:AAHfeQj1vsUGO0AdfW-hRRzCKVAlIe5rN7A'

# Connect to SQLite database
conn = sqlite3.connect('telegram_bot.db')
cursor = conn.cursor()

# Create tables if not exists
cursor.execute('''CREATE TABLE IF NOT EXISTS links (
                    link_id TEXT PRIMARY KEY,
                    user_id INTEGER
                )''')

cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY,
                    ref_user_id INTEGER,
                    message_text TEXT
                )''')

conn.commit()

ALLOWED_USERS = ['fuddnexst', 'keepohuy', 'levsha707']

def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    link_id = context.user_data.get('link_id')
    if not link_id:
        link_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO links (link_id, user_id) VALUES (?, ?)", (link_id, user_id))
        context.user_data['link_id'] = link_id
        conn.commit()
    unique_link = f"<code>t.me/{context.bot.username}?start={link_id}</code>"
    update.message.reply_text(f"✉️ <i>получай анонимные сообщения прямо сейчас!</i>\n\n<i>твоя личная ссылка:</i>\n\n👉{unique_link}\n\n<i>нажми на ссылку, чтобы скопировать</i>", parse_mode=ParseMode.HTML)

def handle_message(update: Update, context: CallbackContext):
    ref_user_id = context.user_data.get('ref_user_id')
    if ref_user_id:
        message = update.message.text
        ref_user_id = update.message.from_user.id
        cursor.execute("INSERT INTO messages (ref_user_id, message_text) VALUES (?, ?)", (ref_user_id, message))
        conn.commit()

        keyboard = [[InlineKeyboardButton("узнать отправителя 🔓", callback_data=str(cursor.lastrowid))]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.send_message(chat_id=ref_user_id, text=f"<b><i>получено новое сообщение</i></b>\n\n<code>{message}</code>", reply_markup=reply_markup, parse_mode=ParseMode.HTML)

        keyboard_reply = [[InlineKeyboardButton("отправить еще", callback_data='send_another')]]
        reply_markup_reply = InlineKeyboardMarkup(keyboard_reply)
        update.message.reply_text("<i>ваше сообщение отправлено!</i>", reply_markup=reply_markup_reply, parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text("✉️ <i>чтобы начать получать анонимные сообщения, размести ссылку!</i>")

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user

    if query.data == 'send_another':
        query.answer()
        query.edit_message_text(text="🚀 <i>отправь еще одно сообщение!</i>", parse_mode=ParseMode.HTML)
        return

    if query.data == 'cancel':
        query.answer()
        user_id = query.from_user.id
        link_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO links (link_id, user_id) VALUES (?, ?)", (link_id, user_id))
        context.user_data['link_id'] = link_id
        conn.commit()
        unique_link = f"<code>t.me/{context.bot.username}?start={link_id}</code>"
        query.edit_message_text(f"<i>твоя личная ссылка:</i>\n\n👉 {unique_link}\n\n<i>нажми на ссылку, чтобы скопировать</i>", parse_mode=ParseMode.HTML)
        return

    if user.username in ALLOWED_USERS:
        message_id = int(query.data.split('_')[1]) if 'hide_' in query.data else int(query.data)
        ref_user_id = query.from_user.id

        if 'hide_' in query.data:
            query.answer()
            original_message = query.message.text_html.split('\n\n', 1)[1].split('\n\n')[0]
            query.edit_message_text(
                text=f"<b><i>получено новое сообщение!</i></b>\n\n<code>{original_message}</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("узнать отправителя 🔓", callback_data=str(message_id))]])
            )
        else:
            query.answer()
            original_message = query.message.text_html.split('\n\n', 1)[1]
            query.edit_message_text(
                text=f"<b><i>получено новое сообщение!</i></b>\n\n<code>{original_message}</code>",
                parse_mode=ParseMode.HTML
            )
            cursor.execute("SELECT ref_user_id FROM messages WHERE message_id=?", (message_id,))
            ref_user_id = cursor.fetchone()[0]
            query.message.reply_text(f"<code>Отправитель: {ref_user_id}</code>", parse_mode=ParseMode.HTML)

    else:
        query.answer(text="❌ у вас нет прав на просмотр отправителя ❌", show_alert=True)

def get_unique_link(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    link_id = context.user_data.get('link_id')
    if not link_id:
        link_id = str(uuid.uuid4())
        cursor.execute("INSERT INTO links (link_id, user_id) VALUES (?, ?)", (link_id, user_id))
        context.user_data['link_id'] = link_id
        conn.commit()
    unique_link = f"<code>t.me/{context.bot.username}?start={link_id}</code>"
    update.message.reply_text(f"<i>твоя личная ссылка:</i>\n\n👉{unique_link}\n\n<i>нажми на ссылку, чтобы скопировать</i>", parse_mode=ParseMode.HTML)

def handle_start_link(update: Update, context: CallbackContext):
    args = context.args
    if args:
        link_id = args[0]
        cursor.execute("SELECT user_id FROM links WHERE link_id=?", (link_id,))
        ref_user_id = cursor.fetchone()
        if ref_user_id:
            context.user_data['ref_user_id'] = ref_user_id[0]
            keyboard = [[InlineKeyboardButton("отменить отправку", callback_data='cancel')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("✏ <i>ты можешь отправить сообщение человеку, который опубликовал эту ссылку</i>", reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            update.message.reply_text("🙊 ссылка недействительна или устарела 🙊")
    else:
        start(update, context)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    updater.bot.set_my_commands([
        BotCommand("start", "🔗 get link"),
        BotCommand("changelink", "✏ change link")
    ])

    dp.add_handler(CommandHandler("start", handle_start_link))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(CommandHandler("getlink", get_unique_link))
    dp.add_handler(CommandHandler("changelink", change_link))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()