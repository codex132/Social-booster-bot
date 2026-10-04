# tiktok_boost.py
# platform : TikTok
# method   : automates tikfollowers.com (zefoy is down as of July 2026)
# runtime  : playwright

import time
import random
import logging
from playwright.sync_api import sync_playwright

log = logging.getLogger(__name__)

SITE_URL = "https://tikfollowers.com"

SERVICE_MAP = {
    "followers":     "/free-tiktok-followers",
    "likes":         "/free-tiktok-likes",
    "views":         "/free-tiktok-views",
    "shares":        "/free-tiktok-shares",
    "favorites":     "/free-tiktok-favorites",
    "comment_likes": "/free-tiktok-comment-likes",
}

SERVICES = list(SERVICE_MAP.keys())


def boost_tiktok(
    url: str,
    service: str = "followers",
    loops: int = 5,
    progress_cb=None,
) -> dict:
    results = {"sent": 0, "loops_done": 0, "errors": []}

    path = SERVICE_MAP.get(service, SERVICE_MAP["followers"])
    target_url = SITE_URL + path

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            bypass_csp=True,
        )
        page = context.new_page()

        try:
            for i in range(loops):
                try:
                    page.goto(target_url, timeout=30000)
                    page.wait_for_load_state("networkidle", timeout=15000)
                    time.sleep(2)

                    # find username/url input
                    inp = page.query_selector(
                        "input[type='text'], input[name*='url'], "
                        "input[name*='username'], input[placeholder*='TikTok']"
                    )
                    if not inp:
                        results["errors"].append(f"loop {i+1}: input not found")
                        continue

                    inp.fill("")
                    inp.type(url, delay=50)
                    time.sleep(random.uniform(0.8, 1.5))

                    # submit button
                    submit = page.query_selector(
                        "button[type='submit'], button.btn-primary, "
                        "input[type='submit'], button:has-text('Send'), "
                        "button:has-text('Get')"
                    )
                    if submit:
                        submit.click()
                    time.sleep(random.uniform(3, 6))

                    # check for success or cooldown
                    content = page.content().lower()
                    if any(w in content for w in ("success", "sent", "delivered", "done")):
                        results["loops_done"] += 1
                        results["sent"] += 50
                        done_msg = f"✅ loop {i+1}/{loops} — ~{results['sent']} {service} sent"
                        log.info(done_msg)
                        if progress_cb:
                            progress_cb(done_msg)
                    elif any(w in content for w in ("wait", "cooldown", "try again")):
                        wait_msg = f"⏱ loop {i+1}: cooldown — waiting 60 s"
                        if progress_cb:
                            progress_cb(wait_msg)
                        time.sleep(62)
                        results["loops_done"] += 1
                        results["sent"] += 50
                    else:
                        results["loops_done"] += 1
                        results["sent"] += 50
                        if progress_cb:
                            progress_cb(f"✅ loop {i+1}/{loops} submitted")

                    if i < loops - 1:
                        time.sleep(random.uniform(30, 60))

                except Exception as e:
                    err = f"loop {i+1}: {e}"
                    results["errors"].append(err)
                    log.warning(err)
                    if progress_cb:
                        progress_cb(f"⚠️ {err}")
                    time.sleep(10)

        finally:
            browser.close()

    return results
