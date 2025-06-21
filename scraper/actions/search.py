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
        # await self.page.wait_for_load_state()
        # search_input = await self.page.get_by_placeholder("Search", exact=True).is_visible()
        # logger.info("Search box seen")
        selector = "div#global-nav-search.global-nav__search"
        search_input = await check_if_its_visible(self.page, selector, logger)
        if search_input:
            logger.info(f"Search box visible")
            hover_search = await hover_with_fallback(self.page, selector, logger)
            logger.info(f"Hover Search box visible {hover_search}")

            click_search = await click_with_fallback(self.page, selector, logger)
            logger.info(f"Click Search box {click_search}")

            await self.page.keyboard.type(self.name, delay=100)
            # await self.page.get_by_placeholder("Search", exact=True).fill(self.name)
            await asyncio.sleep(short_delay)

            logger.info(f"Search box filled with company name {self.name}")
            await self.page.keyboard.press("Enter")
            await self.page.wait_for_load_state()
            await asyncio.sleep(delay)
            logger.info(f"Search success for {self.name}")
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
        # check if filters section is loaded
        filters_bar = await check_if_its_visible(self.page, selector, logger)
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
                        is_visible = await check_if_its_visible(self.page, candidate, logger)
                        if not is_visible:
                            logger.warning(f"Selector not visible: {candidate} {is_visible}")
                            continue

                        logger.info(f"Attempting filter with selector: {candidate}")

                        # 2. Hover interaction
                        hover_success = await hover_with_fallback(self.page, candidate, logger)
                        if not hover_success:
                            logger.warning(f"Hover failed for selector: {candidate} {hover_success}")

                        # 3. Click interaction
                        click_success = await click_with_fallback(self.page, candidate)
                        if not click_success:
                            logger.error(f"Click failed for selector: {candidate} {click_success}")
                            continue

                        # 4. Success verification
                        await asyncio.sleep(short_delay)  # Allow time for navigation
                        verified = await check_if_click_successful(
                            self.page,
                            selector=candidate,
                            url_pattern=url_pattern,
                            logger=logger
                        )
                        logger.info(f"Company filter click successfully: {candidate} {verified}")
                        if verified:
                            logger.info(f"Company filter activated successfully with: {candidate}")
                            success = True
                            break
                        else:
                            # Fallback: Check if button state changed
                            pressed_state = await self.page.evaluate(f"""selector => {{
                                        const btn = document.querySelector(selector);
                                        return btn ? btn.getAttribute('aria-pressed') : null;
                                    }}""", candidate)

                            if pressed_state == 'true':
                                logger.info(f"Filter state changed to active: {candidate}")
                                success = True
                                break
                    except Exception as e:
                        logger.error(f"Filter processing failed for {candidate}: {str(e)}")

                try:
                    # CLick about first result to visit company
                    result_click = await select_first_company_result(self.page, "div[data-chameleon-result-urn]", logger)
                    # result_click = self.page.locator(
                    #     'ul[role="list"] li >> a[data-test-app-aware-link]').first()
                    # await result_click.click(force=True)
                    logger.debug(f"First result click status {result_click}")
                    success = True
                except Exception as e:
                    logger.error(f"Result click failed {e}")

                if not success:
                    logger.error("All company filter methods failed")

                return success

        except Exception as e:
            logger.error(f"Search filters not loaded {e}")

    # async def navigate_to_verified_link(page):
    #     """
    #     Locates and clicks the verified badge link to navigate to the about page
    #     """
    #     # Define selectors in priority order
    #     selectors = [
    #         "a[href*='/about/'][aria-label='Verified']",  # Most specific
    #         "a.ember-view.active[href*='/about/']",  # Class-based
    #         "a[href*='/about/'] svg[data-test-icon='verified-medium']",  # Child element
    #         "a[href*='/about/']"  # Generic fallback
    #     ]
    #
    #     for selector in selectors:
    #         try:
    #             # Check visibility
    #             if await page.locator(selector).is_visible():
    #                 logger.info(f"Verified link found with selector: {selector}")
    #
    #                 # Click using our robust click method
    #                 if await click_with_fallback(page, selector):
    #                     # Verify navigation success
    #                     await page.wait_for_url("**/about/", timeout=10000)
    #                     logger.info("Successfully navigated to About page via verified badge")
    #                     return True
    #         except Exception as e:
    #             logger.warning(f"Attempt failed with {selector}: {str(e)}")
    #
    #     logger.error("All attempts to locate verified badge failed")
    #     return False

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
            logger.info("Verified company page URL pattern")
        except TimeoutError:
            logger.error("Not on a company page - aborting About navigation")
            return False

        # 2. Wait for navigation bar to load using wait_for
        try:
            await check_if_its_visible(self.page, nav_selector, logger)
            logger.info("Company navigation bar loaded")
        except TimeoutError:
            logger.error("Navigation bar not found - cannot proceed to About page")
            return False

        success = False

        for about_selector in about_selectors:
            try:
                logger.info(f"Attempting with selector: {about_selector}")

                # 3. Check visibility using our utility function
                is_visible = await check_if_its_visible(self.page, about_selector, logger)
                if not is_visible:
                    logger.warning(f"About link not visible with selector: {about_selector}")
                    continue

                # 4. Hover interaction
                hover_success = await hover_with_fallback(self.page, about_selector, logger)
                if not hover_success:
                    logger.warning(f"Hover failed for selector: {about_selector}")

                    # Check for hover effects using wait_for
                    # try:
                    #     await self.page.wait_for_function(
                    #         """selector => {{
                    #             const el = document.querySelector(selector);
                    #             return el && (el.matches(':hover') ||
                    #                    getComputedStyle(el).backgroundColor !== 'rgba(0, 0, 0, 0)');
                    #         }}""", about_selector,
                    #         timeout=2000
                    #     )
                    #     logger.info("Hover effects confirmed")
                    # except Exception as e:
                    #     logger.debug(f"Hover effects not detected, proceeding anyway {e}")

                # 5. Click interaction
                click_success = await click_with_fallback(self.page, about_selector, logger)
                if not click_success:
                    logger.error(f"Click failed for selector: {about_selector}")
                    continue

                await self.page.wait_for_load_state()
                check = await check_if_click_successful(self.page, about_selector, company_url_pattern, logger)
                logger.info("----- ---- ----- Checking if click to about page was successful")

                if check:

                    overview = self.page.get_by_text("Overview")
                    logger.info("----- ---- ----- About page overview successful")

                    if overview:
                        scrape_about = await self.scrape_company_about()
                        if scrape_about:
                            success = True
                            logger.info("----- ---- ----- Scrape successful")
                            return success



                # Verify navigation success using wait_for
                # try:
                #     # Wait for URL change using wait_for
                #     await self.page.wait_for_url(
                #         lambda: re.match(r".*/about/$", self.page.url) or
                #                 re.match(r".*/about$", self.page.url),
                #         timeout=400
                #     )
                #     logger.info("About page navigation verified by URL pattern")
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
                    #     logger.info("About link shows active state - navigation successful")
                    #     success = True
                    #     break
                    # except Exception as e:
                    #     logger.warning(f"About page verification failed for {about_selector} {e}")

            except Exception as e:
                logger.error(f"About navigation failed with {about_selector}: {str(e)}")

        # if not success:
        #     # Final fallback: Check for About page content using wait_for
        #     try:
        #         await self.page.wait_for_function(
        #             """() => {
        #                 return document.querySelector('section.about-us') ||
        #                        document.querySelector('h2')?.innerText.includes('Overview');
        #             }""",
        #             timeout=3000
        #         )
        #         logger.info("Detected About page content - navigation successful")
        #         success = True
        #     except Exception as e:
        #         logger.error(f"All About navigation methods failed {e}")

        return success

    async def scrape_company_about(self):
        # Get page content after navigation
        page_content = await self.page.content()
        source_url = self.page.url

        # Initialize scraper
        from scraper.actions.scrape import CompanyAboutScraper
        scraper = CompanyAboutScraper(page_content, source_url)

        # Extract data
        company_data = scraper.scrape()
        logger.info(f'{company_data}')

        # Save to JSON
        json_path = scraper.save_to_json()
        logger.info(f"Company data saved to: {json_path}")

        return company_data

    async def execute(self):
        if await self.search_name():
            logger.info(f"Search {self.name} loading")
            company_selector = "section.scaffold-layout-toolbar"
            apply_filter = await self.company_filter(company_selector)
            logger.info(f"Apply filter {apply_filter} success")

            if apply_filter:
                logger.info(f"Search filter about page in {self.name} success")
                about_page = await self.company_about()
                logger.info(f"Company about page {about_page}")

                try:
                    if about_page:
                        logger.info("About page loaded success")
                        logger.info("Now on About page - scraping company data")
                        company_data = await self.scrape_company_about()
                        logger.info(f"Scraped data for {company_data}")

                except Exception as e:
                    logger.info(f"About page load error {e}")

        await self.page.wait_for_load_state()
        logger.info(f"Search and filter success and about page")
