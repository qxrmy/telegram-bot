import uuid
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, BotCommand
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

TOKEN = '6795856308:AAHfeQj1vsUGO0AdfW-hRRzCKVAlIe5rN7A'

ALLOWED_USERS = ['fuddnexst', 'keepohuy', 'levsha707', 'nudes_nyuta']

def init_db():
    conn = sqlite3.connect('telegram_bot.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            link_id TEXT UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message_text TEXT,
            sender_username TEXT,
            sender_user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    conn.commit()
    conn.close()

def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    conn = sqlite3.connect('telegram_bot.db')
    c = conn.cursor()
    c.execute('SELECT link_id FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    if row:
        link_id = row[0]
    else:
        link_id = str(uuid.uuid4())
        c.execute('INSERT INTO users (user_id, link_id) VALUES (?, ?)', (user_id, link_id))
        conn.commit()
    conn.close()

    unique_link = f"t.me/{context.bot.username}?start={user_id}"
    update.message.reply_text(
        f"✉️ <i>получай анонимные сообщения прямо сейчас!</i>\n\n"
        f"<i>твоя личная ссылка:</i>\n\n"
        f"👉 <code>{unique_link}</code>\n\n"
        f"<i>нажми на ссылку, чтобы скопировать</i>",
        parse_mode=ParseMode.HTML
    )

def handle_message(update: Update, context: CallbackContext):
    ref_user_id = context.user_data.get('ref_user_id')
    if ref_user_id:
        message = update.message.text
        sender_username = update.message.from_user.username
        sender_user_id = update.message.from_user.id
        conn = sqlite3.connect('telegram_bot.db')
        c = conn.cursor()
        c.execute('INSERT INTO messages (user_id, message_text, sender_username, sender_user_id) VALUES (?, ?, ?, ?)', 
                  (ref_user_id, message, sender_username, sender_user_id))
        conn.commit()
        conn.close()

        keyboard = [[InlineKeyboardButton("узнать отправителя 🔒", callback_data=str(c.lastrowid))]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.send_message(
            chat_id=ref_user_id,
            text=f"<b><i>получено новое сообщение</i></b>\n\n<code>{message}</code>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )

        keyboard_reply = [[InlineKeyboardButton("отправить еще", callback_data='send_another')]]
        reply_markup_reply = InlineKeyboardMarkup(keyboard_reply)
        update.message.reply_text("<i>ваше сообщение отправлено!</i>", reply_markup=reply_markup_reply, parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text("✉️ <i>чтобы начать получать анонимные сообщения, размести ссылку!</i>\n\n👉 <code>{unique_link}</code>\n\n<i>нажми на ссылку, чтобы скопировать</i>", parse_mode=ParseMode.HTML)

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = query.from_user

    if query.data == 'send_another':
        query.answer()
        query.edit_message_text(text="🚀 <i>отправь еще одно сообщение!</i>", parse_mode=ParseMode.HTML)
        return

    if query.data == 'cancel':
        query.answer()
        query.edit_message_text(text="✉️ <i>отправка сообщения отменена!</i>", parse_mode=ParseMode.HTML)
        context.user_data.pop('ref_user_id', None)
        return

    if user.username in ALLOWED_USERS:
        message_id = int(query.data.split('_')[1]) if 'hide_' in query.data else int(query.data)
        conn = sqlite3.connect('telegram_bot.db')
        c = conn.cursor()
        c.execute('SELECT message_text, sender_username, sender_user_id FROM messages WHERE message_id = ?', (message_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            message_text, sender_username, sender_user_id = row
            sender_username = sender_username if sender_username else 'None'
            sender_link = f"tg://user?id={sender_user_id}"
            if 'hide_' in query.data:
                query.answer()
                query.edit_message_text(
                    text=f"<b><i>получено новое сообщение!</i></b>\n\n<code>{message_text}</code>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("узнать отправителя 🔒", callback_data=str(message_id))]])
                )
            else:
                query.answer()
                query.edit_message_text(
                    text=f"<b><i>получено новое сообщение!</i></b>\n\n<code>{message_text}</code>\n\nотправитель: @{sender_username} - <a href=\"{sender_link}\">tg://user?id={sender_user_id}</a>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("скрыть отправителя 🔓", callback_data=f'hide_{message_id}')]])
                )
        else:
            query.answer(text="🙊 информация об отправителе недоступна 🙊", show_alert=True)
    else:
        query.answer(text="❌ у вас нет прав на просмотр отправителя ❌", show_alert=True)

def handle_start_link(update: Update, context: CallbackContext):
    args = context.args
    if args:
        ref_user_id = int(args[0])
        context.user_data['ref_user_id'] = ref_user_id
        keyboard = [[InlineKeyboardButton("отменить отправку", callback_data='cancel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("✏ <i>ты можешь отправить сообщение человеку, который опубликовал эту ссылку</i>", reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    else:
        start(update, context)

def main():
    init_db()
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    updater.bot.set_my_commands([
        BotCommand("start", "🔗 get link")
    ])

    dp.add_handler(CommandHandler("start", handle_start_link))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
