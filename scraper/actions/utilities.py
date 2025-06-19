from ..logger import setup_logger

logger = setup_logger("linkedn", "INFO")


async def check_if_click_successful(page, selector, url_pattern):
    """
    Verifies if a click operation was successful by checking:
    1. Network idle state
    2. URL navigation pattern match
    3. Element state changes

    Returns:
        bool: True if any success indicator is detected, False otherwise
    """
    success = False
    original_url = page.url

    # 1. Check network idle state
    try:
        await page.wait_for_load_state("networkidle", timeout=5000)
        logger.info(f"Network idle check completed for {selector}")
        success = True
    except TimeoutError:
        logger.warning(f"Network did not reach idle state for {selector}")

    # 2. Check URL navigation pattern
    try:
        await page.wait_for_url(
            url_pattern,
            timeout=5000,
            wait_until="domcontentloaded"
        )
        logger.info(f"URL pattern match successful: {url_pattern}")
        return True  # Return immediately on URL match
    except TimeoutError:
        logger.warning(f"URL did not change to match pattern: {url_pattern}")

    # 3. Verify element state changes (if URL didn't change)
    if not success:
        try:
            # Check if element disappeared or changed state
            if not await page.is_visible(selector):
                logger.info(f"Element vanished after click: {selector}")
                success = True
            else:
                # Check for visual/state changes
                is_now_disabled = await page.evaluate(f"""() => {{
                    const el = document.querySelector('{selector}');
                    return el && (el.disabled || el.getAttribute('aria-disabled') === 'true');
                }}""")

                if is_now_disabled:
                    logger.info(f"Element state changed to disabled: {selector}")
                    success = True

                # Check for CSS change indicating success
                has_success_style = await page.evaluate(f"""() => {{
                    const el = document.querySelector('{selector}');
                    if (!el) return false;
                    const style = getComputedStyle(el);
                    return style.backgroundColor.includes('green') || 
                           style.border.includes('green') ||
                           style.color.includes('green');
                }}""")

                if has_success_style:
                    logger.info(f"Visual success indicators detected: {selector}")
                    success = True
        except Exception as e:
            logger.error(f"Element state check failed: {str(e)}")

    # 4. Final fallback: Check if URL changed at all
    if not success:
        current_url = page.url
        if current_url != original_url:
            logger.info(f"URL changed from {original_url} to {current_url}")
            success = True

    return success


async def check_if_its_visible(page, selector):
    """
    Checks if a selector is visible using multiple methods.
    Returns True as soon as one method confirms visibility.
    :param page: Playwright page context
    :param selector: Element selector
    :return: Boolean
    """
    # Method 1: Using is_visible()
    try:
        if await page.locator(selector).is_visible():
            logger.info(f"is_visible() confirmed visibility for: {selector}")
            return True
    except Exception as e:
        logger.error(f"is_visible() failed for {selector}: {str(e)}")

    # Method 2: CSS visibility check
    try:
        visible = await page.locator(selector).evaluate("""
            el => {
                const style = window.getComputedStyle(el);
                return style.visibility !== 'hidden' && 
                       style.display !== 'none' &&
                       el.offsetWidth > 0 &&
                       el.offsetHeight > 0;
            }
        """)
        if visible:
            logger.info(f"CSS check confirmed visibility for: {selector}")
            return True
    except Exception as e:
        logger.error(f"CSS visibility check failed for {selector}: {str(e)}")

    # Method 3: Bounding box check
    try:
        bounding_box = await page.locator(selector).bounding_box()
        if bounding_box and bounding_box['width'] > 0 and bounding_box['height'] > 0:
            logger.info(f"Bounding box confirmed visibility for: {selector}")
            return True
    except Exception as e:
        logger.error(f"Bounding box check failed for {selector}: {str(e)}")

    # Method 4: Wait-based verification
    try:
        await page.wait_for_selector(selector, state="visible", timeout=3000)
        logger.info(f"Wait-based verification succeeded for: {selector}")
        return True
    except Exception as e:
        logger.error(f"Wait-based verification failed for {selector}: {str(e)}")

    # Method 5: Element handle check
    try:
        handle = await page.locator(selector).element_handle()
        if handle:
            logger.info(f"Element handle confirmed existence for: {selector}")
            return True
    except Exception as e:
        logger.error(f"Element handle check failed for {selector}: {str(e)}")

    logger.warning(f"All visibility checks failed for: {selector}")
    return False


