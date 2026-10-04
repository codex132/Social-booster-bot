# instagram_boost.py
# platform : Instagram — playwright version

import time
import random
import logging
from playwright.sync_api import sync_playwright

log = logging.getLogger(__name__)

IG_BASE = "https://www.instagram.com"


def boost_instagram(
    username: str,
    password: str,
    target_account: str,
    follow_count: int = 50,
    progress_cb=None,
) -> dict:
    results = {"followed": 0, "skipped": 0, "errors": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/16.6 Mobile/15E148 Safari/604.1"
            ),
            viewport={"width": 375, "height": 812},
        )
        page = context.new_page()

        try:
            page.goto(f"{IG_BASE}/accounts/login/", timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(3)

            page.fill("input[name='username']", username)
            page.fill("input[name='password']", password)
            time.sleep(random.uniform(0.8, 1.5))
            page.keyboard.press("Enter")
            time.sleep(6)

            for text in ("Not Now", "Not now", "Skip"):
                try:
                    btn = page.query_selector(f"button:has-text('{text}')")
                    if btn:
                        btn.click()
                        time.sleep(2)
                        break
                except Exception:
                    pass

            page.goto(f"{IG_BASE}/{target_account}/", timeout=30000)
            time.sleep(4)

            try:
                fol = page.query_selector("a[href*='/followers/']")
                if fol:
                    fol.click()
                    time.sleep(3)
            except Exception as e:
                results["errors"].append(f"could not open followers modal: {e}")
                return results

            followed = 0
            while followed < follow_count:
                btns = page.query_selector_all("button:has-text('Follow')")

                if not btns:
                    page.evaluate(
                        "document.querySelector('[role=dialog]')?.scrollBy(0,500)"
                        " || window.scrollBy(0,500)"
                    )
                    time.sleep(2)
                    btns = page.query_selector_all("button:has-text('Follow')")

                for btn in btns:
                    if followed >= follow_count:
                        break
                    try:
                        btn.scroll_into_view_if_needed()
                        time.sleep(0.5)
                        btn.click()
                        followed += 1
                        results["followed"] += 1
                        msg = f"✅ followed {followed}/{follow_count}"
                        log.info(msg)
                        if progress_cb:
                            progress_cb(msg)
                        time.sleep(random.uniform(15, 45))
                    except Exception as e:
                        results["skipped"] += 1
                        log.warning(f"skip: {e}")

                page.evaluate(
                    "document.querySelector('[role=dialog]')?.scrollBy(0,500)"
                    " || window.scrollBy(0,500)"
                )
                time.sleep(2)

        finally:
            browser.close()

    return results
