import logging, sys, os
import sqlite3
from datetime import datetime

import requests
from typing import Final
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, Application, CallbackContext, JobQueue
from bs4 import BeautifulSoup
import RSSClass
import Enums
import feedparser
import time

BOT_VERSION: Final = 1.1

TOKEN: Final = os.environ.get('TOKEN')
BOT_USERNAME: Final = "@WallaFeederBot"
DEBUG: Final = True
logger = logging.getLogger('WallaFeederLogger')

PERMITTED_ID: Final = int(os.environ.get('PERMITTED_ID'))

def is_permitted(user_id):
    return user_id == PERMITTED_ID


# Database setup (SQLite example)
def setup_database():
    logger.info('Starting database setup')

    conn = sqlite3.connect('users.db')  # SQLite database for storing user data
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (created_at TEXT, user_id INTEGER PRIMARY KEY, full_name TEXT, username TEXT, language_code TEXT, link TEXT)''')
    conn.commit()
    conn.close()
    logger.debug('Finished database setup')


# Function to add user to the database
def add_user(user):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    logger.debug(f'Adding new user to database at {current_time}')
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO users (created_at, user_id, full_name, username, language_code, link)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (current_time, user.id, user.full_name, user.username, user.language_code, user.link))
    conn.commit()
    conn.close()


def list_users():
    logger.debug(f'Listing users from database')
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT created_at, user_id, full_name, username, language_code, link FROM users")
    users = c.fetchall()
    conn.close()
    return users


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f'In start_command!')
    logger.debug(f"Update object: {update}")
    logger.debug(f"Message object: {update.message}")
    user = update.message.from_user  # Get the user who sent the message
    add_user(user)  # Add the user to the database

    if update and update.effective_user:
        user_id = update.effective_user.id
        #logger.debug(f"User ID: {user_id}")
        #await update.message.reply_text(f"This is the help command, user {user_id}!")
        if is_permitted(user_id):
            await update.message.reply_text('Hello! Thanks for chatting with me. I am WallaFeederBot!')
        else:
            await update.message.reply_text("Sorry, you are not permitted to use this bot.")
    else:
        # Log if either update or effective_user is None
        logger.error(f"Invalid update or user: {update}, {update.effective_user}")
    # Further debugging if there's an issue with the message object
    if not update.message:
        logger.error("No message object found in the update!")


async def help_command(update: Update, context:CallbackContext):
    logger.debug(f'In help_command!')
    user_id = update.effective_user.id
    if is_permitted(user_id):
        await update.message.reply_text(f'This is the help command!\n'
                                        'The methods you can use are:\n'
                                        '\'bot version\'\n\'live\'\n\'set log info\'\n\'set log debug\'\n'
                                        '\'test method\'\n\'list users\'\n')
    else:
        await update.message.reply_text("Sorry, you are not permitted to use this bot.")


async def start_listen_command(update: Update, context:CallbackContext):
    logger.debug(f'In start_listen_command!')
    user_id = update.effective_user.id
    listen_interval = 2700
    if is_permitted(user_id):
        await update.message.reply_text(f'Start listening for rss every {listen_interval} seconds!')
        chat_id = update.message.chat_id
        logger.debug('Started callback_check_new_entries')
        context.application.job_queue.run_repeating(callback_check_new_entries, listen_interval, name=str(chat_id))
    else:
        await update.message.reply_text("Sorry, you are not permitted to use this bot.")


async def stop_listen_command(update: Update, context:CallbackContext):
    logger.debug(f'In stop_listen_command!')
    user_id = update.effective_user.id
    if is_permitted(user_id):
        await update.message.reply_text('Stopping from listening for rss!')
        chat_id = update.message.chat_id
        # context.bot.send_message(chat_id=chat_id, text='Stopping automatic messages!')
        logger.debug('Looking for jobs')
        # job = context.application.job_queue.jobs()
        job = context.application.job_queue.get_jobs_by_name(name=str(chat_id))
        if job:
            logger.debug('Stoping job[0]')
            job[0].schedule_removal()
        else:
            logger.debug('There are no jobs scheduled.')
            await update.message.reply_text('There are no jobs scheduled.')

    else:
        await update.message.reply_text("Sorry, you are not permitted to use this bot.")


def callback_check_new_entries(context):
    check_new_entries()


def send_message_to_group(RSSObject, chat_id, thread_id=0):
    # formatting options in here: https://core.telegram.org/bots/api#formatting-options

    if RSSObject.image_url:
        url_post = (f"https://api.telegram.org/bot{TOKEN}/sendPhoto?chat_id=" + str(chat_id) +
                    "&photo=" + str(RSSObject.image_url) + "&message_thread_id=" + str(thread_id) +
                    "&parse_mode=HTML" + "&caption=" +
                    "<b>" + "<a href=\"" + RSSObject.url + "\">" + str(RSSObject.title) + "</a>" + "</b>\n\n" +
                    str(RSSObject.description) + "\n\n" + "וואלה - ערוץ העדכונים הלא רשמי")
        headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
        r = requests.post(url_post, headers=headers)
        #print(r)
        #print(requests.get(url).json())  # this sends the message
    else:
        url_post = (f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id=" + str(chat_id) +
                    "&message_thread_id=" + str(thread_id) + "&parse_mode=HTML" + "&text=" +
                    "<b>" + "<a href=\"" + RSSObject.url + "\">" + str(RSSObject.title) + "</a>" + "</b>\n\n" +
                    str(RSSObject.description) + "\n\n" + "וואלה - ערוץ העדכונים הלא רשמי")
        headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
        r = requests.post(url_post, headers=headers)


def check_new_entries():
    try:
        for current_walla_url in Enums.URLs:
            rss_entry_class = RSSClass.RSSClass(_logger=logger)
            logger.info(f'\nFetching url: {current_walla_url.name}')

            try:
                response = requests.get(current_walla_url)
                if response.status_code != 200:
                    logger.debug(f"Failed to fetch RSS feed, status code: {response.status_code}")
                    logger.debug(f"response.text: {response.text}")
                    return
            except requests.exceptions.RequestException as e:
                logger.debug(f"Error: {e}")
                return None

            rss_feed = feedparser.parse(current_walla_url)
            if rss_feed == None:
                logger.debug("No entries found in the RSS feed.")
                continue
            rss_entry_class.rss_object.title = rss_feed.entries[0].title
            rss_entry_class.rss_object.url = rss_feed.entries[0].link
            rss_entry_class.rss_object.id = rss_entry_class.extract_id(rss_feed.entries[0].id)
            rss_entry_class.rss_object.published_date = rss_feed.entries[0].published
            rss_entry_class.rss_object.image_url = rss_feed.entries[0].links[1].href

            description_html = rss_feed.entries[0].description
            soup = BeautifulSoup(description_html, 'html.parser')
            rss_entry_class.rss_object.description = soup.get_text(strip=True)

            if rss_entry_class.is_new_entry(rss_entry_class.rss_object.id, current_walla_url.name):
                logger.debug(rss_entry_class.print_class())
                if current_walla_url.name == Enums.URLs.WallaSports.name:
                    current_chat_id = Enums.WallaGroupsChatsIDs.WallaSports
                else:
                    current_chat_id = Enums.WallaGroupsChatsIDs.WallaNews
                #current_chat_id = getattr(Enums.WallaGroupsChatsIDs, current_walla_url.name, None)
                send_message_to_group(RSSObject=rss_entry_class.rss_object, chat_id=current_chat_id)
            else:
                logger.info(f'The entry for {current_walla_url.name} is not a new entry')
            time.sleep(128)
    except NameError:
        logger.error("Error fetching rss feed")
    except Exception as e:
        logger.error("Something else went wrong, the error is: ", e)


def handle_text_response(text: str) -> str:
    new_text = text.lower()
    return new_text


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_permitted(user_id):
        await update.message.reply_text("Sorry, you are not permitted to use this bot.")
        return
    message_type: str = update.message.chat.type
    text = str = update.message.text.lower()

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')
    match text:
        case "bot version":
            logger.info('Got \'bot version\' message')
            await update.message.reply_text(f'The bot version is: {BOT_VERSION}')
        case "live":
            logger.info('Got \'live\' message')
            await update.message.reply_text(f'The bot is live!')
        case 'set log info':
            logger.info(f'Got \'set log info\' message')
            change_log_level(logging.INFO)
            await update.message.reply_text(f'Log level set to INFO')
        case 'set log debug':
            logger.debug(f'Got \'set log debug\' message')
            change_log_level(logging.DEBUG)
            await update.message.reply_text(f'Log level set to DEBUG')
        case 'test method':
            logger.info(f'Got \'test method\' message')
            #check_new_products()
            check_function()
        case 'list users':
            logger.info(f'Got \'list users\' message')
            users = list_users()
            if users:
                users = "\n".join([f"created_at = {user[0]}, user id: {user[1]}, full_name: {user[2]}, username: {user[3]},"
                                   f" language_code: {user[4]}, link: {user[5]}"
                             for user in users])
                await update.message.reply_text(users)
            else:
                await update.message.reply_text(f'No users found!')


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f'Update {update} caused error {context.error}')


def init_logger():
    logger.debug('initializing logger')
    logger.setLevel(LOG_LEVEL)
    # Create a stream-based handler that writes the log entries    #into the standard output stream
    handler = logging.StreamHandler(sys.stdout)
    # Create a formatter and apply it to the handler
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def change_log_level(new_level):
    global LOG_LEVEL
    LOG_LEVEL = new_level
    logger.setLevel(LOG_LEVEL)
    logger.info(f'logger level set to {LOG_LEVEL}')


def check_function():
    check_new_entries()
    pass


if __name__ == '__main__':
    init_logger()
    logger.info('Starting WallaFeeder bot...')

    #check_function()
    app = Application.builder().token(TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("start_listen", start_listen_command))
    app.add_handler(CommandHandler("stop_listen", stop_listen_command))

    # Set up the database
    setup_database()

    # Message handler for all text messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polls
    logger.info('Polling...')
    app.run_polling(poll_interval=2)
