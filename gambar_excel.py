import logging
import os
from telebot.types import Message
from bot import bot
from helpers import extract_images_from_excel  # Update to the new helper function
from state import ConvertXlsImagesState

@bot.message_handler(commands='extractimages')
async def extractimages_command(message):
    try:
        await bot.delete_state(message.from_user.id, message.chat.id)
        await bot.set_state(message.from_user.id, ConvertXlsImagesState.filename, message.chat.id)
        await bot.reply_to(message, "Silakan kirim file .xls atau .xlsx yang akan diekstrak gambarnya.")
    except Exception as e:
        logging.error("Error in extractimages_command: ", exc_info=True)

@bot.message_handler(state=ConvertXlsImagesState.filename, content_types=['document'])
async def xls_get(message: Message):
    try:
        if not (message.document.file_name.endswith(".xls") or message.document.file_name.endswith(".xlsx")):
            return await bot.send_message(message.chat.id, "Kirim file .xls atau .xlsx")
        
        # Pastikan direktori 'files/' ada
        if not os.path.exists('files'):
            os.makedirs('files')

        file_info = await bot.get_file(message.document.file_id)
        filename = f"files/{message.document.file_name}"

        logging.info(f"File diterima: {filename}")
        
        # Download file dari Telegram
        try:
            downloaded_file = await bot.download_file(file_info.file_path)
            with open(filename, 'wb') as new_file:
                new_file.write(downloaded_file)
        except Exception as e:
            logging.error(f"Error saat mengunduh file: {e}")
            await bot.send_message(message.chat.id, "Gagal mengunduh file. Silakan coba lagi.")
            return

        # Proses ekstraksi gambar
        try:
            await bot.send_message(message.chat.id, "File diterima. Mengekstrak gambar...")
            image_paths = extract_images_from_excel(filename)  # Call the updated function
            
            if image_paths:
                for img_path in image_paths:
                    with open(img_path, 'rb') as img_file:
                        await bot.send_photo(message.chat.id, img_file)
                logging.info(f"{len(image_paths)} gambar berhasil diekstrak.")
            else:
                await bot.send_message(message.chat.id, "Tidak ada gambar ditemukan dalam file.")
                logging.info("Tidak ada gambar ditemukan dalam file.")
        except Exception as e:
            logging.error(f"Error saat mengekstrak gambar: {e}")
            await bot.send_message(message.chat.id, "Gagal mengekstrak gambar dari file.")
            return
        finally:
            # Hapus file setelah selesai
            os.remove(filename)
        
        await bot.send_message(message.chat.id, "Proses ekstraksi selesai.")
        await bot.delete_state(message.from_user.id, message.chat.id)
    except Exception as e:
        logging.error("Error in xls_get: ", exc_info=True)
