import logging, json, os, asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from pathlib import Path
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = config.BOT_TOKEN
ADMIN_ID = config.ADMIN_ID
CARD_NUMBER = config.CARD_NUMBER

if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
    logger.warning("BOT_TOKEN not set in config.py. Please add your token before running on Render.")

bot = Bot(token=BOT_TOKEN) if BOT_TOKEN and BOT_TOKEN != "YOUR_BOT_TOKEN_HERE" else None
dp = Dispatcher()

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "products.json"
IMAGES_DIR = BASE_DIR / "images"

# load products
def load_products():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

PRODUCTS = load_products()

# simple in-memory carts: {user_id: [{index, name, price, image}]}
CARTS = {}

# Helpers
def format_price(p):
    return str(p)

def build_main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton('🛍 Каталог'), types.KeyboardButton('📋 Прайс'))
    kb.row(types.KeyboardButton('🧾 Корзина'), types.KeyboardButton('💳 Оплата'))
    kb.row(types.KeyboardButton('📞 Связаться с администратором'), types.KeyboardButton('❌ Выйти'))
    return kb

@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    await message.answer("🌸 Добро пожаловать в бутик духов!\nВыберите раздел:", reply_markup=build_main_menu())

@dp.message(Text(equals='🛍 Каталог'))
async def catalog_cmd(message: types.Message):
    if not PRODUCTS:
        await message.answer('Каталог пуст.')
        return
    # show first product (index 0)
    await send_product(message.chat.id, 0)

async def send_product(chat_id, index):
    if index < 0 or index >= len(PRODUCTS):
        return
    p = PRODUCTS[index]
    caption = f"**{p.get('name','')}**\nЦена: {p.get('price','')} ₽"
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton('🛒 В корзину', callback_data=f'add:{index}'))
    nav = []
    if index > 0:
        nav.append(InlineKeyboardButton('⬅️ Назад', callback_data=f'nav:{index-1}'))
    nav.append(InlineKeyboardButton('🔙 В меню', callback_data='menu'))
    if index < len(PRODUCTS)-1:
        nav.append(InlineKeyboardButton('Вперёд ➡️', callback_data=f'nav:{index+1}'))
    kb.row(*nav)
    img_path = IMAGES_DIR / p.get('image','')
    try:
        if img_path.exists():
            await (bot or message_bot()).send_photo(chat_id, InputFile(img_path), caption=caption, reply_markup=kb, parse_mode='Markdown')
        else:
            await (bot or message_bot()).send_message(chat_id, caption, reply_markup=kb, parse_mode='Markdown')
    except Exception as e:
        # fallback to message if photo fails
        await (bot or message_bot()).send_message(chat_id, caption, reply_markup=kb, parse_mode='Markdown')

# helper to create a dummy bot for local preview when BOT_TOKEN not set
def message_bot():
    class Dummy:
        async def send_message(self, chat_id, text, **kwargs):
            print(f"SEND MESSAGE to {chat_id}: {text[:80]}")
        async def send_photo(self, chat_id, photo, **kwargs):
            print(f"SEND PHOTO to {chat_id}: {photo}")
    return Dummy()

@dp.callback_query()
async def cb_handler(cb: types.CallbackQuery):
    data = cb.data or ''
    if data.startswith('add:'):
        idx = int(data.split(':',1)[1])
        user = cb.from_user.id
        CARTS.setdefault(user, []).append(PRODUCTS[idx])
        await cb.answer('Добавлено в корзину ✅', show_alert=False)
    elif data.startswith('nav:'):
        idx = int(data.split(':',1)[1])
        await send_product(cb.message.chat.id, idx)
        await cb.answer()
    elif data == 'menu':
        await cb.message.delete()
        await bot.send_message(cb.message.chat.id, 'Возврат в меню', reply_markup=build_main_menu())
        await cb.answer()
    else:
        await cb.answer()

