import logging
import os
from asyncio import sleep
from telebot.types import Message
from telebot.apihelper import ApiTelegramException

from bot import bot
from message import *
from helpers import *
from state import GabungTxtState

# Ensure the 'files' directory exists
if not os.path.exists('files'):
    os.makedirs('files')

@bot.message_handler(commands='gabungtxt')
async def gabung_txt_command(message: Message):
    try:
        await bot.delete_state(message.from_user.id, message.chat.id)
        await bot.set_state(message.from_user.id, GabungTxtState.waiting_for_files, message.chat.id)
        await bot.reply_to(message, txt_gabung_txt)
    except Exception as e:
        logging.error("Error in gabung_txt_command: ", exc_info=True)

@bot.message_handler(state=GabungTxtState.waiting_for_files, content_types=['document'])
async def handle_txt_files(message: Message):
    try:
        if not message.document.file_name.endswith(".txt"):
            return await bot.send_message(message.chat.id, "Kirim file .txt")
        
        file = await bot.get_file(message.document.file_id)
        filename = f"files/{message.document.file_name}"
        
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if 'files' not in data:
                data['files'] = []
            data['files'].append(filename)
        
        downloaded_file = await bot.download_file(file.file_path)
        with open(filename, 'wb') as new_file:
            new_file.write(downloaded_file)

        await bot.send_message(message.chat.id, 'File diterima. Silakan kirim file TXT lainnya atau ketik /done jika sudah selesai.')
    except Exception as e:
        logging.error("Error in handle_txt_files: ", exc_info=True)

@bot.message_handler(state=GabungTxtState.waiting_for_files, commands=['done'])
async def handle_done(message: Message):
    try:
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if 'files' not in data or not data['files']:
                return await bot.send_message(message.chat.id, "Tidak ada file TXT yang diterima.")
            
            await bot.send_message(message.chat.id, 'Silakan masukkan nama file TXT yang akan dihasilkan:')
            await bot.set_state(message.from_user.id, GabungTxtState.name, message.chat.id)
    except Exception as e:
        logging.error("Error in handle_done: ", exc_info=True)

@bot.message_handler(state=GabungTxtState.name)
async def handle_txt_name(message: Message):
    try:
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['name'] = message.text
            output_file = f"files/{message.text}.txt"
            gabung_txt(data['files'], output_file)
            
            for file in data['files']:
                os.remove(file)

            if not os.path.exists(output_file):
                return await bot.send_message(message.chat.id, "File hasil penggabungan tidak ditemukan. Coba lagi.")
            
            while True:
                try:
                    with open(output_file, 'rb') as doc:
                        await bot.send_document(message.chat.id, doc)
                    os.remove(output_file)
                    break
                except ApiTelegramException as e:
                    if "Too Many Requests" in str(e):
                        delay = int(findall(r'\d+', str(e))[0])
                        await sleep(delay)
                    else:
                        logging.error("API exception: ", exc_info=True)
                        continue
                except Exception as e:
                    logging.error("Error sending document: ", exc_info=True)
                    continue

            await bot.send_message(message.chat.id, "Gabung TXT selesai!")
        await bot.delete_state(message.from_user.id, message.chat.id)
    except Exception as e:
        logging.error("Error in handle_txt_name: ", exc_info=True)

