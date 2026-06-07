# bot_search — поиск по VK и Telegram

Telegram-бот (aiogram) для поиска и парсинга информации в VK и Telegram с возможностью делать скриншоты и выгружать результаты в Excel.

## Файлы

- `bot.py` — точка входа: бот, диалоговые состояния, выгрузка в Excel.
- `vk_parser.py` — парсер VK.
- `tg_parser.py` — парсер Telegram.
- `screenshot_helper.py` — создание скриншотов.
- `debug_telegram.py`, `test.py` — отладочные/тестовые скрипты.

## Технологии

aiogram 3, парсеры VK/Telegram, openpyxl (вставка изображений), Selenium/скриншоты.

## Запуск

```bash
pip install aiogram openpyxl python-dotenv
# плюс зависимости парсеров/скриншотов (selenium и т.п.)
# задайте токен бота и параметры доступа через .env
python bot.py
```

## Замечания

- Отладочные изображения (`debug_*.png`, `test_*.png`) и `debug_telegram.html` исключены из набора.
- Парсинг соцсетей должен соответствовать их правилам и законодательству.


## Зависимости

Зависимости проекта вынесены в `requirements.txt`. Установка:

```bash
pip install -r requirements.txt
```
