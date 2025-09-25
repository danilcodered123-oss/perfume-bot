# Perfume Bot (Render-ready)

Этот архив содержит готовый Telegram-бот-магазин духов. Проект подготовлен для запуска на Render.com.

## Что включено
- Товары: `data/products.json`
- Изображения: `images/` (извлечены из твоего `прайс.xlsx`)
- `bot.py` — основной код (каталог, корзина, оплата, уведомление админу)
- `config.py` — настройки (вставь свой BOT_TOKEN)
- `requirements.txt` — зависимости
- `Procfile` — для Render (worker)

## Быстрая инструкция по деплою на Render
1. Создай репозиторий на GitHub и залей все файлы из архива.
2. В Render Dashboard нажми **New → Web Service** и подключи репозиторий.
3. В настройках сервиса укажи:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: (не обязательно если Procfile) оставить пустым или `python bot.py`
4. В **Environment** добавь переменную:
   - `BOT_TOKEN` — токен от BotFather
5. Нажми **Create Web Service** или **Manual Deploy**.

## Примечание по безопасности
Ваш BOT_TOKEN храните в секрете. Не публикуйте токен в открытых репозиториях.

## Как изменить номер карты или ADMIN_ID
Отредактируйте файл `config.py`.
