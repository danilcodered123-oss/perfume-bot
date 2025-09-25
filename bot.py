import os, asyncio, logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
import openpyxl
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ADMIN_IDS = [589839267]
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    print("Warning: BOT_TOKEN not set. Running in local test mode.")
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher()

DATA_XLSX = Path("data/price.xlsx")
IMAGES_DIR = Path("images")

def load_items():
    wb = openpyxl.load_workbook(DATA_XLSX)
    ws = wb.active
    items = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        image_file, name, price = row
        items.append({"image_file": image_file or "", "name": name or "", "price": price or ""})
    return items

items_cache = load_items()

MAIN_MENU = types.ReplyKeyboardMarkup(keyboard=[
    [types.KeyboardButton("🛍 Каталог"), types.KeyboardButton("💎 Прайс")],
    [types.KeyboardButton("💳 Оплата и доставка"), types.KeyboardButton("📞 Поддержка")],
    [types.KeyboardButton("↩️ Назад"), types.KeyboardButton("❌ Выйти")]
], resize_keyboard=True)

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("🌸 Добро пожаловать в La Maison Parfum!\nВыберите действие:", reply_markup=MAIN_MENU)

@dp.message(Text(equals="🛍 Каталог"))
async def catalog_cmd(message: types.Message):
    # show first item
    if not items_cache:
        await message.answer("Каталог пуст.")
        return
    item = items_cache[0]
    img_path = IMAGES_DIR / item['image_file'] if item['image_file'] else None
    caption = f"**{item['name']}**\nЦена: {item['price']}"
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton('🛒 Купить', callback_data='buy:0'), InlineKeyboardButton('➡️ Вперёд', callback_data='next:0'))
    if img_path and img_path.exists():
        await message.answer_photo(photo=img_path.open('rb'), caption=caption, reply_markup=kb, parse_mode='Markdown')
    else:
        await message.answer(caption, reply_markup=kb, parse_mode='Markdown')

@dp.callback_query()
async def cb_handler(cb: types.CallbackQuery):
    data = cb.data or ''
    if data.startswith('next:'):
        idx = int(data.split(':',1)[1]) + 1
        if idx >= len(items_cache):
            await cb.answer('Это последний товар', show_alert=True)
            return
        item = items_cache[idx]
        img_path = IMAGES_DIR / item['image_file'] if item['image_file'] else None
        caption = f"**{item['name']}**\nЦена: {item['price']}"
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton('🛒 Купить', callback_data=f'buy:{idx}'), InlineKeyboardButton('⬅️ Назад', callback_data=f'prev:{idx}'), InlineKeyboardButton('➡️ Вперёд', callback_data=f'next:{idx}'))
        try:
            if img_path and img_path.exists():
                # edit message with media might fail; safer to send new photo
                await cb.message.answer_photo(photo=img_path.open('rb'), caption=caption, reply_markup=kb, parse_mode='Markdown')
            else:
                await cb.message.answer(caption, reply_markup=kb, parse_mode='Markdown')
        except Exception as e:
            await cb.message.answer(caption, reply_markup=kb, parse_mode='Markdown')
        await cb.answer()
    elif data.startswith('prev:'):
        idx = int(data.split(':',1)[1]) - 1
        if idx < 0:
            await cb.answer('Это первый товар', show_alert=True)
            return
        item = items_cache[idx]
        img_path = IMAGES_DIR / item['image_file'] if item['image_file'] else None
        caption = f"**{item['name']}**\nЦена: {item['price']}"
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton('🛒 Купить', callback_data=f'buy:{idx}'), InlineKeyboardButton('⬅️ Назад', callback_data=f'prev:{idx}'), InlineKeyboardButton('➡️ Вперёд', callback_data=f'next:{idx}'))
        try:
            if img_path and img_path.exists():
                await cb.message.answer_photo(photo=img_path.open('rb'), caption=caption, reply_markup=kb, parse_mode='Markdown')
            else:
                await cb.message.answer(caption, reply_markup=kb, parse_mode='Markdown')
        except Exception:
            await cb.message.answer(caption, reply_markup=kb, parse_mode='Markdown')
        await cb.answer()
    elif data.startswith('buy:'):
        idx = int(data.split(':',1)[1])
        item = items_cache[idx]
        await cb.message.answer(f"Вы выбрали покупку: {item['name']} — {item['price']}. Напишите в поддержку для оформления.")
        await cb.answer('Добавлено')
    else:
        await cb.answer()

@dp.message(Text(equals='💎 Прайс'))
async def price_cmd(message: types.Message):
    if not items_cache:
        await message.answer('Прайс пуст.')
        return
    lines = []
    for it in items_cache:
        lines.append(f"{it['name']} — {it['price']}")
    await message.answer('💎 Прайс-лист:\n' + '\n'.join(lines))

@dp.message(Text(equals='💳 Оплата и доставка'))
async def pay_cmd(message: types.Message):
    await message.answer('Оплата: перевод на карту, QIWI. Доставка: по России курьером.')

@dp.message(Text(equals='📞 Поддержка'))
async def support_cmd(message: types.Message):
    await message.answer('Напишите ваше сообщение, и администратор получит его.')

@dp.message(Text(equals='❌ Выйти'))
async def exit_cmd(message: types.Message):
    await message.answer('Выход. Чтобы вернуться — /start', reply_markup=types.ReplyKeyboardRemove())

async def main():
    print('Bot starting...')
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
