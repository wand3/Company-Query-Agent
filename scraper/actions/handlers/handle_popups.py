import asyncio
import logging
from contextlib import asynccontextmanager
from playwright.async_api import Page

logger = logging.getLogger("popup_handler")


class UnexpectedPopupHandler:
    def __init__(self, page: Page):
        self.page = page
        self.enabled = True
        self.known_popups = set()
        self.handlers = []
        self.periodic_check_task = None

    async def start(self):
        """Activate all popup monitoring mechanisms"""
        # Setup event listeners
        self.handlers = [
            self.page.on("dialog", self.handle_dialog),
            self.page.on("popup", self.handle_popup),
            # self.page.on("load", self.check_page_modals)
        ]

        # Start periodic background checker
        self.periodic_check_task = asyncio.create_task(self.periodic_check())

    async def stop(self):
        """Deactivate all monitoring"""
        self.enabled = False
        for handler in self.handlers:
            await handler.dispose()
        if self.periodic_check_task:
            self.periodic_check_task.cancel()

    async def handle_dialog(self, dialog):
        """Handle JavaScript dialogs (alert, confirm, prompt)"""
        if not self.enabled:
            return

        logger.warning(f"Dismissing unexpected dialog: {dialog.type()} - {dialog.message}")
        await dialog.dismiss()

    async def handle_popup(self, popup):
        """Handle new browser windows/tabs"""
        if not self.enabled:
            return

        logger.warning(f"Closing unexpected popup: {popup.url}")
        await popup.close()

    async def handle_dismissible_alert(self):
        """
        Detects and dismisses access restriction alerts with drop shadow.
        Looks for an alert containing the message:
        "You don't have access to this profile"
        and attempts to click "Got it" or "X" to dismiss it.
        """
        if not self.enabled:
            return

        dismiss_selectors = [
            # LinkedIn dismiss and got it buttons
            "button:has-text('Got it')",
            "button[aria-label='Dismiss']",
        ]

        text_contents = [
         "You don't have access to this profile"
        ]

        try:
            for selector in dismiss_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        for text in text_contents:
                            if text in element.inner_text:
                                try:
                                    # self.logger.info(f"Restriction popup not visible {e}")
                                    # Try clicking the "Got it" button if visible
                                    got_it_button = self.page.locator("button:has-text('Got it')")
                                    if await got_it_button.is_visible():
                                        await got_it_button.click()
                                        logger.info("Dismissed alert with 'Got it' button")
                                        return True

                                    # Fallback: Try closing with 'X' button
                                    close_button = self.page.locator("button[aria-label='Dismiss']")  # Adjust if needed
                                    if await close_button.is_visible():
                                        await close_button.click()
                                        logger.info("Dismissed alert with 'X' button")
                                        return True
                                except Exception as e:
                                    logger.warning(f"Alert was visible but no dismiss button was found {e}")
                except Exception as e:
                    logger.info(f'Alert not Dismissed {e}')
            #
            # # Wait for the alert to appear within 3 seconds
            # try:
            #     from ..utilities import hover_if_text
            #     seen = await hover_if_text(self, "You don't have access to this profile")
            #     if seen:
            #         try:
            #             # self.logger.info(f"Restriction popup not visible {e}")
            #             # Try clicking the "Got it" button if visible
            #             got_it_button = self.page.locator("button:has-text('Got it')")
            #             if await got_it_button.is_visible():
            #                 await got_it_button.click()
            #                 logger.info("Dismissed alert with 'Got it' button")
            #                 return True
            #
            #             # Fallback: Try closing with 'X' button
            #             close_button = self.page.locator("button[aria-label='Dismiss']")  # Adjust if needed
            #             if await close_button.is_visible():
            #                 await close_button.click()
            #                 logger.info("Dismissed alert with 'X' button")
            #                 return True
            #         except Exception as e:
            #             logger.warning(f"Alert was visible but no dismiss button was found {e}")
            # except Exception as e:
            #     logger.error(f"Failed to handle access alert: {str(e)}")
        except Exception as e:
            logger.debug(f"No relevant alert detected or different alert shown {e}")
        return False

    async def check_page_modals(self):
        """Check for in-page modals"""
        if not self.enabled:
            return

        modal_selectors = [
            # Common modal patterns
            "[role='alert']",
            "[role='dialog']",
            ".modal",
            ".popup",
            ".overlay",

            # Platform-specific (LinkedIn, Salesforce, etc.)


            ".cookie-banner",  # GDPR cookie banners
            "[data-test-id='auth-wall']",
            "#tcp-modal",  # Common marketing modals
            ".ab-in-app-message",  # Marketing popups
        ]

        for selector in modal_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    element_id = await element.evaluate("el => el.id || el.className")
                    if element_id not in self.known_popups:
                        logger.warning(f"Closing unexpected modal: {selector}")
                        await self.close_modal(element)
                        self.known_popups.add(element_id)
            except Exception as e:
                logger.debug(f"Modal check error: {str(e)}")

    async def close_modal(self, element):
        """Attempt various strategies to close a modal"""
        try:
            # Strategy 1: Look for close buttons
            close_buttons = await element.query_selector_all(
                "button[aria-label='Close'], button[aria-label='Dismiss'], "
                "[data-testid='dismiss-modal'], .close-button, .btn-close"
            )

            if close_buttons:
                await close_buttons[0].click()
                await self.page.wait_for_timeout(500)
                return True

            # Strategy 2: Click outside modal
            bounding_box = await element.bounding_box()
            if bounding_box:
                await self.page.mouse.click(
                    bounding_box["x"] - 10,
                    bounding_box["y"] - 10
                )
                await self.page.wait_for_timeout(500)
                return True

            # Strategy 3: Press Escape
            await self.page.keyboard.press("Escape")
            await self.page.wait_for_timeout(500)
            return True

        except Exception as e:
            logger.debug(f"Modal close failed: {str(e)}")
            return False

    async def periodic_check(self):
        """Background task to periodically check for popups"""
        while self.enabled:
            try:
                # await self.check_page_modals()
                await self.handle_dismissible_alert()
                await asyncio.sleep(3)  # Check every 3 seconds
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.debug(f"Periodic check error: {str(e)}")

    @asynccontextmanager
    async def disabled(self):
        """Temporarily disable popup handling"""
        was_enabled = self.enabled
        self.enabled = False
        try:
            yield
        finally:
            self.enabled = was_enabled
