#!/usr/bin/env python3
from actions.base import Base
from playwright.async_api import Page
import logging
import asyncio
import json
import random
import os
from pathlib import Path
# from get_user_cookies import login


# Configure logging to display messages to the terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])


parent_dir = os.path.dirname(os.path.dirname(__file__))  # Get the parent directory of the current directory
cookies_filepath = os.path.join(parent_dir, "scraper/cookies.json")


class loginAcct(Base):
    """
        if cookies exist load up user cookies
        login an account with required inputs from pages
    """

    def __init__(self, page, context, url: str):
        self.page = page
        self.url = url
        self.context = context
        logging.info("initialized successfully")

    # load cookies if it exists
    async def load_cookies(self):
        base_folder = Path(__name__).resolve().parent
        file_path = f'{base_folder}/scraper/cookies.json'
        # load cookies of the user from the file
        with open(file_path, "r") as f:
            # cookies_data = f.read()
            # cookies = [{"name": c.split("=")[0], "value": c.split("=")[1], "domain": "x.com", "path": "/"}
            #            for c in cookies_data.split(",")]
            cookies = json.load(f)
            await self.context.add_cookies(cookies)
            logging.info(f"Cookies loaded for successfully")

    async def execute(self):
        await self.load_cookies()
        logging.info(f"cookies loaded to session")
        await asyncio.sleep(random.randint(2, 5))
        await self.page.goto(self.url)
        await self.page.wait_for_load_state()
        await self.page.wait_for_load_state()
