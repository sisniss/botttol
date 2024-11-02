import logging
import os
from re import findall
from asyncio import sleep
from telebot.types import Message
from telebot.apihelper import ApiTelegramException

from bot import bot
from message import *
from helpers import *
from state import PecahTxtState

@bot.message_handler(commands='pecahtxt')
async def pecahtxt_command(message):
  try:
    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.set_state(message.from_user.id, PecahTxtState.filename, message.chat.id)
    await bot.reply_to(message, txt_pecah_txt)
  except Exception as e:
    logging.error("error: ", exc_info=True)

@bot.message_handler(state=PecahTxtState.filename, content_types=['document'])
async def txt_get(message: Message):
  try:
    if not message.document.file_name.endswith(".txt"):
      return await bot.send_message(message.chat.id, "Kirim file .txt")
    
    file = await bot.get_file(message.document.file_id)
    filename = f"files/{message.document.file_name}"
    
    await bot.set_state(message.from_user.id, PecahTxtState.name, message.chat.id)
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
      data['filename'] = filename

    downloaded_file = await bot.download_file(file.file_path)
    with open(filename, 'wb') as new_file:
      new_file.write(downloaded_file)
    
    await bot.send_message(message.chat.id, 'File diterima. Silakan masukan nama file txt yang akan dihasilkan:')
  except Exception as e:
    logging.error("error: ", exc_info=True)

@bot.message_handler(state=PecahTxtState.filename)
async def not_txt(message: Message):
  try:
    await bot.send_message(message.chat.id, 'Kirim file .txt')
  except Exception as e:
    logging.error("error: ", exc_info=True)

@bot.message_handler(state=PecahTxtState.name)
async def name_get(message: Message):
  try:
    await bot.send_message(message.chat.id, f'Nama file diatur menjadi: {message.text}. Silakan masukkan jumlah nomor per file:')
    await bot.set_state(message.from_user.id, PecahTxtState.totaln, message.chat.id)
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
      data['name'] = message.text
  except Exception as e:
    logging.error("error: ", exc_info=True)

@bot.message_handler(state=PecahTxtState.totaln, is_digit=True)
async def number_get(message: Message):
  try:
    await bot.send_message(message.chat.id, f'Jumlah nomor diatur menjadi: {message.text}. Silakan masukkan jumlah file:')
    await bot.set_state(message.from_user.id, PecahTxtState.totalf, message.chat.id)
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
      data['totaln'] = int(message.text)
  except Exception as e:
    logging.error("error: ", exc_info=True)

@bot.message_handler(state=PecahTxtState.totalf, is_digit=True)
async def name_get(message: Message):
  try:
    await bot.send_message(message.chat.id, f'Jumlah file diatur menjadi: {message.text}. Mulai memecah file...')
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
      data['totalf'] = int(message.text)
      files = pecah_txt(data)
      i = 0
      os.remove(data['filename'])
      while i < len(files):
        try:
          await bot.send_document(message.chat.id, open(files[i], 'rb'))
          os.remove(files[i])
          i+=1
        except ApiTelegramException as e:
          if "Too Many Requests" == e.description:
            delay = int(findall('\d+', e.description)[0])
            await sleep(delay)
          else:
            continue
        except Exception as e:
          continue

      await bot.send_message(message.chat.id, "Pecah txt selesai!")
    await bot.delete_state(message.from_user.id, message.chat.id)
  except Exception as e:
    logging.error("error: ", exc_info=True)

@bot.message_handler(state=PecahTxtState.totaln, is_digit=False)
@bot.message_handler(state=PecahTxtState.totalf, is_digit=False)
async def name_get(message: Message):
  try:
    await bot.send_message(message.chat.id, 'Masukkan angka')
  except Exception as e:
    logging.error("error: ", exc_info=True)
