from actions.base import linkednController
# from actions.scroll import Scroll
# from actions.scrollcomments import Scroll_comment
from actions.login import loginAcct
# from actions.interactions import Interact
# from actions.shill import Shill
import asyncio
import json
import logging
import random
import pandas as pd
from pathlib import Path
from playwright.async_api import Playwright, async_playwright, expect


# random delay time using uniform, so it uses floats instead of int to simulate human randomness
delay = random.uniform(3, 7)
short_delay = random.uniform(2, 4)


async def navigate():
    async with async_playwright() as p:
        # browser configs
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},  # mimic Macbook air viewport size
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 12_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Safari/605.1.15"
        )
        # Load the CSV file into a DataFrame
        # df = pd.read_csv('data.csv')

        page = await context.new_page()
        page.set_default_timeout(155000)

        controller = linkednController()
        controller.add_command(loginAcct(page, context, "https://www.linkedin.com"))
        await controller.execute_commands()

        controller.clear_commands()

        await page.close()
        await context.close()


if __name__ == "__main__":
    asyncio.run(navigate())