async def hover_with_fallback(page, selector):
    """
    Attempts to hover on an element using multiple methods.
    Returns True as soon as one hover method succeeds.
    """
    # Method 1: Basic Playwright hover
    try:
        await page.locator(selector).hover()
        logger.info("Basic hover succeeded")
        return True
    except Exception as e:
        logger.error(f"Basic hover failed: {str(e)}")

    # Method 2: Precise mouse movement
    try:
        box = await page.locator(selector).bounding_box()
        if box:
            await page.mouse.move(
                box['x'] + box['width'] / 2,
                box['y'] + box['height'] / 2,
                steps=20
            )
            logger.info("Precise mouse movement hover succeeded")
            return True
        else:
            logger.warning("No bounding box for precise mouse movement")
    except Exception as e:
        logger.error(f"Precise mouse movement hover failed: {str(e)}")

    # Method 3: Event dispatching
    try:
        await page.dispatch_event(selector, 'mouseover')
        await page.dispatch_event(selector, 'mousemove')
        logger.info("Event dispatch hover succeeded")
        return True
    except Exception as e:
        logger.error(f"Event dispatch hover failed: {str(e)}")

    # Method 4: JavaScript-based hover simulation
    try:
        await page.evaluate(f"""selector => {{
            const element = document.querySelector(selector);
            if (element) {{
                const mouseOverEvent = new MouseEvent('mouseover', {{
                    'view': window,
                    'bubbles': true,
                    'cancelable': true
                }});
                element.dispatchEvent(mouseOverEvent);

                const mouseMoveEvent = new MouseEvent('mousemove', {{
                    'view': window,
                    'bubbles': true,
                    'cancelable': true
                }});
                element.dispatchEvent(mouseMoveEvent);
            }}
        }}""", selector)
        logger.info("JavaScript simulation hover succeeded")
        return True
    except Exception as e:
        logger.error(f"JavaScript simulation hover failed: {str(e)}")

    logger.warning("All hover methods failed")
    return False


async def click_with_fallback(page, selector):
    """
    Attempts to click an element using multiple methods.
    Returns True as soon as one click method succeeds.
    """
    # Method 1: Basic Playwright click
    try:
        await page.locator(selector).click()
        logger.info("Method 1: Basic click succeeded")
        return True
    except Exception as e:
        logger.error(f"Method 1: Basic click failed - {str(e)}")

    # Method 2: Force click (bypass visibility checks)
    try:
        await page.locator(selector).click(force=True)
        logger.info("Method 2: Force click succeeded")
        return True
    except Exception as e:
        logger.error(f"Method 2: Force click failed - {str(e)}")

    # Method 3: Position-based click
    try:
        box = await page.locator(selector).bounding_box()
        if box:
            await page.mouse.click(
                box['x'] + box['width'] / 2,
                box['y'] + box['height'] / 2,
                steps=20,
                delay=100  # More human-like
            )
            logger.info("Method 3: Position-based click succeeded")
            return True
        else:
            logger.warning("Method 3: No bounding box for position-based click")
    except Exception as e:
        logger.error(f"Method 3: Position-based click failed - {str(e)}")

    # Method 4: JavaScript click simulation
    try:
        await page.evaluate(f"""selector => {{
            const element = document.querySelector(selector);
            if (element) {{
                element.click();
            }}
        }}""", selector)
        logger.info("Method 4: JavaScript click succeeded")
        return True
    except Exception as e:
        logger.error(f"Method 4: JavaScript click failed - {str(e)}")

    # Method 5: Double-click fallback
    try:
        await page.locator(selector).dblclick()
        logger.info("Method 5: Double-click succeeded")
        return True
    except Exception as e:
        logger.error(f"Method 5: Double-click failed - {str(e)}")

    # Method 6: Enter key simulation
    try:
        await page.locator(selector).focus()
        await page.keyboard.press("Enter")
        logger.info("Method 6: Enter key press succeeded")
        return True
    except Exception as e:
        logger.error(f"Method 6: Enter key press failed - {str(e)}")

    logger.warning("All click methods failed")
    return False


# authenticate
async def device_auth_confirmation(page, selector):
    # Define your selector (using both ID and class)
    try:
        url_pattern = "https://www.linkedin.com/checkpoint/challengesV2/**"
        checkbox_visible = await check_if_click_successful(page, selector, url_pattern)

        if checkbox_visible:
            logger.info("Remember me is visible")
            try:
                check_selector = await page.get_attribute(selector, 'value')
                if check_selector == 'false':
                    await click_with_fallback(page, selector)
            except Exception as e:
                logger.warning(f"Remember me click error {e}")

        else:
            count = 0
            while count <= 6:
                page.wait_for_load_state()
                url_pattern = "https://www.linkedin.com/feed/"
                selector = "div#global-nav-search.global-nav__search"
                feed_navigate = await check_if_click_successful(page, selector, url_pattern)
                if feed_navigate:
                    logger.info("Authentication complete now proceed to search")
                    return True

    except Exception as e:
        logger.error(f"Authentication failed {e}")


async def select_first_company_result(page, selector):
    """Hovers, selects and clicks the middle of the first company result"""
    # Define the main container selector
    company_container_selector = selector

    # Wait for results to load
    await page.wait_for_selector(company_container_selector, state="visible", timeout=15000)

    # Get the first company result
    first_company = page.locator(company_container_selector).first

    # Hover over the entire result area
    linked_area = first_company.locator("div.linked-area")
    await linked_area.hover()

    # Calculate and click the center position
    bbox = await linked_area.bounding_box()
    if bbox:
        center_x = bbox['x'] + bbox['width'] / 2
        center_y = bbox['y'] + bbox['height'] / 2

        # Click the exact center
        await page.mouse.click(center_x, center_y)

        # Wait for navigation to company page
        try:
            await page.wait_for_url(
                "https://www.linkedin.com/company/**",
                timeout=10000,
                wait_until="domcontentloaded"
            )
            return True
        except TimeoutError:
            logger.warning("Navigation to company page timed out")
            return False
    return False