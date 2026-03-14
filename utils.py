import os
import json
import time
import random
from pathlib import Path
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import logger, CHECKPOINT_PATH, SCREENSHOTS_DIR

def human_delay(min_sec=0.8, max_sec=2.5):
    """Sleeps for a random duration to mimic human navigation."""
    time.sleep(random.uniform(min_sec, max_sec))

def take_screenshot(driver, prefix="error"):
    """Saves a screenshot to the logs directory with a timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = SCREENSHOTS_DIR / f"{prefix}_{timestamp}.png"
    import config
    try:
        driver.save_screenshot(str(filepath))
        logger.info(f"Screenshot saved to: {filepath}")
        
        if hasattr(config, "CURRENT_JOB_ID"):
            latest_path = SCREENSHOTS_DIR / f"job_{config.CURRENT_JOB_ID}_latest.png"
            driver.save_screenshot(str(latest_path))
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {str(e)}")

def snapshot(driver):
    """Saves exclusively to the job_id latest.png for live streaming without cluttering history."""
    import config
    if hasattr(config, "CURRENT_JOB_ID"):
        latest_path = SCREENSHOTS_DIR / f"job_{config.CURRENT_JOB_ID}_latest.png"
        try:
            driver.save_screenshot(str(latest_path))
        except Exception:
            pass

def wait_for_element(driver, selector, by=By.CSS_SELECTOR, timeout=10, condition=EC.presence_of_element_located):
    """Explicit wait wrapper returning the located element."""
    try:
        return WebDriverWait(driver, timeout).until(condition((by, selector)))
    except TimeoutException:
        take_screenshot(driver, prefix="timeout")
        logger.error(f"Element not found within {timeout}s: {selector}")
        raise

# Resilient operations retry decorator for DOM/Network failures
def retry_web_action():
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((TimeoutException, WebDriverException)),
        reraise=True
    )

def read_checkpoint():
    """Reads the dict inside checkpoint.json if it exists."""
    if not CHECKPOINT_PATH.exists():
        return {}
    try:
        with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not read checkpoint file: {e}")
        return {}

def write_checkpoint(state_dict):
    """Writes standard dict to the checkpoint file."""
    try:
        with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
            json.dump(state_dict, f, indent=4)
    except Exception as e:
        logger.error(f"Failed writing checkpoint: {e}")

def get_failed_entries_from_checkpoint():
    """Returns list of specific dates that failed based on checkpoint."""
    state = read_checkpoint()
    return state.get("failed_dates", [])

def mark_date_success(date_str):
    """Removes a date from the checkpoint's failed list."""
    state = read_checkpoint()
    failed = state.get("failed_dates", [])
    if date_str in failed:
        failed.remove(date_str)
        state["failed_dates"] = failed
        write_checkpoint(state)

def mark_date_failed(date_str):
    """Adds a date to the checkpoint's failed list."""
    state = read_checkpoint()
    failed = state.get("failed_dates", [])
    if date_str not in failed:
        failed.append(date_str)
        state["failed_dates"] = failed
        write_checkpoint(state)
