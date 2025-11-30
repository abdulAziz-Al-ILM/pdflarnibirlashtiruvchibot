import os
import shutil
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from pypdf import PdfWriter
import asyncio

# --- SOZLAMALAR ---
# Railway Environment variablesdan TOKENni oladi
# Agar lokalda ishlatsangiz, tokeningizni shu yerga yozing, lekin Railwayda ENV ga yozgan ma'qul.
BOT_TOKEN = os.getenv("BOT_TOKEN") 

# Fayllar vaqtinchalik saqlanadigan joy
DOWNLOAD_PATH = "downloads"

# Loglarni yoqish
logging.basicConfig(level=logging.INFO)

# Bot va Dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- YORDAMCHI FUNKSIYALAR ---

def get_user_dir(user_id):
    """Foydalanuvchi uchun shaxsiy papka yo'lini qaytaradi."""
    return os.path.join(DOWNLOAD_PATH, str(user_id))

def clear_user_data(user_id):
    """Foydalanuvchining vaqtinchalik fayllarini o'chiradi."""
    path = get_user_dir(user_id)
    if os.path.exists(path):
        shutil.rmtree(path)

# --- HANDLERLAR (BOT BUYRUQLARI) ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Start bosilganda ishlaydi."""
    user_id = message.from_user.id
    clear_user_data(user_id) # Eski fayllarni tozalash
    
    await message.answer(
        "Assalomu alaykum! Menga PDF fayllarni birin-ketin yuboring.\n\n"
        "1. Fayllarni yuboring (30 tagacha).\n"
        "2. Barchasini yuborib bo'lgach, **/birlashtir** buyrug'ini bosing."
    )

@dp.message(F.document)
async def handle_document(message: types.Message):
    """PDF fayllarni qabul qilish."""
    if not message.document.file_name.lower().endswith('.pdf'):
        await message.answer("Iltimos, faqat PDF formatidagi fayllarni yuboring.")
        return

    user_id = message.from_user.id
    user_dir = get_user_dir(user_id)
    
    # Papka yo'q bo'lsa yaratamiz
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    # Fayl nomini olamiz (takrorlanmasligi uchun file_id dan foydalanish mumkin, 
    # lekin tartib muhim bo'lsa, vaqtni qo'shamiz yoki shu holda saqlaymiz)
    file_id = message.document.file_id
    file_name = message.document.file_name
    
    # Faylni yuklab olish
    file = await bot.get_file(file_id)
    file_path = os.path.join(user_dir, file_name)
    
    # Agar fayl nomi bir xil bo'lsa, ustiga yozilib ketmasligi uchun oldiga raqam qo'shamiz
    counter = 1
    while os.path.exists(file_path):
        name, ext = os.path.splitext(file_name)
        file_path = os.path.join(user_dir, f"{name}_{counter}{ext}")
        counter += 1

    await bot.download_file(file.file_path, file_path)
    
    # Foydalanuvchiga xabar (qancha fayl yig'ilganini aytish mumkin)
    count = len(os.listdir(user_dir))
    await message.answer(f"✅ Qabul qilindi! Jami fayllar: {count} ta.\nDavom eting yoki /birlashtir ni bosing.")

@dp.message(Command("birlashtir"))
async def merge_pdfs(message: types.Message):
    """Fayllarni birlashtirib yuborish."""
    user_id = message.from_user.id
    user_dir = get_user_dir(user_id)

    if not os.path.exists(user_dir) or not os.listdir(user_dir):
        await message.answer("Siz hali hech qanday PDF fayl yubormadingiz.")
        return

    status_msg = await message.answer("⏳ Fayllar birlashtirilmoqda, kuting...")

    try:
        # Fayllarni ro'yxatga olish va saralash (OS ga qarab tartibsiz bo'lishi mumkin, shuning uchun sort qilamiz)
        # Agar foydalanuvchi yuborgan ketma-ketlik muhim bo'lsa, fayl nomiga vaqt tamg'asi qo'shish kerak edi,
        # lekin oddiy holatda nom bo'yicha saralaymiz.
        files = sorted([os.path.join(user_dir, f) for f in os.listdir(user_dir) if f.endswith('.pdf')])
        
        merger = PdfWriter()

        for pdf in files:
            merger.append(pdf)

        output_path = os.path.join(user_dir, "birlashtirilgan_hujjat.pdf")
        merger.write(output_path)
        merger.close()

        # Tayyor faylni yuborish
        result_file = FSInputFile(output_path)
        await message.answer_document(result_file, caption="Mana faylingiz tayyor! 😊")
        
        # Tugagach tozalash
        await status_msg.delete()
        clear_user_data(user_id)

    except Exception as e:
        await message.answer(f"Xatolik yuz berdi: {str(e)}")
        logging.error(f"Error merging files for {user_id}: {e}")

@dp.message(Command("tozalash"))
async def clear_files(message: types.Message):
    """Bekor qilish va tozalash."""
    user_id = message.from_user.id
    clear_user_data(user_id)
    await message.answer("Barcha yuklangan fayllar o'chirildi. Yangidan boshlashingiz mumkin.")

async def main():
    print("Bot ishga tushdi...")
    # Downloads papkasini yaratib qo'yish
    if not os.path.exists(DOWNLOAD_PATH):
        os.makedirs(DOWNLOAD_PATH)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
