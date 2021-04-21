import os
import re
from telegram.chatmember import ChatMember
from telegram.ext import Updater, CommandHandler,  CallbackContext, MessageHandler, MessageFilter, Filters
from telegram.update import Update, Message
import psycopg2
from pony.orm import *
from typing import List, Union

save_command_pattern = re.compile(r'^!save (\w+)$')
faq_pattern = re.compile(r'^#(\w+)$')

DATABASE_URL = os.environ['DATABASE_URL']
PORT = os.environ.get('PORT')
TOKEN = os.environ.get('TOKEN')
CREATOR_UID=os.environ.get('CREATOR_UID')

user,password,host,port,db_name = re.match('postgres://(.*):(.*)@(.*):(.*)/(.*)', DATABASE_URL).groups()
db = Database(
    provider='postgres',
    user=user,
    password=password,
    host=host,
    port=port,
    database=db_name
    )

class FAQ(db.Entity):
    keyword = Required(str)
    message = Required(str)
    group = Required('Group')
    PrimaryKey(keyword,group)

class Group(db.Entity):
    id=PrimaryKey(int)
    admins=Set('Admin', reverse='groups')
    faqs=Set(FAQ, reverse='group')

class Admin(db.Entity):
    id=PrimaryKey(int)
    groups=Set(Group, reverse='admins')

db.generate_mapping(create_tables=True)


updater = Updater(TOKEN)

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me! {}".format(update.message.from_user.id))

def added_to_group(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    adminMembers = update.effective_chat.get_administrators()
    adminMembers[0].user.id
    with db_session:
        group: Group = Group.get(id=chat_id) or Group(id=chat_id)
        admins: List[Admin] = [Admin.get(id=member.user.id) or Admin(id=member.user.id)
                     for member in adminMembers]
        for admin in admins:
            admin.groups += group
        group.admins=admins

    context.bot.send_message(chat_id=update.effective_chat.id, text="Hello creator")

def save_faq(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    sender_id = update.effective_user.id

    keyword, = re.match(save_command_pattern, update.effective_message.text).groups()
    message = update.effective_message.reply_to_message.text

    with db_session:
        group: Union[Group,None] = Group.get(id=chat_id)
        if group is None:
            return
        if not Admin.exists(lambda admin: admin in group.admins):
            return
        faq = FAQ.get(keyword=keyword,group=group) or FAQ(keyword=keyword, group=group,message=message)
        faq.message = message
    update.effective_message.reply_text(text='saved!')

def get_faq(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    keyword, = faq_pattern.match(update.effective_message.text).groups()
    reply_to_message = update.effective_message.reply_to_message
    with db_session:
        group = Group.get(id=chat_id)
        if group is None:
            return
        faq: Union[FAQ,None] = FAQ.get(keyword=keyword,group=group)
    if faq is not None:
        if reply_to_message is not None:
            reply_to_message.reply_text(text=faq.message)
        else:
            context.bot.send_message(chat_id=chat_id ,text=faq.message)
    else:
        print(faq,flush=True)

def reload_admins(update: Update, context: CallbackContext):
    chat_id=update.effective_chat.id
    adminMembers=update.effective_chat.get_administrators()
    with db_session:
        group:Union[Group,None]=Group.get(id=chat_id)
        if group is None:
            return
        admins=[Admin.get(id=member.user.id) or Admin(id=member.user.id)
         for member in adminMembers]
        for admin in admins:
            admin.groups+=group
        group.admins=admins
    context.bot.send_message(chat_id=chat_id, text='reloaded!')

class _MyJoinMessage(MessageFilter):
    name = 'my_join_message_filter'

    def __init__(self, username):
        self.username = username

    def filter(self, message: Message) -> bool:
        return any(user.username == self.username for user in message.new_chat_members)

my_join_message_filter = _MyJoinMessage(updater.bot.username)

updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(MessageHandler(Filters.user(int(CREATOR_UID)) and my_join_message_filter, added_to_group))
updater.dispatcher.add_handler(MessageHandler(Filters.chat_type.group and Filters.reply and Filters.regex(save_command_pattern), save_faq))
updater.dispatcher.add_handler(MessageHandler(Filters.chat_type.group and Filters.regex(faq_pattern), get_faq))
updater.dispatcher.add_handler(MessageHandler(Filters.chat_type.group and Filters.regex('!reload_admins'), reload_admins))


updater.start_webhook(listen="0.0.0.0",
                       port=PORT,
                       url_path='wh')

updater.idle()
