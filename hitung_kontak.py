import logging
import os
from telebot.types import Message
from telebot.apihelper import ApiTelegramException

from bot import bot
from message import *
from helpers import count_vcf_contacts
from state import HitungCtcState  # Use HitungCtcState

@bot.message_handler(commands='count_contacts')
async def count_contacts_command(message):
    try:
        await bot.delete_state(message.from_user.id, message.chat.id)
        await bot.set_state(message.from_user.id, HitungCtcState.waiting_for_files, message.chat.id)
        await bot.reply_to(message, "Silakan kirim file .vcf satu per satu untuk menghitung kontak. Kirim '/selesai' jika sudah.")
    except Exception as e:
        logging.error("Error: ", exc_info=True)

@bot.message_handler(state=HitungCtcState.waiting_for_files, content_types=['document'])
async def vcf_get(message: Message):
    try:
        if not message.document.file_name.endswith(".vcf"):
            return await bot.send_message(message.chat.id, "Kirim file .vcf yang valid.")
        
        file = await bot.get_file(message.document.file_id)
        filename = f"files/{message.document.file_name}"
        
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if 'filenames' not in data:
                data['filenames'] = []
            data['filenames'].append(filename)

        downloaded_file = await bot.download_file(file.file_path)
        with open(filename, 'wb') as new_file:
            new_file.write(downloaded_file)

        await bot.send_message(message.chat.id, f"File {message.document.file_name} diterima. Silakan kirim file .vcf lain atau ketik '/selesai' untuk menghitung kontak.")
    except Exception as e:
        logging.error("Error: ", exc_info=True)

@bot.message_handler(commands='selesai', state=HitungCtcState.waiting_for_files)
async def count_all_vcf_contacts(message: Message):
    try:
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if 'filenames' not in data or len(data['filenames']) == 0:
                return await bot.send_message(message.chat.id, "Tidak ada file .vcf yang diunggah.")
            
            total_contacts = 0
            result_message = ""

            for filename in data['filenames']:
                contacts_in_file = count_vcf_contacts(filename)
                total_contacts += contacts_in_file

                # Format output for the current file
                result_message += f"Nama file: {filename}\nIsi kontak: {contacts_in_file} kontak ditemukan.\n\n"

                # Remove the file if it's no longer needed
                os.remove(filename)

            # Add total contacts to the result message
            result_message += f"Total kontak di semua file: {total_contacts}"
            await bot.send_message(message.chat.id, result_message)
        
        await bot.delete_state(message.from_user.id, message.chat.id)
    except Exception as e:
        logging.error("Error: ", exc_info=True)

@bot.message_handler(state=HitungCtcState.waiting_for_files, commands=['cancel'])
async def cancel_process(message: Message):
    try:
        await bot.send_message(message.chat.id, "Proses dibatalkan.")
        await bot.delete_state(message.from_user.id, message.chat.id)
    except Exception as e:
        logging.error("Error: ", exc_info=True)
