# tiktok_boost.py
# platform : TikTok
# method   : automates zefoy.com — no API key, no payment, no login
# services : followers, views, likes, shares, favorites, comment_likes

import time
import random
import logging
import shutil
import os

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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


def _make_driver() -> uc.Chrome:
    chromium_bin = (
        shutil.which("chromium")
        or shutil.which("chromium-browser")
        or "/usr/bin/chromium"
    )
    chromedriver_bin = (
        shutil.which("chromedriver")
        or "/usr/bin/chromedriver"
    )

    opts = uc.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,800")

    driver = uc.Chrome(
        options=opts,
        browser_executable_path=chromium_bin,
        driver_executable_path=chromedriver_bin,
        use_subprocess=False,
    )
    return driver


def _find_service_btn(driver, service: str):
    label = SERVICE_LABELS.get(service, service).lower()
    containers = driver.find_elements(By.CSS_SELECTOR, "div.col-sm-4, div.card")
    for c in containers:
        if label in c.text.lower():
            btns = c.find_elements(By.TAG_NAME, "button")
            if btns:
                return btns[0]
    return None


def boost_tiktok(
    url: str,
    service: str = "followers",
    loops: int = 5,
    progress_cb=None,
) -> dict:
    results = {"sent": 0, "loops_done": 0, "errors": []}
    driver = _make_driver()

    try:
        driver.get(ZEFOY_URL)
        time.sleep(4)

        WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.col-sm-4, div.card"))
        )

        btn = _find_service_btn(driver, service)
        if not btn:
            results["errors"].append(f"service '{service}' not found on zefoy today")
            return results

        btn.click()
        time.sleep(2)

        for i in range(loops):
            try:
                inp = WebDriverWait(driver, 12).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "input[type='text']")
                    )
                )
                inp.clear()
                inp.send_keys(url)
                time.sleep(random.uniform(0.8, 1.8))

                submit = driver.find_element(
                    By.CSS_SELECTOR,
                    "button[type='button'].btn-primary, button.btn-success"
                )
                submit.click()
                time.sleep(random.uniform(3, 5))

                src = driver.page_source.lower()
                if "please wait" in src or "cooldown" in src or "timer" in src:
                    wait_msg = f"⏱ loop {i+1}: cooldown — waiting 65 s"
                    log.info(wait_msg)
                    if progress_cb:
                        progress_cb(wait_msg)
                    time.sleep(67)
                    try:
                        s2 = driver.find_element(
                            By.CSS_SELECTOR,
                            "button[type='button'].btn-primary, button.btn-success"
                        )
                        s2.click()
                        time.sleep(4)
                    except Exception:
                        pass

                results["loops_done"] += 1
                results["sent"] += 50
                done_msg = f"✅ loop {i+1}/{loops} — ~{results['sent']} {service} sent"
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
        try:
            driver.quit()
        except Exception:
            pass

    return results
