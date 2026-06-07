import asyncio
from screenshot_helper import ScreenshotHelper

async def test():
    helper = ScreenshotHelper()
    await helper.start()

    success_tg = await helper.take_screenshot(
        'https://t.me/osomospolytech/663',
        'test_tg.png',
        'telegram'
    )
    print(f"Telegram: {'' if success_tg else ''}")

    success_vk = await helper.take_screenshot(
        'https://vk.com/wall-145727260_5935',
        'test_vk.png',
        'vk'
    )
    print(f"VK: {'' if success_vk else ''}")

    await helper.stop()

if __name__ == '__main__':
    asyncio.run(test())
