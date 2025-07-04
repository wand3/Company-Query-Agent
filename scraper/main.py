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


# load cookies if it exists
async def load_cookies(context, logger):
    try:
        base_folder = Path(__name__).resolve().parent
        file_path = base_folder / 'scraper' / 'cookies.json'
        # load cookies of the user from the file
        with open(file_path, "r") as f:
            cookies = json.load(f)
            await context.add_cookies(cookies)
            logger.info(f"Cookies loaded for successfully")
        return True
    except Exception as e:
        logger.error(e)
        return False


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
        controller = linkednController()
        # load cookies first else login if cookies doesn't exist
        try:
            load = await load_cookies(context, logger)
            page = await context.new_page()
            page.set_default_timeout(15000)
            if load:
                await page.goto('https://www.linkedin.com/feed')
                return
            else:
                from scraper.actions.login import loginAcct
                controller.add_command(loginAcct(page, context, "https://www.linkedin.com", logger=logger))
                await controller.execute_commands()
                controller.clear_commands()
                logger.info("Auth complete")
        except Exception as e:
            logger.error(f'{e}')

        from scraper.actions.search import search
        # get and loop through company and country data
        base_folder = Path(__name__).resolve().parent
        results_dir = base_folder / "scraper" / "companies.json"
        # Load the JSON file
        with open(results_dir, "r", encoding="utf-8") as file:
            companies = json.load(file)

        # Loop through each company and call the function with the name
        for company in companies:

            controller.add_command(search(page, context, name=company["name"], logger=logger))
            await controller.execute_commands()

            # scrape page
            from scraper.actions.scrape import CompanyAboutScraper
            page_content = await page.content()
            source_url = page.url
            controller.clear_commands()
            controller.add_command(CompanyAboutScraper(page_content, source_url,  logger=logger))
            await controller.execute_commands()

            controller.clear_commands()

        await page.close()
        await context.close()


if __name__ == "__main__":
    asyncio.run(navigate())
