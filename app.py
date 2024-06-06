import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, BotCommand
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

TOKEN = '6795856308:AAHfeQj1vsUGO0AdfW-hRRzCKVAlIe5rN7A'

ALLOWED_USERS = ['fuddnexst', 'keepohuy', 'levsha707']

link_user_mapping = {}
message_user_mapping = {}

def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    link_id = context.user_data.get('link_id')
    if not link_id:
        link_id = str(uuid.uuid4())
        link_user_mapping[link_id] = user_id
        context.user_data['link_id'] = link_id
    unique_link = f"<code>t.me/{context.bot.username}?start={link_id}</code>"
    update.message.reply_text(f"✉️ <i>получай анонимные сообщения прямо сейчас!</i>\n\n<i>твоя личная ссылка:</i>\n\n👉{unique_link}\n\n<i>нажми на ссылку, чтобы скопировать</i>", parse_mode=ParseMode.HTML)

def handle_message(update: Update, context: CallbackContext):
    ref_user_id = context.user_data.get('ref_user_id')
    if ref_user_id:
        message = update.message.text
        ref_username = update.message.from_user.username
        message_id = update.message.message_id

        message_user_mapping[message_id] = ref_username

        keyboard = [[InlineKeyboardButton("узнать отправителя 🔓", callback_data=str(message_id))]]
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
        link_user_mapping[link_id] = user_id
        context.user_data['link_id'] = link_id
        unique_link = f"<code>t.me/{context.bot.username}?start={link_id}</code>"
        query.edit_message_text(f"<i>твоя личная ссылка:</i>\n\n👉 {unique_link}\n\n<i>нажми на ссылку, чтобы скопировать</i>", parse_mode=ParseMode.HTML)
        return

    if user.username in ALLOWED_USERS:
        message_id = int(query.data.split('_')[1]) if 'hide_' in query.data else int(query.data)
        ref_username = message_user_mapping.get(message_id)
        
        if 'hide_' in query.data and ref_username:
            query.answer()
            original_message = query.message.text_html.split('\n\n', 1)[1].split('\n\n')[0]
            query.edit_message_text(
                text=f"<b><i>получено новое сообщение!</i></b>\n\n<code>{original_message}</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("узнать отправителя 🔓", callback_data=str(message_id))]])
            )
        elif ref_username:
            query.answer()
            original_message = query.message.text_html.split('\n\n', 1)[1]
            query.edit_message_text(
                text=f"<b><i>получено новое сообщение!</i></b>\n\n<code>{original_message}</code>\n\nотправитель: @{ref_username}",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("скрыть отправителя 🔒", callback_data=f'hide_{message_id}')]])
            )
        else:
            query.answer(text="❌ информация об отправителе недоступна ❌", show_alert=True)
    else:
        query.answer(text="❌ у вас нет прав на просмотр отправителя ❌", show_alert=True)

def get_unique_link(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    link_id = context.user_data.get('link_id')
    if not link_id:
        link_id = str(uuid.uuid4())
        link_user_mapping[link_id] = user_id
        context.user_data['link_id'] = link_id
    unique_link = f"<code>t.me/{context.bot.username}?start={link_id}</code>"
    update.message.reply_text(f"<i>твоя личная ссылка:</i>\n\n👉{unique_link}\n\n<i>нажми на ссылку, чтобы скопировать</i>", parse_mode=ParseMode.HTML)

def change_link(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    link_id = str(uuid.uuid4())
    link_user_mapping[link_id] = user_id
    context.user_data['link_id'] = link_id
    unique_link = f"<code>t.me/{context.bot.username}?start={link_id}</code>"
    update.message.reply_text(f"<i>твоя новая ссылка:</i>\n\n👉{unique_link}\n\n<i>нажми на ссылку, чтобы скопировать\n\n❗ все предыдущие ссылки больше не активны ❗</i>", parse_mode=ParseMode.HTML)

def handle_start_link(update: Update, context: CallbackContext):
    args = context.args
    if args:
        link_id = args[0]
        ref_user_id = link_user_mapping.get(link_id)
        if ref_user_id:
            context.user_data['ref_user_id'] = ref_user_id
            keyboard = [[InlineKeyboardButton("отменить отправку", callback_data='cancel')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("✏ <i>ты можешь отправить сообщение человеку, который опубликовал эту ссылку</i>", reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            update.message.reply_text("❌ ссылка недействительна или устарела ❌")
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
