# tiktok_boost.py
# platform : TikTok
# method   : automates zefoy.com
# runtime  : playwright — bundles its own chromium, zero selenium/chromedriver issues

import time
import random
import logging
import asyncio
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

log = logging.getLogger(__name__)

ZEFOY_URL = "https://zefoy.com"

SERVICE_LABELS = {
    "followers":     "followers",
    "views":         "views",
    "likes":         "likes",
    "shares":        "shares",
    "favorites":     "favorites",
    "comment_likes": "comment likes",
}

SERVICES = list(SERVICE_LABELS.keys())


def boost_tiktok(
    url: str,
    service: str = "followers",
    loops: int = 5,
    progress_cb=None,
) -> dict:
    results = {"sent": 0, "loops_done": 0, "errors": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ]
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        try:
            page.goto(ZEFOY_URL, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(2)

            # find the service container and click its button
            service_label = SERVICE_LABELS.get(service, service).lower()
            found = False

            containers = page.query_selector_all("div.col-sm-4, div.card")
            for c in containers:
                if service_label in (c.inner_text() or "").lower():
                    btn = c.query_selector("button")
                    if btn:
                        btn.click()
                        found = True
                        break

            if not found:
                results["errors"].append(
                    f"service '{service}' not found on zefoy today"
                )
                return results

            time.sleep(2)

            for i in range(loops):
                try:
                    inp = page.wait_for_selector(
                        "input[type='text']", timeout=12000
                    )
                    inp.fill("")
                    inp.type(url, delay=50)
                    time.sleep(random.uniform(0.8, 1.8))

                    submit = page.query_selector(
                        "button[type='button'].btn-primary, button.btn-success"
                    )
                    if submit:
                        submit.click()
                    time.sleep(random.uniform(3, 5))

                    content = page.content().lower()
                    if any(w in content for w in ("please wait", "cooldown", "timer")):
                        wait_msg = f"⏱ loop {i+1}: cooldown — waiting 65 s"
                        log.info(wait_msg)
                        if progress_cb:
                            progress_cb(wait_msg)
                        time.sleep(67)
                        try:
                            s2 = page.query_selector(
                                "button[type='button'].btn-primary, button.btn-success"
                            )
                            if s2:
                                s2.click()
                            time.sleep(4)
                        except Exception:
                            pass

                    results["loops_done"] += 1
                    results["sent"] += 50
                    done_msg = (
                        f"✅ loop {i+1}/{loops} — ~{results['sent']} {service} sent"
                    )
                    log.info(done_msg)
                    if progress_cb:
                        progress_cb(done_msg)

                    if i < loops - 1:
                        time.sleep(random.uniform(60, 70))

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
