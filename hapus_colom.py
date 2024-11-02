import os
import logging
import asyncio
from re import findall
from telebot.types import Message
from telebot.apihelper import ApiTelegramException

from bot import bot
from helpers import rearrange_to_one_column
from state import kolomState

# Pastikan direktori 'files' ada
if not os.path.exists('files'):
    os.makedirs('files')

@bot.message_handler(commands='1kolom', state=None)
async def satu_kolom_command(message: Message):
    try:
        await bot.delete_state(message.from_user.id, message.chat.id)
        await bot.set_state(message.from_user.id, kolomState.waiting_for_file, message.chat.id)
        await bot.reply_to(message, "Masukkan file .txt untuk diubah menjadi 1 kolom.")
    except Exception as e:
        logging.error("Error in satu_kolom_command: ", exc_info=True)

@bot.message_handler(state=kolomState.waiting_for_file, content_types=['document'])
async def handle_text_file(message: Message):
    try:
        if not message.document.file_name.endswith(".txt"):
            return await bot.send_message(message.chat.id, "Kirim file .txt")
        
        file = await bot.get_file(message.document.file_id)
        filename = f"files/{message.document.file_name}"
        
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['filename'] = filename
        
        downloaded_file = await bot.download_file(file.file_path)
        with open(filename, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Proses file untuk mengurutkan kolom
        output_file = filename.replace('.txt', '_sorted.txt')
        rearrange_to_one_column(filename, output_file)
        
        await bot.send_message(message.chat.id, 'File diproses. Mengirim hasil...')
        while True:
            try:
                with open(output_file, 'rb') as doc:
                    await bot.send_document(message.chat.id, doc)
                os.remove(output_file)
                break
            except ApiTelegramException as e:
                if "Too Many Requests" in str(e):
                    delay = int(findall(r'\d+', str(e))[0])
                    await asyncio.sleep(delay)
                else:
                    logging.error("API exception: ", exc_info=True)
                    continue
            except Exception as e:
                logging.error("Error sending document: ", exc_info=True)
                continue

        await bot.send_message(message.chat.id, "Proses selesai!")
        os.remove(filename)
        await bot.delete_state(message.from_user.id, message.chat.id)
    except Exception as e:
        logging.error("Error in handle_text_file: ", exc_info=True)
