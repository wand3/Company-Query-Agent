import re
from scraper.actions.base import Base
from playwright.async_api import Page
import asyncio
import json
import random
import os
from pathlib import Path
from scraper.main import delay, short_delay
from .utilities import check_if_click_successful, check_if_its_visible, click_with_fallback, hover_with_fallback, \
    select_first_company_result

# Configure logging to display messages to the terminal
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.StreamHandler()])
from ..logger import setup_logger


parent_dir = os.path.dirname(os.path.dirname(__file__))  # Get the parent directory of the current directory
companies_filepath = os.path.join(parent_dir, "scraper/companies.json")


class search(Base):
    """
        if cookies exist load up user cookies
        login an account with required inputs from pages
    """

    # logger = setup_logger("linkedn", "INFO")

    def __init__(self, page, context, name: str, logger):
        super().__init__(page=page)  # <--- ADD THIS LINE! Pass the 'page' argument up to Base.__init__
        self.page = page
        self.name = name
        self.context = context
        self.logger = logger
        self.logger.info("initialized successfully")

    # load cookies if it exists
    async def search_name(self):
        # await self.page.wait_for_load_state()
        # search_input = await self.page.get_by_placeholder("Search", exact=True).is_visible()
        # self.logger.info("Search box seen")
        selector = "div#global-nav-search.global-nav__search"
        search_input = await check_if_its_visible(self.page, selector, self.logger)
        if search_input:
            self.logger.info(f"Search box visible")
            hover_search = await hover_with_fallback(self.page, selector, self.logger)
            self.logger.info(f"Hover Search box visible {hover_search}")

            click_search = await click_with_fallback(self.page, selector, self.logger)
            self.logger.info(f"Click Search box {click_search}")

            await self.page.keyboard.type(self.name, delay=100)
            # await self.page.get_by_placeholder("Search", exact=True).fill(self.name)
            await asyncio.sleep(short_delay)

            self.logger.info(f"Search box filled with company name {self.name}")
            await self.page.keyboard.press("Enter")
            await self.page.wait_for_load_state()
            await asyncio.sleep(delay)
            self.logger.info(f"Search success for {self.name}")
            return True

    # selects company filter
    async def company_filter(self, selector):
        """
        Handles company filter interaction with full verification workflow:
        1. Checks visibility using multiple methods
        2. Hovers with fallback techniques
        3. Clicks with prioritized fallbacks
        4. Verifies success through URL pattern and element state
        """
        async with self.disable_popups():
            # check if filters section is loaded
            filters_bar = await check_if_its_visible(self.page, selector, self.logger)
            try:

                if filters_bar:
                    # Define URL pattern for verification
                    url_pattern = "https://www.linkedin.com/search/results/companies/**"

                    # Candidate selectors in priority order
                    candidate_selectors = [
                        "ul[role='list'] li button:has-text('Companies')",  # First locator in list
                        "button.artdeco-pill:has-text('Companies')",  # Direct button selector
                        "button.search-reusables__filter-pill-button:has-text('Companies')",
                        "button:has-text('Companies')"
                    ]

                    success = False

                    for candidate in candidate_selectors:
                        try:
                            # 1. Visibility check
                            is_visible = await check_if_its_visible(self.page, candidate, self.logger)
                            if not is_visible:
                                self.logger.warning(f"Selector not visible: {candidate} {is_visible}")
                                continue

                            self.logger.info(f"Attempting filter with selector: {candidate}")

                            # 2. Hover interaction
                            hover_success = await hover_with_fallback(self.page, candidate, self.logger)
                            if not hover_success:
                                self.logger.warning(f"Hover failed for selector: {candidate} {hover_success}")

                            # 3. Click interaction
                            click_success = await click_with_fallback(self.page, candidate)
                            if not click_success:
                                self.logger.error(f"Click failed for selector: {candidate} {click_success}")
                                continue

                            # check and handle alert for dialog on expanding network

                            try:
                                check_alert = await self.handle_access_alert()
                                if check_alert:
                                    pass
                            except Exception as e:
                                self.logger.debug(f"No relevant alert detected or different alert shown {e}")

                            # 4. Success verification
                            verified = await check_if_click_successful(
                                self.page,
                                selector=candidate,
                                url_pattern=url_pattern,
                                logger=self.logger
                            )
                            self.logger.info(f"Company filter click successfully: {candidate} {verified}")
                            if verified:
                                self.logger.info(f"Company filter activated successfully with: {candidate}")
                                success = True
                                break
                            else:
                                # Fallback: Check if button state changed
                                pressed_state = await self.page.evaluate(f"""selector => {{
                                            const btn = document.querySelector(selector);
                                            return btn ? btn.getAttribute('aria-pressed') : null;
                                        }}""", candidate)

                                if pressed_state == 'true':
                                    self.logger.info(f"Filter state changed to active: {candidate}")
                                    success = True
                                    break
                        except Exception as e:
                            self.logger.error(f"Filter processing failed for {candidate}: {str(e)}")

                    try:
                        # CLick about first result to visit company
                        result_click = await select_first_company_result(self.page, "div[data-chameleon-result-urn]", self.logger)
                        # result_click = self.page.locator(
                        #     'ul[role="list"] li >> a[data-test-app-aware-link]').first()
                        # await result_click.click(force=True)
                        self.logger.debug(f"First result click status {result_click}")
                        success = True
                    except Exception as e:
                        self.logger.error(f"Result click failed {e}")

                    if not success:
                        self.logger.error("All company filter methods failed")

                    return success

            except Exception as e:
                self.logger.error(f"Search filters not loaded {e}")

    # scrape company about page
    async def company_about(self):
        """
        Navigates to a company's 'About' page using LinkedIn's navigation bar.
        Optimized with page.wait_for for better performance and reliability.
        """
        # Define URL patterns for verification
        # company_url_pattern = "https://www.linkedin.com/search/results/companies/**"
        company_url_pattern = "https://www.linkedin.com/company/**"

        about_url_pattern = "**/about/"

        # Define navigation bar selector
        # nav_selector = "ul.org-page-navigation__items"
        nav_selector = "ul.org-page-navigation__items"

        # Define About link selector options (in priority order)
        about_selectors = [
            f"{nav_selector} >> text='About'",  # Text-based targeting,
            # f"{nav_selector} li a{n}",  # Text-based targeting

            f"{nav_selector} a:has-text('About')",  # Text-based targeting
            f"{nav_selector} a[href*='{about_url_pattern}']",  # URL pattern targeting
            f"{nav_selector} li:nth-child(2) a",  # Position-based (2nd item)
            "a.org-page-navigation__item-anchor:has-text('About')"  # Fallback
        ]

        # 1. Verify we're on a company page using wait_for
        try:
            # await self.page.wait_for(
            #     lambda: re.match(r"https://www\.linkedin\.com/company/.*", self.page.url),
            #     timeout=5000
            # )
            await self.page.wait_for_url(lambda: re.match(r"https://www\.linkedin\.com/company/.*", self.page.url))
            self.logger.info("Verified company page URL pattern")
        except TimeoutError:
            self.logger.error("Not on a company page - aborting About navigation")

        # 2. Wait for navigation bar to load using wait_for
        try:
            await check_if_its_visible(self.page, nav_selector, self.logger)
            self.logger.info("Company navigation bar loaded")
        except TimeoutError:
            self.logger.error("Navigation bar not found - cannot proceed to About page")

        success = False

        for about_selector in about_selectors:
            try:
                self.logger.info(f"Attempting with selector: {about_selector}")

                # 3. Check visibility using our utility function
                is_visible = await check_if_its_visible(self.page, about_selector, self.logger)
                if not is_visible:
                    self.logger.warning(f"About link not visible with selector: {about_selector}")
                    continue

                # 4. Hover interaction
                hover_success = await hover_with_fallback(self.page, about_selector, self.logger)
                if not hover_success:
                    self.logger.warning(f"Hover failed for selector: {about_selector}")

                # Click interaction
                click_success = await click_with_fallback(self.page, about_selector, self.logger)
                if not click_success:
                    self.logger.error(f"Click failed for selector: {about_selector}")
                    continue

                await self.page.wait_for_load_state()
                try:

                    check = await check_if_click_successful(self.page, about_selector, company_url_pattern, self.logger)
                    if check:
                        self.logger.info(f"{check}----- ---- ----- Checking if click to about page was successful")
                except Exception as e:
                    self.logger.error(f"{e}----- ---- ----- About page overview successful")

                overview = self.page.get_by_text("Overview")
                if overview:
                    self.logger.info(f"----- ---- ----- About page overview successful")
                    # if overview:
                    #     scrape_about = await self.scrape_company_about()
                    #     if scrape_about:
                    success = True
                    self.logger.info("----- ---- ----- Scrape successful")
                    return success

                # Verify navigation success using wait_for
                # try:
                #     # Wait for URL change using wait_for
                #     await self.page.wait_for_url(
                #         lambda: re.match(r".*/about/$", self.page.url) or
                #                 re.match(r".*/about$", self.page.url),
                #         timeout=400
                #     )
                #     self.logger.info("About page navigation verified by URL pattern")
                #     success = True
                #     break
                # except TimeoutError:
                    # Verify active state using wait_for_function
                    # try:
                    #     await self.page.wait_for_function("""selector => {{
                    #             const el = document.querySelector(selector);
                    #             return el && el.getAttribute('aria-current') === 'page';
                    #         }}""",
                    #                                       about_selector,
                    #                                       timeout=2000
                    #                                       )
                    #     self.logger.info("About link shows active state - navigation successful")
                    #     success = True
                    #     break
                    # except Exception as e:
                    #     self.logger.warning(f"About page verification failed for {about_selector} {e}")

            except Exception as e:
                self.logger.error(f"About navigation failed with {about_selector}: {str(e)}")

        return success

    async def execute(self):
        if await self.search_name():
            self.logger.info(f"Search {self.name} loading")
            company_selector = "section.scaffold-layout-toolbar"
            apply_filter = await self.company_filter(company_selector)
            self.logger.info(f"Apply filter {apply_filter} success")

            if apply_filter:
                self.logger.info(f"Search filter about page in {self.name} success")
                about_page = await self.company_about()
                self.logger.info(f"Company about page {about_page}")

                try:
                    if about_page:
                        self.logger.info("About page loaded success")
                        self.logger.info("Now on About page - scraping company data")
                        return

                except Exception as e:
                    self.logger.info(f"About page load error {e}")

        await self.page.wait_for_load_state()
        self.logger.info(f"Search and filter success and about page")
