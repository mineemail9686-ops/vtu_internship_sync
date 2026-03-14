import time
import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from config import (
    logger, DIARY_CREATE_URL, LOGIN_URL_A1, LOGIN_URL_A2,
    ACCOUNT1_USER, ACCOUNT1_PASS, ACCOUNT2_USER, ACCOUNT2_PASS,
    SEL_FORM_SUMMARY, SEL_FORM_HOURS, SEL_FORM_LINKS, 
    SEL_FORM_LEARNINGS, SEL_FORM_BLOCKERS
)
from login import login, get_driver
from utils import wait_for_element, human_delay, take_screenshot, retry_web_action
from scraper import scrape_account_entries

# Template Default Values provided by user
DEFAULT_INTERNSHIP = "Bharat Unnati AI Fellowship(CodeXpert + Expertpedia + GenAI + Agentic AI)"
DEFAULT_HOURS = "8"
DEFAULT_BLOCKERS = "—"
DEFAULT_SKILLS = ["CodeIgniter", "Xcode"]

@retry_web_action()
def pick_date_and_continue(driver, date_str):
    logger.info(f"Navigating to calendar for {date_str}...")
    driver.get(DIARY_CREATE_URL)
    human_delay(3.0, 5.0)
    
    # 1. Select Internship if accessible
    try:
        internship_btn = wait_for_element(driver, "internship_id", By.ID, timeout=5)
        internship_btn.click()
        time.sleep(1)
        ActionChains(driver).send_keys(Keys.DOWN).send_keys(Keys.ENTER).perform()
        time.sleep(1)
    except Exception as e:
        logger.debug(f"Internship dropdown not found or handled: {e}")

    # 2. Pick a Date
    try:
        date_btns = driver.find_elements(By.XPATH, "//button[contains(., 'Pick a Date') or @data-slot='popover-trigger']")
        if date_btns:
            date_btns[0].click()
            time.sleep(1)
            
            target_dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            target_month = target_dt.strftime("%B")
            
            # Go backward
            for _ in range(12):
                caption_elements = driver.find_elements(By.CSS_SELECTOR, "[aria-live='polite']")
                caption = caption_elements[0].text if caption_elements else ""
                if target_month in caption and str(target_dt.year) in caption:
                    break
                
                prev_btns = (
                    driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'previous')]") or
                    driver.find_elements(By.XPATH, "//button[@name='previous-month']") or
                    driver.find_elements(By.XPATH, "//button[contains(@class, 'rdp-nav_button_previous')]")
                )
                if prev_btns:
                    prev_btns[0].click()
                    time.sleep(1)
                else:
                    break

            # Click the exact day
            data_day_str = f"{target_dt.month}/{target_dt.day}/{target_dt.year}"
            for _ in range(12):
                day_btns = driver.find_elements(By.CSS_SELECTOR, f"button[data-day='{data_day_str}']")
                if day_btns:
                    break
                
                prev_month_btn = driver.find_elements(By.CSS_SELECTOR, "button.rdp-button_previous, button[aria-label='Go to the Previous Month']")
                if prev_month_btn and prev_month_btn[0].get_attribute("disabled") is None:
                    try:
                        prev_month_btn[0].click()
                    except:
                        driver.execute_script("arguments[0].click();", prev_month_btn[0])
                    time.sleep(0.8)
                else:
                    break
            
            day_btns = driver.find_elements(By.CSS_SELECTOR, f"button[data-day='{data_day_str}']")
            if day_btns:
                try:
                    ActionChains(driver).move_to_element(day_btns[-1]).click().perform()
                except:
                    driver.execute_script("arguments[0].click();", day_btns[-1])
                time.sleep(1)
            else:
                raise Exception(f"Could not find day button for {date_str}!")
    except Exception as e:
        logger.warning(f"Failed handling calendar for {date_str}. (Might be a Sunday/Holiday): {e}")
        raise

    # 3. Hit Continue
    con_btn = wait_for_element(driver, "//button[text()='Continue']", By.XPATH, timeout=5)
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(1)
    
    try:
        con_btn.click()
    except:
        try:
            driver.execute_script("arguments[0].click();", con_btn)
        except:
            pass
    human_delay(3.0, 5.0)

def extract_form_data(driver):
    """Extracts existing data from the form. Returns None if empty."""
    try:
        summary_ele = wait_for_element(driver, SEL_FORM_SUMMARY, By.CSS_SELECTOR, timeout=5)
        summary_val = summary_ele.get_attribute('value') or summary_ele.text
        
        hours_ele = driver.find_element(By.CSS_SELECTOR, SEL_FORM_HOURS)
        hours_val = hours_ele.get_attribute('value')
        
        learnings_ele = driver.find_element(By.CSS_SELECTOR, SEL_FORM_LEARNINGS)
        learnings_val = learnings_ele.get_attribute('value') or learnings_ele.text
        
        blockers_ele = driver.find_element(By.CSS_SELECTOR, SEL_FORM_BLOCKERS)
        blockers_val = blockers_ele.get_attribute('value') or blockers_ele.text
        
        if not summary_val.strip():
            return None
            
        return {
            'work_summary': summary_val.strip(),
            'hours_worked': hours_val.strip() if hours_val else '',
            'learnings': learnings_val.strip(),
            'blockers': blockers_val.strip()
        }
    except Exception as e:
        logger.debug(f"Form data extraction failed (likely empty): {e}")
        return None

