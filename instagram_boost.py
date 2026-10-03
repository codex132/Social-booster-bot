# instagram_boost.py
# platform : Instagram
# method   : follow-back
# python   : 3.13 compatible

import time
import random
import logging
import shutil

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

log = logging.getLogger(__name__)

IG_BASE = "https://www.instagram.com"


def _make_driver() -> webdriver.Chrome:
    chromium_bin = (
        shutil.which("chromium")
        or shutil.which("chromium-browser")
        or "/usr/bin/chromium"
    )
    chromedriver_bin = (
        shutil.which("chromedriver")
        or "/usr/bin/chromedriver"
    )

    opts = Options()
    opts.binary_location = chromium_bin
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=375,812")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/16.6 Mobile/15E148 Safari/604.1"
    )
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    service = Service(executable_path=chromedriver_bin)
    driver = webdriver.Chrome(service=service, options=opts)
    return driver


def _login(driver, username: str, password: str) -> bool:
    driver.get(f"{IG_BASE}/accounts/login/")
    time.sleep(3)
    try:
        u = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        u.send_keys(username)
        p = driver.find_element(By.NAME, "password")
        p.send_keys(password)
        time.sleep(random.uniform(0.8, 1.5))
        p.submit()
        time.sleep(6)
        for text in ("Not Now", "Not now", "Skip"):
            try:
                driver.find_element(
                    By.XPATH, f"//button[text()='{text}']"
                ).click()
                time.sleep(2)
                break
            except Exception:
                pass
        return True
    except Exception as e:
        log.error(f"IG login error: {e}")
        return False


def boost_instagram(
    username: str,
    password: str,
    target_account: str,
    follow_count: int = 50,
    progress_cb=None,
) -> dict:
    results = {"followed": 0, "skipped": 0, "errors": []}
    driver = _make_driver()

    try:
        if not _login(driver, username, password):
            results["errors"].append(
                "login failed — check IG_USERNAME / IG_PASSWORD in env"
            )
            return results

        driver.get(f"{IG_BASE}/{target_account}/")
        time.sleep(4)

        try:
            fol_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(@href,'/followers/')]")
                )
            )
            fol_link.click()
            time.sleep(3)
        except Exception:
            try:
                driver.find_element(
                    By.XPATH, "//span[contains(text(),'followers')]"
                ).click()
                time.sleep(3)
            except Exception as e:
                results["errors"].append(f"could not open followers modal: {e}")
                return results

        followed = 0

        while followed < follow_count:
            btns = driver.find_elements(
                By.XPATH, "//button[normalize-space(text())='Follow']"
            )

            if not btns:
                try:
                    modal = driver.find_element(
                        By.XPATH, "//div[@role='dialog']"
                    )
                    driver.execute_script(
                        "arguments[0].scrollTop = arguments[0].scrollHeight",
                        modal
                    )
                except Exception:
                    driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight)"
                    )
                time.sleep(2)
                btns = driver.find_elements(
                    By.XPATH, "//button[normalize-space(text())='Follow']"
                )

            for btn in btns:
                if followed >= follow_count:
                    break
                try:
                    driver.execute_script(
                        "arguments[0].scrollIntoView(true);", btn
                    )
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

            try:
                modal = driver.find_element(
                    By.XPATH, "//div[@role='dialog']"
                )
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight",
                    modal
                )
            except Exception:
                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight)"
                )
            time.sleep(2)

    finally:
        try:
            driver.quit()
        except Exception:
            pass

    return results