@dp.message(Text(equals='📋 Прайс'))
async def price_cmd(message: types.Message):
    if not PRODUCTS:
        await message.answer('Прайс пуст.')
        return
    lines = [f"{i+1}. {p.get('name','')} — {p.get('price','')} ₽" for i,p in enumerate(PRODUCTS)]
    await message.answer('💎 Прайс-лист:\n' + '\n'.join(lines))

@dp.message(Text(equals='🧾 Корзина'))
async def cart_cmd(message: types.Message):
    user = message.from_user.id
    cart = CARTS.get(user, [])
    if not cart:
        await message.answer('Корзина пуста.')
        return
    lines = []
    total = 0
    for i, it in enumerate(cart):
        lines.append(f"{i+1}. {it.get('name','')} — {it.get('price','')} ₽")
        try:
            total += float(str(it.get('price','')).replace(',','.'))
        except Exception:
            pass
    kb = types.InlineKeyboardMarkup(row_width=2)
    # add delete buttons per item
    for i, it in enumerate(cart):
        kb.add(InlineKeyboardButton(f'Удалить {i+1}', callback_data=f'del:{i}'))
    kb.add(InlineKeyboardButton('✅ Оформить заказ', callback_data='checkout'))
    kb.add(InlineKeyboardButton('Очистить корзину', callback_data='clear'))
    await message.answer('🧾 Корзина:\n' + '\n'.join(lines) + f"\n\nИтого: {total} ₽", reply_markup=kb)

@dp.callback_query()
async def cart_callbacks(cb: types.CallbackQuery):
    data = cb.data or ''
    user = cb.from_user.id
    if data.startswith('del:'):
        idx = int(data.split(':',1)[1])
        cart = CARTS.get(user, [])
        if 0 <= idx < len(cart):
            removed = cart.pop(idx)
            await cb.answer(f'Удалено: {removed.get("name","")}', show_alert=False)
        await cb.message.delete()
        # re-show cart
        await cart_cmd(cb.message)
    elif data == 'clear':
        CARTS[user] = []
        await cb.message.edit_text('Корзина очищена.')
        await cb.answer()
    elif data == 'checkout':
        cart = CARTS.get(user, [])
        if not cart:
            await cb.answer('Корзина пуста', show_alert=True); return
        total = 0
        lines = []
        for it in cart:
            lines.append(f" - {it.get('name','')} — {it.get('price','')} ₽")
            try:
                total += float(str(it.get('price','')).replace(',','.'))
            except:
                pass
        # notify user with card info
        await cb.message.answer(f"💳 Для оплаты переведите {total} ₽ на карту:\n{CARD_NUMBER}\nПосле оплаты пришлите чек администратору.")
        # notify admin
        admin_text = f"🛒 Новый заказ от @{cb.from_user.username or cb.from_user.full_name}\n" + '\n'.join(lines) + f"\nИтого: {total} ₽"
        if bot:
            try:
                await bot.send_message(ADMIN_ID, admin_text)
            except Exception as e:
                print('Failed to send admin message', e)
        CARTS[user] = []  # clear cart after checkout
        await cb.answer('Заказ оформлен.')
    else:
        await cb.answer()

@dp.message(Text(equals='💳 Оплата'))
async def pay_info(message: types.Message):
    await message.answer(f"Оплата картой:\n{CARD_NUMBER}\nПожалуйста, отправьте чек в чат администратора после оплаты.")

@dp.message(Text(equals='📞 Связаться с администратором'))
async def contact_admin(message: types.Message):
    admin_link = f"tg://user?id={ADMIN_ID}"
    kb = types.InlineKeyboardMarkup().add(InlineKeyboardButton('Написать администратору', url=admin_link))
    await message.answer('Связаться с администратором:', reply_markup=kb)

@dp.message(Text(equals='❌ Выйти'))
async def exit_cmd(message: types.Message):
    await message.answer('Выход. Чтобы вернуться — /start', reply_markup=types.ReplyKeyboardRemove())

async def main():
    if bot:
        await dp.start_polling(bot)
    else:
        print('BOT_TOKEN not configured; running in dry mode (no Telegram).')
        while True:
            await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
