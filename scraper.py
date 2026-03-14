import pandas as pd
import json
import time
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from config import (
    logger, JSON_DATA_PATH, CSV_DATA_PATH, DIARY_VIEW_URL,
    SEL_DIARY_ROW
)
from utils import wait_for_element, human_delay, take_screenshot, retry_web_action, snapshot

@retry_web_action()
def navigate_to_diary(driver):
    logger.info(f"Navigating to view diary page: {DIARY_VIEW_URL}")
    driver.get(DIARY_VIEW_URL)
    human_delay(3.0, 5.0)
    
    # Simple explicit wait to ensure table loads
    wait_for_element(driver, SEL_DIARY_ROW, By.CSS_SELECTOR, timeout=20)
    snapshot(driver)

def extract_entries_from_html(html_page):
    """Uses BeautifulSoup to parse the diary table."""
    soup = BeautifulSoup(html_page, 'html.parser')
    rows = soup.select(SEL_DIARY_ROW)
    
    entries = []
    for row in rows:
        try:
            cols = row.find_all('td')
            if len(cols) >= 2:
                date_val = cols[0].get_text(strip=True)
                summary_val = cols[1].get_text(strip=True)
                
                # The table on vtu doesn't show hours or learnings, so we default and mirror.
                # When updating, we will use the summary as learnings too, and default hours to 8.
                if date_val:
                    entries.append({
                        "date": date_val,
                        "work_summary": summary_val,
                        "hours_worked": 8.0,
                        "learnings": summary_val, 
                    })
        except Exception as e:
            logger.warning(f"Failed to parse a row in diary table: {e}")
            continue
            
    return entries

def scrape_account_entries(driver, save_to_disk=False):
    logger.info("Starting scrape of diary entries...")
    try:
        navigate_to_diary(driver)
        html_page = driver.page_source
        entries = extract_entries_from_html(html_page)
        
        logger.info(f"Scraped {len(entries)} entries successfully.")
        snapshot(driver)
        
        if save_to_disk and entries:
            with open(JSON_DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(entries, f, indent=4)
            df = pd.DataFrame(entries)
            df.to_csv(CSV_DATA_PATH, index=False)
            
        return entries
    except Exception as e:
        take_screenshot(driver, prefix="scrape_error")
        logger.error(f"Failed during scrape operation: {e}")
        raise
