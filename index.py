import os
import telegram
from telegram.ext import Updater, CommandHandler, CallbackContext

PORT = os.environ.PORT
TOKEN = os.environ.TOKEN
updater = Updater(TOKEN)

def start(update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

updater.dispatcher.add_handler(CommandHandler('start', start))

updater.start_webhook(listen="0.0.0.0",
                      port=PORT,
                      url_path='wh')

updater.idle()
