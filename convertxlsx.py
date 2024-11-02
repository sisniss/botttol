import logging
import os
from re import findall
from asyncio import sleep
from telebot.types import Message
from telebot.apihelper import ApiTelegramException

from bot import bot
from message import *
from helpers import *
from state import ConvertXlsxState

@bot.message_handler(commands='convertxlsx')
async def convertxlsx_command(message):
  try:
    await bot.delete_state(message.from_user.id, message.chat.id)
    await bot.set_state(message.from_user.id, ConvertXlsxState.filename, message.chat.id)
    await bot.reply_to(message, txt_convertxlsx)
  except Exception as e:
    logging.error("error: ", exc_info=True)

@bot.message_handler(state=ConvertXlsxState.filename, content_types=['document'])
async def txt_get(message: Message):
  try:
    if not message.document.file_name.endswith(".xlsx"):
      return await bot.send_message(message.chat.id, "Kirim file .xlsx")
    
    file = await bot.get_file(message.document.file_id)
    filename = f"files/{message.document.file_name}"
    
    await bot.set_state(message.from_user.id, ConvertXlsxState.name, message.chat.id)
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
      data['filename'] = filename

    downloaded_file = await bot.download_file(file.file_path)
    with open(filename, 'wb') as new_file:
      new_file.write(downloaded_file)

    await bot.send_message(message.chat.id, 'File diterima. Silakan masukan nama file txt yang akan dihasilkan:')
  except Exception as e:
    logging.error("error: ", exc_info=True)

@bot.message_handler(state=ConvertXlsxState.filename)
async def not_txt(message: Message):
  try:
    await bot.send_message(message.chat.id, 'Kirim file .xlsx')
  except Exception as e:
    logging.error("error: ", exc_info=True)

@bot.message_handler(state=ConvertXlsxState.name)
async def name_get(message: Message):
  try:
    await bot.send_message(message.chat.id, f'Nama file diatur menjadi: {message.text}. Mulai mengonversi file...')
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
      data['name'] = message.text
      file = convert_xlsx_to_txt(data)
      os.remove(data['filename'])

      while True:
        try:
          await bot.send_document(message.chat.id, open(file, 'rb'))
          os.remove(file)
          break
        except ApiTelegramException as e:
          if "Too Many Requests" == e.description:
            delay = int(findall(r'\d+', e.description)[0])
            await sleep(delay)
          else:
            continue
        except Exception as e:
          continue

      await bot.send_message(message.chat.id, "Convert Xlsx to txt selesai!")
    await bot.delete_state(message.from_user.id, message.chat.id)
  except Exception as e:
    logging.error("error: ", exc_info=True)
