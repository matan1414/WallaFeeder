import logging, sys, os
import requests
from typing import Final
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, Application, CallbackContext, JobQueue
from bs4 import BeautifulSoup
import RSSClass
import Enums
import feedparser

TOKEN: Final = os.environ.get('TOKEN')
BOT_USERNAME: Final = "@WallaFeederBot"
DEBUG: Final = True
logger = logging.getLogger('WallaFeederLogger')

PERMITTED_ID: Final = int(os.environ.get('PERMITTED_ID'))

def is_permitted(user_id):
    return user_id == PERMITTED_ID

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f'In start_command!')
    logger.debug(f"Update object: {update}")
    logger.debug(f"Message object: {update.message}")
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
        await update.message.reply_text('This is the help command!')
    else:
        await update.message.reply_text("Sorry, you are not permitted to use this bot.")


async def start_listen_command(update: Update, context:CallbackContext):
    logger.debug(f'In start_listen_command!')
    user_id = update.effective_user.id
    if is_permitted(user_id):
        await update.message.reply_text('Start listening for rss!')
        chat_id = update.message.chat_id
        logger.debug('Started callback_check_new_entries')
        context.application.job_queue.run_repeating(callback_check_new_entries, 370, name=str(chat_id))
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
            logger.info(f'Fetching url: {current_walla_url.name}')

            response = requests.get(current_walla_url)
            print(response.text)  # Log the feed content
            if response.status_code != 200:
                logger.debug(f"Failed to fetch RSS feed, status code: {response.status_code}")
                return
            rss_feed = feedparser.parse(current_walla_url)
            if rss_feed == None:
                logger.debug("No entries found in the RSS feed.")
            else:
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
    except NameError:
        logger.error("Error fetching rss feed")
    except Exception as e:
        logger.error("Something else went wrong, the error is: ", e)


def handle_text_response(text: str) -> str:
    new_text = text.lower()
    return new_text


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text = str = update.message.text.lower()

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')
    if "test" in text:
        # response: str = handle_text_response(text)
        await update.message.reply_text('Test Successful')
    if "do" in text:
        check_new_entries()
    # if message_type == 'group':
    #     if BOT_USERNAME in text:
    #         new_text: str = text.replace(BOT_USERNAME, '').strip()
    #         response: str = handle_text_response(new_text)
    #     else:
    #         return
    # else:
    #     response: str = handle_text_response(text)

    # print('Bot:', response)
    # await update.message.reply_text(response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f'Update {update} caused error {context.error}')


def init_logger():
    logger.debug('initializing logger')
    # Set the threshold logging level of the logger to INFO
    if DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    # Create a stream-based handler that writes the log entries    #into the standard output stream
    handler = logging.StreamHandler(sys.stdout)
    # Create a formatter for the logs
    logger.addHandler(handler)



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

    # Message handler for all text messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polls
    logger.info('Polling...')
    app.run_polling(poll_interval=2)
