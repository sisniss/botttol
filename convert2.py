import logging
import os
from re import findall
from asyncio import sleep
from telebot.types import Message
from telebot.apihelper import ApiTelegramException
from bot import bot
from message import *
from helpers import convert2
from state import Convert2State

@bot.message_handler(commands='convert2')
async def convert_command(message):
    try:
        await bot.delete_state(message.from_user.id, message.chat.id)
        await bot.set_state(message.from_user.id, Convert2State.filename, message.chat.id)
        await bot.reply_to(message, txt2_convert)
    except Exception as e:
        logging.error("error: ", exc_info=True)

@bot.message_handler(state=Convert2State.filename, content_types=['document'])
async def txt_get(message: Message):
    try:
        if not message.document.file_name.endswith(".txt"):
            return await bot.send_message(message.chat.id, "Kirim file .txt")

        file = await bot.get_file(message.document.file_id)
        filename = f"files/{message.document.file_name}"
        logging.info(f"File akan disimpan dengan nama: {filename}")

        downloaded_file = await bot.download_file(file.file_path)
        with open(filename, 'wb') as new_file:
            new_file.write(downloaded_file)
        logging.info(f"File berhasil diunduh dan disimpan sebagai: {filename}")

        await bot.set_state(message.from_user.id, Convert2State.file_change_count, message.chat.id)
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['filename'] = filename

        await bot.send_message(message.chat.id, 'File diterima. Berapa kali nama file akan berganti?')
    except Exception as e:
        logging.error("error: ", exc_info=True)

@bot.message_handler(state=Convert2State.file_change_count, is_digit=True)
async def file_change_count_get(message: Message):
    try:
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['file_change_count'] = int(message.text)

        await bot.send_message(message.chat.id, 'Setiap berapa file nama file akan berganti? (Masukkan angka)')
        await bot.set_state(message.from_user.id, Convert2State.file_change_frequency, message.chat.id)

    except Exception as e:
        logging.error("Error in file_change_count_get: ", exc_info=True)

@bot.message_handler(state=Convert2State.file_change_frequency, is_digit=True)
async def file_change_frequency_get(message: Message):
    try:
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['file_change_frequency'] = int(message.text)

        await bot.send_message(message.chat.id, 'Masukkan nama file pertama:')
        await bot.set_state(message.from_user.id, Convert2State.file_names, message.chat.id)

    except Exception as e:
        logging.error("Error in file_change_frequency_get: ", exc_info=True)

@bot.message_handler(state=Convert2State.file_names)
async def file_names_get(message: Message):
    try:
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if 'file_names' not in data:
                data['file_names'] = []
            data['file_names'].append(message.text)

        if len(data['file_names']) < data['file_change_count']:
            await bot.send_message(message.chat.id, f'Masukkan nama file berikutnya ({len(data["file_names"]) + 1} dari {data["file_change_count"]}):')
        else:
            await bot.send_message(message.chat.id, 'Masukkan nama kontak per file:')
            await bot.set_state(message.from_user.id, Convert2State.contact_names, message.chat.id)

    except Exception as e:
        logging.error("Error in file_names_get: ", exc_info=True)

@bot.message_handler(state=Convert2State.contact_names)
async def contact_names_get(message: Message):
    try:
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            if 'contact_names' not in data:
                data['contact_names'] = []
            data['contact_names'].append(message.text)

        if len(data['contact_names']) < data['file_change_count']:
            await bot.send_message(message.chat.id, f'Masukkan nama kontak berikutnya ({len(data["contact_names"]) + 1} dari {data["file_change_count"]}):')
        else:
            await bot.send_message(message.chat.id, 'Masukkan jumlah kontak per file:')
            await bot.set_state(message.from_user.id, Convert2State.totalc, message.chat.id)

    except Exception as e:
        logging.error("Error in contact_names_get: ", exc_info=True)

@bot.message_handler(state=Convert2State.totalc, is_digit=True)
async def totalc_get(message: Message):
    try:
        await bot.send_message(message.chat.id, f'Jumlah kontak per file diatur menjadi: {message.text}. Silakan masukkan jumlah file:')
        await bot.set_state(message.from_user.id, Convert2State.totalf, message.chat.id)
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['totalc'] = int(message.text)

    except Exception as e:
        logging.error("error: ", exc_info=True)

@bot.message_handler(state=Convert2State.totalf, is_digit=True)
async def totalf_get(message: Message):
    try:
        await bot.send_message(message.chat.id, f'Jumlah file diatur menjadi: {message.text}. Mulai mengonversi...')
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['totalf'] = int(message.text)

            # Logging sebelum konversi
            logging.info(f"Memulai konversi untuk {data['totalf']} file, dengan jumlah kontak per file: {data['totalc']}")
            
            vcf_files = convert2(data)  # Pastikan ini adalah fungsi yang benar dari helpers.py

            os.remove(data['filename'])

            for file in vcf_files:
                if os.path.exists(file):  # Cek apakah file ada
                    try:
                        await bot.send_document(message.chat.id, open(file, 'rb'))
                        os.remove(file)  # Hapus file setelah berhasil dikirim
                    except ApiTelegramException as e:
                        if "Too Many Requests" in e.description:
                            delay = int(findall('\d+', e.description)[0])
                            logging.info(f"Too many requests, delaying for {delay} seconds.")
                            await sleep(delay)
                        else:
                            logging.error("Telegram API error: ", exc_info=True)
                    except Exception as e:
                        logging.error("Error sending document: ", exc_info=True)
                else:
                    logging.error(f"File tidak ditemukan: {file}")  # Log jika file tidak ada

            await bot.send_message(message.chat.id, "Convert selesai!")
        await bot.delete_state(message.from_user.id, message.chat.id)

    except Exception as e:
        logging.error("error: ", exc_info=True)

@bot.message_handler(state=Convert2State.totalc, is_digit=False)
@bot.message_handler(state=Convert2State.totalf, is_digit=False)
async def invalid_input(message: Message):
    try:
        await bot.send_message(message.chat.id, 'Masukkan angka yang valid.')
    except Exception as e:
        logging.error("error: ", exc_info=True)
