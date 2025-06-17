from scraper.actions.base import linkednController
import asyncio
import json
import random
import pandas as pd
from pathlib import Path
from .logger import setup_logger
from playwright.async_api import Playwright, async_playwright, expect


# random delay time using uniform, so it uses floats instead of int to simulate human randomness
delay = random.uniform(3, 7)
short_delay = random.uniform(2, 4)

logger = setup_logger("linkedn", "INFO")


async def navigate():
    async with async_playwright() as p:
        # browser configs
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(
            # viewport={"width": 414, "height": 896},  # iPhone 11 viewport size
            # user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
            viewport={"width": 1440, "height": 900},  # macbook air viewport size
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0",
            locale="en-NG",  # 'en-NG' for English in Nigeria
            timezone_id="Africa/Lagos",  # Lagos is the most common timezone for Nigeria, including Abuja
            color_scheme="light",
            permissions=[],
            extra_http_headers={
                "Accept-Language": "en-NG,en;q=0.9",  # Prioritize Nigerian English
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                # Consider adding a realistic User-Agent
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:134.0) Gecko/20100101 Firefox/134.0"

            }
        )

        # Disable webdriver detection
        await context.add_init_script(
            """
                delete navigator.__proto__.webdriver;
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3]
                });
            """
            )

        # Load the CSV file into a DataFrame
        # df = pd.read_csv('data.csv')

        page = await context.new_page()
        page.set_default_timeout(120000)

        from scraper.actions.login import loginAcct
        controller = linkednController()
        controller.add_command(loginAcct(page, context, "https://www.linkedin.com"))
        await controller.execute_commands()
        controller.clear_commands()

        logger.info("Auth complete")
        from scraper.actions.search import search
        controller.add_command(search(page, context, "Merec Industries"))
        await controller.execute_commands()
        controller.clear_commands()

        await page.close()
        await context.close()


if __name__ == "__main__":
    asyncio.run(navigate())
