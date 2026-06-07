import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

async def debug_telegram():
    """Детальная диагностика Telegram скриншотов"""

    url = 'https://t.me/osomospolytech/663'

    async with async_playwright() as p:

        print("Запуск браузера в видимом режиме...")
        browser = await p.chromium.launch(
            headless=False,
            args=['--no-sandbox']
        )

        context = await browser.new_context(
            viewport={'width': 1200, 'height': 1200},
            locale='ru-RU',
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        page = await context.new_page()

        print(f"Загрузка: {url}")

        try:

            response = await page.goto(url, wait_until='networkidle', timeout=30000)
            print(f"Статус ответа: {response.status}")

            await asyncio.sleep(3)

            html_content = await page.content()
            Path('debug_telegram.html').write_text(html_content, encoding='utf-8')
            print(f"HTML сохранён в debug_telegram.html")

            await page.screenshot(path='debug_full_page.png', full_page=True)
            print(f"Полный скриншот сохранён: debug_full_page.png")

            selectors_to_check = [
                '.tgme_widget_message_bubble',
                '.tgme_widget_message',
                '.tgme_widget_message_wrap',
                '.tgme_page',
                '.tgme_page_widget',
                'div[class*="tgme"]',
                '.tgme_widget_message_text',
                'article',
                '[data-post]'
            ]

            print("\nПроверка селекторов:")
            found_selectors = []

            for selector in selectors_to_check:
                try:
                    elements = await page.query_selector_all(selector)
                    count = len(elements)
                    if count > 0:
                        print(f"  {selector}: найдено {count} элементов")
                        found_selectors.append(selector)

                        if elements[0]:
                            try:
                                await elements[0].screenshot(
                                    path=f'debug_element_{selector.replace(".", "_").replace("[", "").replace("]", "")}.png')
                                print(f"     Скриншот элемента сохранён")
                            except Exception as e:
                                print(f"     Не удалось сделать скриншот: {e}")
                    else:
                        print(f"  {selector}: не найден")
                except Exception as e:
                    print(f"  {selector}: ошибка - {e}")

            body_text = await page.text_content('body')
            if body_text and len(body_text) > 100:
                print(f"\nНайден текст на странице ({len(body_text)} символов)")
                print(f"   Первые 200 символов: {body_text[:200]}")
            else:
                print(f"\nМало текста на странице")

            page.on('console', lambda msg: print(f"Console: {msg.text}"))
            page.on('pageerror', lambda err: print(f"JS Error: {err}"))

            print(f"\nНайдено рабочих селекторов: {len(found_selectors)}")
            if found_selectors:
                print(f"   Рекомендуемый: {found_selectors[0]}")

        except Exception as e:
            print(f"Критическая ошибка: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await asyncio.sleep(2)
            await browser.close()
            print("\nДиагностика завершена")

if __name__ == '__main__':
    asyncio.run(debug_telegram())
