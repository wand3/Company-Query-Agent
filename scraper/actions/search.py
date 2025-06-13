#!/usr/bin/env python3
from actions.base import Base
from playwright.async_api import Page
import asyncio
import json
import random
import os
from pathlib import Path
from ..logger import setup_logger
from ..main import delay, short_delay


# Configure logging to display messages to the terminal
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])

logger = setup_logger("linkedn", "INFO")


parent_dir = os.path.dirname(os.path.dirname(__file__))  # Get the parent directory of the current directory
companies_filepath = os.path.join(parent_dir, "scraper/companies.json")


class search(Base):
    """
        if cookies exist load up user cookies
        login an account with required inputs from pages
    """

    def __init__(self, page, context, name: str):
        self.page = page
        self.name = name
        self.context = context
        logger.info("initialized successfully")

    # load cookies if it exists
    async def search_name(self):
        search_input = await self.page.locator('id=global-nav-search').is_visible()
        logger.info("Search box seen")
        if search_input:
            await self.page.get_by_placeholder("Search").fill(self.name)
            await asyncio.sleep(short_delay)

            logger.info(f"Search box filled with company name {self.name}")
            await self.page.keyboard.press("Enter")
            await self.page.wait_for_load_state()
            await asyncio.sleep(delay)
            logger.info(f"Search success for {self.name}")

    async def company_filter(self):
        """ user either botton click on company name or goto then about to get company with name and fetch company details

        e.g. https://www.linkedin.com/company/lapaire/

        https://www.linkedin.com/company/lapaire/about/

        """
        pass





    async def execute(self):
        logger.info(f"cookies loaded to session")
        await asyncio.sleep(random.randint(2, 5))
        await self.page.goto(self.url)
        await self.page.wait_for_load_state()
        await self.page.wait_for_load_state()
