import logging
from telebot.types import Message
from bot import bot
from message import wifiwps_wpa
from helpers import exploit_wifi_wps
from state import WiFiWpsWpaState

# Handler untuk perintah /wifiwps
@bot.message_handler(commands=['wifiwps'])
async def wifi_wps_command(message: Message):
    try:
        logging.info(f"User {message.from_user.id} memulai perintah /wifiwps")
        await bot.set_state(message.from_user.id, WiFiWpsWpaState.waiting_for_interface, message.chat.id)
        await bot.reply_to(message, wifiwps_wpa)
    except Exception as e:
        logging.error("Error in wifi_wps_command: ", exc_info=True)

# Handler untuk input interface
@bot.message_handler(state=WiFiWpsWpaState.waiting_for_interface)
async def handle_interface(message: Message):
    try:
        interface = message.text
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['interface'] = interface
        logging.info(f"Interface diterima: {interface}")
        await bot.set_state(message.from_user.id, WiFiWpsWpaState.waiting_for_bssid, message.chat.id)
        await bot.send_message(message.chat.id, "Masukkan BSSID target (misalnya: 00:11:22:33:44:55).")
    except Exception as e:
        logging.error("Error in handle_interface: ", exc_info=True)

# Handler untuk input BSSID
@bot.message_handler(state=WiFiWpsWpaState.waiting_for_bssid)
async def handle_bssid(message: Message):
    try:
        bssid = message.text
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['bssid'] = bssid
        logging.info(f"BSSID diterima: {bssid}")
        await bot.set_state(message.from_user.id, WiFiWpsWpaState.waiting_for_channel, message.chat.id)
        await bot.send_message(message.chat.id, "Masukkan channel (misalnya: 6).")
    except Exception as e:
        logging.error("Error in handle_bssid: ", exc_info=True)

# Handler untuk input channel
@bot.message_handler(state=WiFiWpsWpaState.waiting_for_channel)
async def handle_channel(message: Message):
    try:
        channel = message.text
        async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            interface = data['interface']
            bssid = data['bssid']
        
        # Jalankan exploit WiFi WPS/WPA
        result = exploit_wifi_wps(interface, bssid, channel)
        
        logging.info(f"Exploit result for {bssid}: {result}")
        
        # Kirim hasil ke pengguna
        await bot.send_message(
            message.chat.id, 
            f"Nama WiFi: {result['ssid']}\nPIN: {result['pin']}\nPassword: {result['password']}\nKeamanan: {result['security']}\nKelemahan: {result['weakness']}"
        )
        
        await bot.delete_state(message.from_user.id, message.chat.id)
    except Exception as e:
        logging.error("Error in handle_channel: ", exc_info=True)
        await bot.send_message(message.chat.id, "Terjadi kesalahan saat mencoba mengeksploitasi jaringan.")
