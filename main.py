import asyncio

from bot import bot
from commands import *
from message import *
from handlers import *

async def main():
  await set_commands()
  await bot.infinity_polling()


print("BOT IS RUNNING")
asyncio.run(main())
