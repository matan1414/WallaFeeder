import logging, sys, os
import requests
from typing import Final
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes, Application, CallbackContext, JobQueue
from bs4 import BeautifulSoup
import time
import RSSClass
import Enums
import feedparser

TOKEN: Final = os.environ.get('TOKEN')
BOT_USERNAME: Final = "@WallaFeederBot"
DEBUG: Final = True
logger = logging.getLogger('WallaFeederLogger')
LAST_PRODUCT_ID_YAD2 = '7765792161852'
LAST_PRODUCT_ID_AGORA = '7765792161852'


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug(f'In start_command!')
    await update.message.reply_text('Hello! Thanks for chatting with me. I am LemesiraBot!')

async def help_command(update: Update, context:CallbackContext):
    logger.debug(f'In help_command!')
    await update.message.reply_text('This is the help command!')


async def start_listen_command(update: Update, context:CallbackContext):
    logger.debug(f'In start_listen_command!')
    await update.message.reply_text('Start listening for new products!')
    chat_id = update.message.chat_id
    logger.debug('Started run_repeating')
    context.application.job_queue.run_repeating(callback_check_new_products, 600, name=str(chat_id))


async def stop_listen_command(update: Update, context:CallbackContext):
    logger.debug(f'In stop_listen_command!')
    await update.message.reply_text('Stopping from listening for new products!')
    chat_id = update.message.chat_id
    #context.bot.send_message(chat_id=chat_id, text='Stopping automatic messages!')
    logger.debug('Looking for jobs')
    # job = context.application.job_queue.jobs()
    job = context.application.job_queue.get_jobs_by_name(name=str(chat_id))
    logger.debug('Stop job[0]')
    job[0].schedule_removal()

def callback_check_new_products(context):
    check_new_products()


def handle_text_response(text: str) -> str:
    text = text.lower()
    #if "yad2" in text:
    #    fetch_Yad2()

def send_message_to_group(RSSObject, chat_id, thread_id=0):
    # formatting options in here: https://core.telegram.org/bots/api#formatting-options

    if RSSObject.image_url:
        url_post = (f"https://api.telegram.org/bot{TOKEN}/sendPhoto?chat_id=" + str(chat_id) +
                    "&photo=" + str(RSSObject.image_url) + "&message_thread_id=" + str(thread_id) +
                    "&caption=" + "&parse_mode=HTML" +
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


def check_new_products():
    # Check Yad2 for new products
    agora_class = AgoraClass.AgoraClass(logger)

    for agora_url in Enums.AgoraURLs:
        item_agora_received = agora_class.fetch_item(agora_url)
        item_agora, item_city_topic = agora_class.handle_item(item_agora_received, agora_url.name)
        if item_agora:
            send_message_to_group(Enums.ChatsIds.LemesiraMainGroup, item_city_topic, agora_class.print_class())


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text = str = update.message.text.lower()

    print(f'User ({update.message.chat.id}) in {message_type}: "{text}"')
    if "do" in text:
        check_new_products()
        # if reply:
        #     #await update.message.reply_text(reply)
        #     send_message_to_group(Enums.ChatsIds.LemesiraTempGroup, reply)
        # else:
        #     logger.warning("Fetched yad2 data is empty.")
        #     await update.message.reply_text("Fetched yad2 data is empty.")

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


# def init_seleniumbase_driver():
#     logger.debug('initializing seleniumbase_driver')
#     os.environ["PATH"] = "/opt/render/project/.render/chrome/opt/google/chrome:" + os.environ.get("PATH", "")
#     try:
#         driver = Driver(uc=True, headless=True)
#         driver.get(Enums.LemesiraURLs.example)
#         time.sleep(1)
#     except NameError:
#         logger.error(f'Error fetching url in init_seleniumbase_driver try')
#     except Exception as e:
#         logger.error(f'Something else went wrong in init_seleniumbase_driver try, the error is: {e}')
#     finally:
#         logger.debug(f'init_seleniumbase_driver.quit()')
#         driver.quit()


def check_function():
    # agora_class = AgoraClass.AgoraClass(logger)
    # for agora_url in Enums.AgoraURLs:
    #     item_agora_received = agora_class.fetch_item(agora_url)
    #     item_agora, item_city_topic = agora_class.handle_item(item_agora_received, agora_url.name)
    #     if item_agora:
    #         send_message_to_group(Enums.ChatsIds.LemesiraMainGroup, item_city_topic, agora_class.print_class())
    try:
        for current_walla_url in Enums.URLs:
            rss_entry_class = RSSClass.RSSClass(_logger=logger)

            rss_feed = feedparser.parse(current_walla_url)
            rss_entry_class.rss_object.title = rss_feed.entries[0].title
            rss_entry_class.rss_object.url = rss_feed.entries[0].link
            rss_entry_class.rss_object.id = rss_feed.entries[0].id[30:]
            rss_entry_class.rss_object.published_date = rss_feed.entries[0].published
            rss_entry_class.rss_object.image_url = rss_feed.entries[0].links[1].href

            description_html = rss_feed.entries[0].description
            soup = BeautifulSoup(description_html, 'html.parser')
            rss_entry_class.rss_object.description = soup.get_text(strip=True)

            rss_entry_class.print_class()
            if rss_entry_class.is_new_entry(rss_entry_class.rss_object.id, current_walla_url.name):
                current_chat_id = getattr(Enums.WallaGroupsChatsIDs, current_walla_url.name, None)
                send_message_to_group(RSSObject=rss_entry_class.rss_object, chat_id=current_chat_id)
    except NameError:
        logger.error("Error fetching rss feed")
    except Exception as e:
        logger.error("Something else went wrong, the error is: ", e)

    # entry_object = RSSObject.RSSObject()
    #
    # walla_news_rss_url = Enums.URLs.WallaNews
    # rss_feed = feedparser.parse(walla_news_rss_url)
    # entry_object.title = rss_feed.entries[0].title
    # entry_object.url = rss_feed.entries[0].link
    # entry_object.id = rss_feed.entries[0].id[30:]
    # entry_object.published_date = rss_feed.entries[0].published
    # entry_object.image_url = rss_feed.entries[0].links[1].href
    #
    # description_html = rss_feed.entries[0].description
    # soup = BeautifulSoup(description_html, 'html.parser')
    # entry_object.description = soup.get_text(strip=True)
    #
    # send_message_to_group(RSSObject=entry_object, chat_id=Enums.WallaGroupsChatsIDs.WallaNews)

if __name__ == '__main__':
    init_logger()
    logger.info('Starting WallaFeeder bot...')
    logger.debug('branch: agora_scrape')

    check_function()
    #init_seleniumbase_driver()
    app = Application.builder().token(TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    #app.add_handler(CommandHandler("start_listen", start_listen_command))
    #app.add_handler(CommandHandler("stop_listen", stop_listen_command))

    # Message handler for all text messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    # Polls
    logger.info('Polling...')
    app.run_polling(poll_interval=2)
