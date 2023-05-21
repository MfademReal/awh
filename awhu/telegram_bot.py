import sys
import time
import os
from telethon.tl.types import DocumentAttributeVideo,InputMediaUploadedDocument
from awhu.config import Config
from telethon.sync import TelegramClient, events
import asyncio
import logging
import sys
import re
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
    if(chat_id[:4] != "-100" and chat_id[1:].isdigit()):
        chat_id = int(f"-100{chat_id}")
    return chat_id




def handle_message(update, context):
    message_id = update.message.message_id
    print("Received message ID:", message_id)




def dump(obj,file):
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

def download(link="", chat_id="", msg_id=0, folder= "."):
    os.system(f"rm *.session*")
    if(link != ""):
         tmp = link.split("/")
         chat_id = tmp[-2]
         msg_id = int(tmp[-1])
    chat_id = trim_id(chat_id)
    async def fast_download():
        asyncio.set_event_loop(asyncio.new_event_loop())
        bot = await TelegramClient('bot',Config.APP_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)
        message = await bot.get_messages(chat_id, ids=msg_id)
        begin = time.time()
        try:
            filename=message.media.document.attributes[0].file_name
        except:
            filename=message.media.document.attributes[-1].file_name
        print(f"Downloading {filename}:")
        with open(filename, "wb") as out:
            path= await download_file(bot,message.document,out)
        end = time.time()
        unzip(filename, folder)
        logging.warning(f"\nElapsed Time: {int((end-begin)//60)}min : {int((end-begin) % 60)}sec")
    asyncio.run(fast_download())


def upload(chat_id, path, caption: str = "",video_mode=False):
    if(not os.path.exists(path)):return 
    chat_id = trim_id(chat_id)
    user=chat_id
    if(Config.AWHT_ID in ["Shiroyasha","NOT85"] and user=="colab_hs_bot"):return 
    os.system(f"rm *.session*")
    if(os.path.exists(f"{user}.pickle")):
        chat_id=load(user)
    async def fast_upload():
        asyncio.set_event_loop(asyncio.new_event_loop())
        bot = await TelegramClient('bot',Config.APP_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)
        if(not os.path.exists(f"{user}.pickle")):
            input_entity=await bot.get_input_entity(user)
            dump(input_entity,chat_id)
        begin = time.time()
        logging.warning(f"Uploading {path}:")
        with open(path, "rb") as out:
            res = await upload_file(bot, out)
            attributes, mime_type = utils.get_attributes(path)
            media = InputMediaUploadedDocument(
                file=res,
                mime_type=mime_type,
                attributes=attributes,
                # not needed for most files, thumb=thumb,
                force_file=not video_mode
            )
            await bot.send_file(chat_id, media,caption=caption,parse_mode='HTML')
        end = time.time()
        logging.warning(f"\nElapsed Time: {int((end-begin)//60)}min : {int((end-begin) % 60)}sec")

    asyncio.run(fast_upload())

def sort_files(chat_id, from_who, epi_ids):
    os.system(f"rm *.session*")
    asyncio.set_event_loop(asyncio.new_event_loop())
    bot = TelegramClient('bot', Config.APP_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)
    chat_id=trim_id(chat_id)
    from_who=trim_id(from_who)

    def same_name(src, name):
        x = regex.search("\[AWHT\]([a-zA-Z!. ]*).*", name)
        return x != None and x.groups(0)[0].lower() == src.lower()
    messages = bot.get_messages(from_who, ids=list(epi_ids))
    src = regex.search("\[AWHT\]([a-zA-Z!. ]*).*",
                    messages[0].document.attributes[0].file_name).groups(0)[0]
    offset = epi_ids.start
    epi_links = []
    while(offset < epi_ids.stop):
        logging.info(epi_links)
        for msg in messages:
            if msg.document == None:
                continue
            fn = msg.document.attributes[0].file_name
            if not same_name(src, fn):
                continue
            epi = regex.search("[-Ee ]([0-9]{2,4})[ \[\(.]", fn).groups(0)[0]
            epi_links.append(((epi, fn), msg.id))
        offset += 200
        if(offset >= epi_ids.stop):
            break
        messages = bot.get_messages(from_who, ids=list(range(offset, epi_ids.stop)))

    epi_links=list(dict(epi_links).items())
    epi_links.sort()
    print(epi_links)
    is_line_sent = False
    for i in range(0, len(epi_links), 3):
        epi = epi_links[i][0][0]
        bot.forward_messages(chat_id, from_peer=from_who, messages=epi_links[i+1][1])
        bot.forward_messages(chat_id, from_peer=from_who, messages=epi_links[i+2][1])
        bot.forward_messages(chat_id, from_peer=from_who, messages=epi_links[i][1])
        if(not is_line_sent):
            bot.send_message(chat_id, ".................")
            is_line_sent = True



def archive_files(msg_ids):
    os.system(f"rm *.session*")
    asyncio.set_event_loop(asyncio.new_event_loop())
    bot = TelegramClient('bot', Config.APP_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)
    for msg_id in msg_ids:
      message = bot.get_messages("AWHTarchive", ids=msg_id)
      if(message==None):continue
      print(f"\nMessage {msg_id} 👇")
      x=message.media.document.attributes[0]
      if(type(x) is DocumentAttributeVideo):continue
      filename=x.file_name
      print(f"\nDownloading {filename}:")
      path= bot.download_media(message, progress_callback=progress)
      print(f"\nUploading {filename}:")
      bot.send_file(-1001531045531, path, force_document=True,caption=message.message,progress_callback=progress)

def download_files(chat_id,msg_ids):
    os.system(f"rm *.session*")
    chat_id=trim_id(chat_id)
    asyncio.set_event_loop(asyncio.new_event_loop())
    bot = TelegramClient('bot', Config.APP_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)
    for msg_id in msg_ids:
      message = bot.get_messages(chat_id, ids=msg_id)
      if(message==None):continue
      print(f"\nMessage {msg_id} 👇")
      x=message.media.document.attributes[0]
      if(type(x) is DocumentAttributeVideo):continue
      filename=x.file_name
      print(f"\nDownloading {filename}:")
      path= bot.download_media(message, progress_callback=progress)


def upload_files(chat_id,files):
    os.system(f"rm *.session*")
    chat_id=trim_id(chat_id)
    asyncio.set_event_loop(asyncio.new_event_loop())
    bot = TelegramClient('bot', Config.APP_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)
    l=len(files)
    for i,file in enumerate(files):
      print(f"\nUploading {file}: ({i} out of {l})")
      bot.send_file(chat_id, file, force_document=True,progress_callback=progress, reply_to_message_id=message_id)


def send_msg(chat_id,msg):
    os.system(f"rm *.session*")
    chat_id=trim_id(chat_id)
    asyncio.set_event_loop(asyncio.new_event_loop())
    bot = TelegramClient('bot', Config.APP_ID, Config.API_HASH).start(bot_token=Config.BOT_TOKEN)
    if(msg!=""):
        bot.send_message(chat_id,msg,reply_to_message_id=message_id)


def testupload(t_id,filename):
  async def progress(current, total):
    print(f"{current * 100 / total:.1f}%")

  async def main():
    async with Client("bot2", api_id=Config.APP_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN) as app:
        await app.send_document(t_id, filename, progress=progress, reply_to_message_id=message_id)

  asyncio.run(main())
