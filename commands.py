from bot import bot
from telebot.types import BotCommand

async def set_commands():
  await bot.delete_my_commands(scope=None, language_code=None)
  await bot.set_my_commands(
    commands=[
      BotCommand('convert', 'Mengonversi file dari format TXT ke VCF'),
      BotCommand('convert2', 'Mengonversi file dari format TXT ke VCF dengan nama file yang berbeda'),
      BotCommand('pecahvcf', 'Membagi satu file VCF menjadi beberapa file'),
      BotCommand('pecahtxt', 'Membagi satu file TXT menjadi beberapa file'),
      BotCommand('convertxlsx', 'Mengonversi file dari format XLSX ke TXT'),
      BotCommand('convertvcf', 'Mengonversi file dari format XLSX ke VCF'),
      BotCommand('convertvcf_to_txt', 'mengonversi file dari format vcf ke txt'),
      BotCommand('gabungvcf', 'Menggabungkan beberapa file vcf menjadi 1'),
      BotCommand('chattotxt', 'Mengonversi chat ke txt '),
      BotCommand('wifiwps', 'mengekploitasi jaringan wifi '),
      BotCommand('gabungtxt', 'Menggabungkan beberapa file txt menjadi 1'),
      BotCommand('hapuss', 'menghapus awalan + dan spasi'),
      BotCommand('1kolom', 'menggabung file txt. beberapa kolom menjadi 1 kolom'),
      BotCommand('count_contacts', 'menghitung CTC atau Kontak'),
      BotCommand('extractimages', 'untuk mengambil gambar di xlsx'),
      BotCommand('cancel', 'Membatalkan proses'),
      
    ],
  )
