import asyncio
from playwright.async_api import async_playwright, Error as PlaywrightError
from pathlib import Path
import random

class ScreenshotHelper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.is_available = False

    async def check_availability(self):
        """Проверка доступности Playwright"""
        try:
            pw = await async_playwright().start()
            browser = await pw.chromium.launch(headless=True)
            await browser.close()
            await pw.stop()
            self.is_available = True
            return True
        except PlaywrightError as e:
            error_msg = str(e)
            if "Executable doesn't exist" in error_msg:
                print("Playwright браузеры не установлены!")
                print("Выполните команду: playwright install chromium")
            else:
                print(f"Ошибка Playwright: {e}")
            self.is_available = False
            return False
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            self.is_available = False
            return False

    async def start(self):
        """Запуск браузера с оптимизированными настройками"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--lang=ru-RU'
                ]
            )
            self.is_available = True
            return True
        except PlaywrightError as e:
            print(f"Не удалось запустить браузер: {e}")
            self.is_available = False
            return False
        except Exception as e:
            print(f"Критическая ошибка запуска: {e}")
            self.is_available = False
            return False

    async def stop(self):
        """Остановка браузера"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Ошибка при остановке браузера: {e}")

    async def take_screenshot_telegram(self, page, url):
        """
        Telegram скриншоты с расширенной обработкой
        """
        try:

            await page.goto(url, wait_until='domcontentloaded', timeout=45000)

            await asyncio.sleep(4)

            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(1.5)
            await page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(1.5)

            tg_selectors = [
                '.tgme_widget_message_wrap',
                '.tgme_widget_message',
                'div[class*="tgme_widget"]',
                '.tgme_page_widget_description',
                'article.tgme_widget_message',
                '.tgme_channel_info_description'
            ]

            element = None
            successful_selector = None

            for selector in tg_selectors:
                try:
                    element = await page.wait_for_selector(
                        selector,
                        timeout=8000,
                        state='visible'
                    )
                    if element:
                        successful_selector = selector
                        print(f"   TG: Найден селектор '{selector}'")
                        break
                except Exception as e:
                    print(f"   TG: Селектор '{selector}' не найден")
                    continue

            if element:
                await element.scroll_into_view_if_needed()
                await asyncio.sleep(0.7)

                bbox = await element.bounding_box()

                if bbox:
                    padding = 15
                    screenshot_bytes = await page.screenshot(
                        type='png',
                        clip={
                            'x': max(0, bbox['x'] - padding),
                            'y': max(0, bbox['y'] - padding),
                            'width': min(bbox['width'] + (padding * 2), 1200),
                            'height': min(bbox['height'] + (padding * 2), 1800)
                        }
                    )
                else:
                    screenshot_bytes = await element.screenshot(type='png')

                return screenshot_bytes

            print(f"   TG: Элемент не найден, делаю общий скриншот")
            screenshot_bytes = await page.screenshot(type='png', full_page=False)
            return screenshot_bytes

        except asyncio.TimeoutError:
            print(f"   TG: Timeout {url[:50]}")

            try:
                screenshot_bytes = await page.screenshot(type='png', full_page=False)
                return screenshot_bytes
            except:
                return None

        except Exception as e:
            print(f"   TG: {str(e)[:60]}")
            return None

    async def take_screenshot_vk_with_retry(self, page, url, max_retries=3):
        """
        VK с механизмом повторных попыток и увеличенными таймаутами
        """
        for attempt in range(max_retries):
            try:

                await page.goto(url, wait_until='domcontentloaded', timeout=45000)

                await asyncio.sleep(3 + random.uniform(0.5, 1.5))

                await page.evaluate('window.scrollTo(0, 600)')
                await asyncio.sleep(1)
                await page.evaluate('window.scrollTo(0, 0)')
                await asyncio.sleep(1.5)

                vk_selectors = [
                    '.wall_post_cont',
                    '.post',
                    '.wall_item',
                    'div[class*="wall_post"]',
                    '.post_content'
                ]

                element = None
                for selector in vk_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=5000, state='visible')
                        if element:
                            break
                    except:
                        continue

                if element:
                    await element.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)

                    bbox = await element.bounding_box()

                    if bbox:
                        padding = 20
                        screenshot_bytes = await page.screenshot(
                            type='png',
                            clip={
                                'x': max(0, bbox['x'] - padding),
                                'y': max(0, bbox['y'] - padding),
                                'width': min(bbox['width'] + (padding * 2), 1400),
                                'height': min(bbox['height'] + (padding * 2), 2000)
                            }
                        )
                        return screenshot_bytes
                    else:
                        screenshot_bytes = await element.screenshot(type='png')
                        return screenshot_bytes

                screenshot_bytes = await page.screenshot(type='png', full_page=False)
                return screenshot_bytes

            except asyncio.TimeoutError:
                print(f"   VK timeout попытка {attempt + 1}/{max_retries}")

                if attempt < max_retries - 1:

                    wait_time = 3 * (attempt + 1)
                    print(f"   Ждём {wait_time} сек перед повтором...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"   VK: все попытки исчерпаны")
                    return None

            except Exception as e:
                print(f"   VK ошибка попытка {attempt + 1}: {str(e)[:50]}")

                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    return None

        return None

    async def take_screenshot_vk(self, page, url):
        """
        Обёртка для VK с retry
        """
        return await self.take_screenshot_vk_with_retry(page, url, max_retries=2)

    async def take_screenshot(self, url, output_path, platform='vk'):
        """
        Создание скриншота с улучшенной обработкой ошибок
        """
        if not self.is_available or not self.browser:
            return False

        context = None
        try:

            context = await self.browser.new_context(
                viewport={
                    'width': 1000,
                    'height': 1400
                },
                device_scale_factor=1,
                locale='ru-RU',
                timezone_id='Europe/Moscow',
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                extra_http_headers={
                    'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
                    'Accept': 'text/html,application/xhtml+xml',
                }
            )

            page = await context.new_page()
            page.set_default_timeout(50000)

            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            await page.route("**/*", lambda route: (
                route.abort() if (
                        route.request.resource_type == "font" or
                        (route.request.resource_type == "stylesheet" and platform == 'vk')
                )
                else route.continue_()
            ))

            if platform == 'telegram':
                screenshot_data = await self.take_screenshot_telegram(page, url)
            else:
                screenshot_data = await self.take_screenshot_vk(page, url)

            await context.close()

            if screenshot_data:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, 'wb') as f:
                    f.write(screenshot_data)

                return True

            return False

        except asyncio.TimeoutError:
            print(f"Timeout: {url[:60]}")
            if context:
                await context.close()
            return False
        except Exception as e:
            print(f"Error {url[:50]}: {str(e)[:60]}")
            if context:
                try:
                    await context.close()
                except:
                    pass
            return False

    async def take_screenshots_batch(self, posts, output_dir='screenshots', max_concurrent=1, enable_vk=True):
        """
        Пакетное создание с МИНИМАЛЬНЫМ параллелизмом для VK

        Args:
            enable_vk: если False, пропускает VK скриншоты
        """
        if not self.is_available:
            print("Скриншоты недоступны")
            return {}

        Path(output_dir).mkdir(exist_ok=True)

        results = {}

        semaphore = asyncio.Semaphore(max_concurrent)

        completed = 0
        total = len(posts)
        vk_count = sum(1 for p in posts if p['platform'] == 'vk')
        tg_count = total - vk_count

        print(f"\nК обработке: {total} постов (VK: {vk_count}, TG: {tg_count})")
        if not enable_vk:
            print(f"VK скриншоты отключены\n")

        async def process_one(post):
            nonlocal completed
            async with semaphore:
                index = post['index']
                platform = post['platform']
                url = post['link']

                if platform == 'vk' and not enable_vk:
                    completed += 1
                    print(f"⊘ [{completed}/{total}] VK пропущен (отключено): {url[:45]}")
                    return False

                filename = f"{output_dir}/post_{index}.png"

                success = await self.take_screenshot(url, filename, platform)

                completed += 1

                if success:
                    results[index] = filename
                    print(f"[{completed}/{total}] {platform.upper()}: {url[:50]}")
                else:
                    print(f"[{completed}/{total}] Пропущен: {url[:50]}")

                if platform == 'vk':
                    delay = random.uniform(2.0, 4.0)
                else:
                    delay = random.uniform(0.5, 1.5)

                await asyncio.sleep(delay)

                return success

        tasks = [process_one(post) for post in posts]
        await asyncio.gather(*tasks, return_exceptions=True)

        print(f"\nИтого скриншотов: {len(results)}/{total}")
        print(f"   Успешно: {len(results)}")
        print(f"   Ошибки: {total - len(results)}")

        return results
