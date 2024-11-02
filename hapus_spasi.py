import os
import logging
from telebot.types import Message
from telebot.apihelper import ApiTelegramException

from bot import bot
from message import txt_hapus_spasi
from helpers import remove_plus_and_spaces
from state import HapusSpasiState

# Pastikan direktori 'files' ada
if not os.path.exists('files'):
    os.makedirs('files')

@bot.message_handler(commands='hapuss', state=None)
async def hapus_spasi_command(message: Message):
    try:
        await bot.delete_state(message.from_user.id, message.chat.id)
        await bot.set_state(message.from_user.id, HapusSpasiState.waiting_for_file, message.chat.id)
        await bot.reply_to(message, "Masukkan file .txt. untuk di hapus karakternya.")
    except Exception as e:
        logging.error("Error in hapus_spasi_command: ", exc_info=True)

@bot.message_handler(state=HapusSpasiState.waiting_for_file, content_types=['document'])
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

        # Proses file untuk menghapus '+' dan spasi
        output_file = filename.replace('.txt', '_processed.txt')
        remove_plus_and_spaces(filename, output_file)
        
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
                    await sleep(delay)
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
