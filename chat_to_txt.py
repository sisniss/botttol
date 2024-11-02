import os
import logging
from telebot.types import Message

from bot import bot
from message import txt_chat_to_txt
from helpers import save_txt
from state import ChatToTxtState

# Pastikan direktori untuk menyimpan file ada
if not os.path.exists('files'):
    os.makedirs('files')

# Handler untuk perintah /chattotxt
@bot.message_handler(commands=['chattotxt'])
async def chat_to_txt_command(message: Message):
    try:
        logging.info(f"User {message.from_user.id} memulai perintah /chattotxt")
        await bot.delete_state(message.from_user.id, message.chat.id)
        await bot.set_state(message.from_user.id, ChatToTxtState.waiting_for_text_input, message.chat.id)
        await bot.reply_to(message, txt_chat_to_txt)
    except Exception as e:
        logging.error("Error in chat_to_txt_command: ", exc_info=True)

# Handler untuk menerima input teks
@bot.message_handler(state=ChatToTxtState.waiting_for_text_input)
async def handle_text_input(message: Message):
    try:
        input_text = message.text
        
        if input_text.lower() == '/done':
            # Handle jika user mengetik /done
            await handle_done_txt(message)
        else:
            logging.info(f"Teks diterima dari user {message.from_user.id}: {input_text}")
            
            async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                # Append teks baru ke data sebelumnya jika ada
                if 'input_text' in data:
                    data['input_text'] += f"\n{input_text}"
                else:
                    data['input_text'] = input_text
            
            await bot.send_message(message.chat.id, 'Teks ditambahkan. Ketik /done jika sudah selesai menambah teks.')
    except Exception as e:
        logging.error("Error in handle_text_input: ", exc_info=True)

# Fungsi untuk menangani jika user mengetik /done
async def handle_done_txt(message: Message):
    try:
        logging.info(f"Command /done diterima dari user {message.from_user.id}")
        
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            input_text = data.get('input_text', '')

            if not input_text:
                logging.warning(f"Tidak ada teks yang ditemukan untuk user {message.from_user.id}")
                return await bot.send_message(message.chat.id, "Tidak ada teks yang ditemukan. Silakan tambahkan teks.")

            # Nama file bisa diambil dari id pengguna atau waktu input untuk membuatnya unik
            txt_filename = f"chat_{message.from_user.id}.txt"
            file_path = save_txt(input_text, txt_filename)

            logging.info(f"File TXT {txt_filename} berhasil dibuat untuk user {message.from_user.id}")

            await bot.send_message(message.chat.id, f'File TXT berhasil dibuat dengan nama: {txt_filename}')

            # Kirim file TXT ke user
            with open(file_path, 'rb') as doc:
                await bot.send_document(message.chat.id, doc)

            # Hapus file lokal setelah dikirim
            os.remove(file_path)
            logging.info(f"File {txt_filename} dihapus dari server.")
            
            await bot.delete_state(message.from_user.id, message.chat.id)
            logging.info(f"State dihapus untuk user {message.from_user.id}")
    except Exception as e:
        logging.error("Error in handle_done_txt: ", exc_info=True)
        await bot.send_message(message.chat.id, "Terjadi kesalahan saat membuat file TXT.")
