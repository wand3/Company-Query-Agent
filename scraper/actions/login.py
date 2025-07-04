from scraper.actions.base import Base
from playwright.async_api import Page
import asyncio
import json
import random
from pathlib import Path
from ..logger import setup_logger
from scraper.main import delay, short_delay
from .utilities import check_if_click_successful, check_if_its_visible, click_with_fallback, hover_with_fallback, \
    device_auth_confirmation
from dotenv import load_dotenv
import os

load_dotenv()
username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")


# logger = setup_logger("linkedn", "INFO")


parent_dir = Path(__name__).resolve().parent  # Get the parent directory of the current directory
cookies_filepath = parent_dir / 'scraper' / 'cookies.json'


class loginAcct(Base):
    """
        if cookies exist load up user cookies
        login an account with required inputs from pages
    """

    def __init__(self, page, context, url: str, logger):
        self.page = page
        self.url = url
        self.context = context
        self.logger = logger
        logger.info("initialized successfully")

    # save login cookies
    async def save_cookies(self, file_path=cookies_filepath):
        self.logger.info(f"Attempting to save cookies to: {cookies_filepath}")
        try:
            cookies = await self.context.cookies()
            with open(file_path, 'w') as f:
                json.dump(cookies, f, indent=4)  # Added indent for readability in JSON file
            self.logger.info(f"Login cookies successfully saved to {cookies_filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save login cookies: {e}")
            return False



    # login if it auto logs out
    @staticmethod
    async def sign_in(page, context, logger):

        """

            Check your LinkedIn app

            We sent a notification to your signed in devices. Open your LinkedIn app and tap Yes to confirm your sign-in attempt.

            Login the site
        :param logger:
        :param page:
        :param context:
        :return:
        """

        login_button = await page.get_by_text("Sign in with email").is_visible()
        if login_button:
            await page.get_by_text("Sign in with email").click()
            logger.info("Login button spotted succesfully")
        else:
            logger.error("Login button not found")
            return "Not Visible"
        await page.wait_for_load_state()
        await page.locator("input[name='session_key']").click()
        await asyncio.sleep(delay)

        # email = input("email: ")
        await page.locator("input[name='session_key']").fill(username)

        await page.get_by_label("Password", exact=True).click()
        # password = input("enter password: ")
        await asyncio.sleep(short_delay)

        await page.get_by_label("Password", exact=True).fill(password)
        await asyncio.sleep(short_delay)

        signin = await page.get_by_role("button", name="Sign in", exact=True).is_visible()
        if signin:
            await page.get_by_role("button", name="Sign in", exact=True).click()
            await asyncio.sleep(delay)
            logger.info("Login button click success")

            # check if signin expired
            # Define your selector (using both ID and class)
            selector = "div#card-container.card-layout"
            try:
                card_visible = await check_if_its_visible(page, selector)
                if card_visible:
                    # check if sign in expired is visible and click try signing in again
                    selector = "h1.header__content__heading__inapp"
                    signin_expired = await check_if_its_visible(page, selector)
                    if not signin_expired:
                        # hover and click
                        selector = "div.try-again"
                        button_hover = await hover_with_fallback(page, selector)
                        if button_hover:
                            await click_with_fallback(page, selector)
                            check = check_if_click_successful(page, selector, 'https://www.linkedin.com/checkpoint/lg/login')
                            if check:
                                logger.warning("Click was successful")
                                if login_button:
                                    await page.get_by_text("Sign in with email").click()
                                    logger.info("Login button spotted succesfully")
                                else:
                                    logger.error("Login button not found")
                                    return "Not Visible"
                                await page.wait_for_load_state()
                                await page.locator("input[name='session_key']").click()
                                await asyncio.sleep(delay)

                                # email = input("email: ")
                                await page.locator("input[name='session_key']").fill(username)

                                await page.get_by_label("Password", exact=True).click()
                                # password = input("enter password: ")
                                await asyncio.sleep(short_delay)

                                await page.get_by_label("Password", exact=True).fill(password)
                                await asyncio.sleep(short_delay)

                                signin = await page.get_by_role("button", name="Sign in", exact=True).is_visible()
                                if signin:
                                    await page.get_by_role("button", name="Sign in", exact=True).click()
                                    await asyncio.sleep(delay)
                                    logger.info("Login button click success")

                    selector = "input#recognizedDevice.large-input"
                    if not await check_if_its_visible(page, selector):
                        confirm = await device_auth_confirmation(page, selector)

                        try:
                            if confirm:
                                logger.info("Feed page all set")
                        except Exception as e:
                            logger.info(f"Feed page load failed : {e}")

                    # check if feed page loaded
                    url_pattern = "https://www.linkedin.com/feed/"
                    selector = "div#global-nav-search.global-nav__search"
                    feed_navigate = await check_if_click_successful(page, selector, url_pattern, logger)
                    if feed_navigate:
                        logger.info("Authentication complete now proceed to search")

            except Exception as e:
                logger.info(f"Error checking card layout locator : {e}")

    async def execute(self):
        # load = await self.load_cookies()
        # if load:
        #     self.logger.info(f"cookies loaded to session")
        #     verify_cookies = check_if_click_successful(self.page, "div#global-nav-search.global-nav__search", "https://www.linkedin.com/feed/", self.logger)
        #     if verify_cookies:
        #         await asyncio.sleep(random.randint(2, 5))
        #         return
        await asyncio.sleep(random.randint(2, 5))
        await self.page.goto(self.url)
        await self.page.wait_for_load_state()
        login_button = await self.page.get_by_text("Sign in with email").is_visible()
        if login_button:
            #     logger.error("Session continued failed for user")
            #     # await login()
            await self.sign_in(self.page, self.context, self.logger)
            self.logger.info(f"Session continued successful for")
            await self.page.wait_for_load_state()

            # Save the login cookies
            await self.save_cookies()
            self.logger.info(f"Cookies saved for successfully")

