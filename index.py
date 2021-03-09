import os
from telegram.ext import Updater, CommandHandler,  CallbackContext, MessageHandler, MessageFilter, Filters
from telegram.update import Update, Message

PORT = os.environ.get('PORT')
TOKEN = os.environ.get('TOKEN')
CREATOR_UID=os.environ.get('CREATOR_UID')
updater = Updater(TOKEN)

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me! {}".format(update.message.from_user.id))

def creator_message(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello creator")

class _MyJoinMessage(MessageFilter):
    name = 'my_join_message_filter'

    def __init__(self, username):
        self.username = username

    def filter(self, message: Message) -> bool:
        any(user.username == self.username for user in message.new_chat_members)

my_join_message_filter = _MyJoinMessage(updater.bot.username)

updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(MessageHandler(Filters.user(int(CREATOR_UID)) and my_join_message_filter, creator_message))

updater.start_webhook(listen="0.0.0.0",
                      port=PORT,
                      url_path='wh')

updater.idle()