import logging
from bot import *
from message import *

@bot.message_handler(commands='start')
async def send_welcome(message):
  try:
    await bot.reply_to(message, txt_start)
  except Exception as e:
    logging.error("error: ", exc_info=True)

@bot.message_handler(state="*", commands=['cancel'])
async def any_state(message):
  await bot.send_message(message.chat.id, "Proses dibatalkan.")
  await bot.delete_state(message.from_user.id, message.chat.id)
