import sys
import time
import os
from telethon.tl.types import DocumentAttributeVideo, InputMediaUploadedDocument
from awhu.config import Config
from telethon.sync import TelegramClient, events
import asyncio
import logging
import regex
from telethon import utils
from awhu.FastTelethon import download_file, upload_file
import dill as pickle
from pyrogram import Client
import requests
from subprocess import Popen, PIPE, STDOUT
from awhu.subtitle import Subtitle
from awhu.hardsub_logger import *
import IPython
from threading import Thread
import logging
import asyncio
import nest_asyncio


def trim_id(chat_id):
    chat_id = chat_id.strip().strip("@")
    if chat_id[:4] != "-100" and chat_id[1:].isdigit():
        chat_id = int(f"-100{chat_id}")
    return chat_id


def handle_message(update, context):
    message_id = update.message.message_id
    print("Received message ID:", message_id)


def dump(obj, file):
    with open(f'{file}.pickle', 'wb') as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)


def load(file):
    with open(f'{file}.pickle', 'rb') as handle:
        return pickle.load(handle)


def unzip(filename, folder="."):
    os.system(f"./7zz -y e \"{filename}\"  -o\"{folder}\"")


# Keep track of the progress while downloading
def progress(current, total):
    sys.stdout.write('\r')
    sys.stdout.write(f"{current * 100 / total:.1f}%")
    sys.stdout.flush()


def download(link="", chat_id="", msg_id=0, folder="."):
    os.system(f"rm *.session*")
    if link != "":
        tmp = link.split("/")
        chat_id = tmp[-2]
        msg_id = int(tmp[-1])
    chat_id = trim_id(chat_id)

    async def fast_download():
        asyncio.set_event_loop(asyncio.new_event_loop())
        bot = await TelegramClient('bot', Config.APP_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)
        message = await bot.get_messages(chat_id, ids=msg_id)
        begin = time.time()
        try:
            filename = message.media.document.attributes[0].file_name
        except:
            filename = message.media.document.attributes[-1].file_name
        print(f"Downloading {filename}:")
        with open(filename, "wb") as out:
            path = await download_file(bot, message.document, out)
        end = time.time()
        unzip(filename, folder)
        logging.warning(f"\nElapsed Time: {int((end - begin) // 60)}min : {int((end - begin) % 60)}sec")

    asyncio.run(fast_download())


def upload(chat_id, path, caption: str = "", video_mode=False):
    if not os.path.exists(path):
        return
    chat_id = trim_id(chat_id)
    user = chat_id
    if Config.AWHT_ID in ["Shiroyasha", "NOT85"] and user == "colab_hs_bot":
        return
    os.system(f"rm *.session*")
    if os.path.exists(f"{user}.pickle"):
        chat_id = load(user)

    async def fast_upload():
        asyncio.set_event_loop(asyncio.new_event_loop())
        bot = await TelegramClient('bot', Config.APP_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)