def fill_and_save_form(driver, entry_data):
    """Locates fields, clears them, fills text, and hits Save."""
    def _fill(selector, text):
        try:
            ele = wait_for_element(driver, selector, By.CSS_SELECTOR, timeout=5)
            ele.clear()
            ele.send_keys(str(text))
            human_delay(0.5, 1.2)
        except Exception as e:
            logger.warning(f"Could not fill {selector}: {e}")

    _fill(SEL_FORM_SUMMARY, entry_data.get('work_summary', ''))
    _fill(SEL_FORM_HOURS, entry_data.get('hours_worked', DEFAULT_HOURS))
    _fill(SEL_FORM_LEARNINGS, entry_data.get('learnings', ''))
    _fill(SEL_FORM_BLOCKERS, entry_data.get('blockers', DEFAULT_BLOCKERS))
    try:
        _fill(SEL_FORM_LINKS, "")
    except: pass

    # Try to select the specific Skills
    try:
        skills_inputs = driver.find_elements(By.CSS_SELECTOR, "input[id^='react-select-']")
        if skills_inputs:
            for skill in DEFAULT_SKILLS:
                skills_inputs[0].click()
                time.sleep(0.5)
                skills_inputs[0].send_keys(skill)
                time.sleep(1)
                ActionChains(driver).send_keys(Keys.ENTER).perform()
                time.sleep(1)
    except Exception as e:
        logger.debug(f"Could not enter skills: {e}")

    try:
        save_btns = driver.find_elements(By.XPATH, "//button[text()='Save' or text()='Submit' or text()='Update']")
        if save_btns:
            try:
                save_btns[0].click()
            except:
                driver.execute_script("arguments[0].click();", save_btns[0])
    except Exception as e:
        logger.error(f"Save button error: {e}")
        raise

    human_delay(3.0, 5.0)

def main():
    print("Welcome to the VTU Deep Sync Script")
    start_date_str = input("Enter the start date (YYYY-MM-DD) [e.g., 2026-01-23]: ").strip()
    end_date_str = input("Enter the end date (YYYY-MM-DD) [e.g., 2026-03-13]: ").strip()
    
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()

    dates_to_sync = []
    curr = start_date
    while curr <= end_date:
        dates_to_sync.append(curr.strftime("%Y-%m-%d"))
        curr += datetime.timedelta(days=1)

    logger.info("=== Phase 1: Scraping Account 2 ===")
    driver2 = get_driver(headless=False)
    source_data_map = {}
    try:
        login(driver2, LOGIN_URL_A2, ACCOUNT2_USER, ACCOUNT2_PASS)
        # Attempt to get data from list view first to speed things up
        try:
            list_entries = scrape_account_entries(driver2, save_to_disk=False)
            for e in list_entries:
                if e['date'] in dates_to_sync:
                    source_data_map[e['date']] = {
                        'work_summary': e['work_summary'],
                        'hours_worked': DEFAULT_HOURS,
                        'learnings': e.get('work_summary', ''),  # Use summary as learnings
                        'blockers': DEFAULT_BLOCKERS
                    }
        except Exception as e:
            logger.warning(f"Failed to scrape list entries. Proceeding solely with calendar form: {e}")
        
        # Check calendar for missing dates
        for d in dates_to_sync:
            if d not in source_data_map:
                logger.info(f"Date {d} not found in List. Checking Calendar form...")
                try:
                    pick_date_and_continue(driver2, d)
                    f_data = extract_form_data(driver2)
                    if f_data:
                        logger.info(f"Found data inside form for {d}!")
                        source_data_map[d] = f_data
                    else:
                        logger.info(f"No data for {d} in source account.")
                except Exception as e:
                    logger.debug(f"Failed to check form for {d} (might be holiday): {e}")
    finally:
        driver2.quit()

    logger.info("=== Phase 2: Updating Account 1 ===")
    driver1 = get_driver(headless=False)
    try:
        login(driver1, LOGIN_URL_A1, ACCOUNT1_USER, ACCOUNT1_PASS)
        for d in dates_to_sync:
            if d not in source_data_map:
                logger.info(f"Skipping {d}: No source data found in Account 2.")
                continue

            target_data = source_data_map[d]
            
            logger.info(f"Checking Account 1 calendar for {d}...")
            try:
                pick_date_and_continue(driver1, d)
                curr_data = extract_form_data(driver1)
                
                needs_update = False
                if not curr_data:
                    logger.info(f"{d} is empty in Account 1. Proceeding to fill.")
                    needs_update = True
                else:
                    # check if diff
                    if curr_data['work_summary'] != target_data['work_summary'] or str(curr_data['hours_worked']) != str(target_data['hours_worked']):
                        logger.info(f"{d} has differing data in Account 1. Overwriting...")
                        needs_update = True
                    else:
                        logger.info(f"{d} data matches perfectly. Skipping save.")

                if needs_update:
                    fill_and_save_form(driver1, target_data)
                    logger.info(f"Saved {d}!")
                    
            except Exception as e:
                logger.warning(f"Error while syncing {d} to Account 1: {e}")
                take_screenshot(driver1, prefix=f"deep_sync_err_{d}")
    finally:
        driver1.quit()
        
    logger.info("=== Deep Sync Complete ===")

if __name__ == "__main__":
    main()
