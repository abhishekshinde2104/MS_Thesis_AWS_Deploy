from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import logging
import time
import os

# from ad_logging import start_logging, log_video_info
from csv_storage import store_data_in_csv
from utils import wait_for_page_load, extract_domain, current_time, take_element_screenshot, take_page_screenshot
from youtube_selectors import YOUTUBE_SELECTORS
from yt_config import summary_data

from updated_bannerclick.bannerclick.bannerdetection import init as bannerclick_init, run_all_for_domain

unique_ads = set()

def check_sponsored_link(driver):
    logging.info("Function: check_sponsored_link() -> Trying to check for sponosred link on the video player")
    try:
        # Locate the advertiser link using its ID or CSS selector
        sponsored_link_element = driver.find_element(By.CSS_SELECTOR, "div.ytp-visit-advertiser-link span.ytp-visit-advertiser-link__text")
        
        # Get the text inside the span element
        sponsored_link_text = sponsored_link_element.text
        logging.info(f"check_sponsored_link Sponsored link text: {sponsored_link_text}")
        if sponsored_link_text and sponsored_link_text not in unique_ads:
            unique_ads.add(sponsored_link_text)
            logging.info(f"check_sponsored_link function Sponsored link text found: {sponsored_link_text}")
            # logging.info(f"Sponsored link text found: {sponsored_link_text}")
        return sponsored_link_text
    except Exception as e:
        logging.error(f" Sponsored video link could not be found: {e}")
    return None


def detect_ads(driver):
    # for selector in YOUTUBE_SELECTORS:
    ad_elements_found = set()
    for selector in YOUTUBE_SELECTORS:
        ad_elements = driver.find_elements(By.CSS_SELECTOR, selector)
        
        if ad_elements:
            logging.info(f"Ad detected using selector: {selector}")
            # Iterate through detected ad elements
            for ad in ad_elements:
                href = ad.get_attribute("href")  # For link ads
                if href and href not in unique_ads:
                    unique_ads.add(href)
                    logging.info(f"New ad detected with URL: {href}")
                    ad_elements_found.add(ad)
                    # logging.info(f"New ad detected with URL: {href}")
                # else:
                #     # Find possible clickable elements within the ad container
                #     clickable_elements = ad.find_elements(By.CSS_SELECTOR, "a, button, div[role='link']")
                #     for clickable in clickable_elements:
                #         if clickable.is_displayed() and clickable.is_enabled():
                #             ad_elements_found.add(clickable)
                #             logging.info("Detected a clickable ad element within ad container.")
                
    # TODO: If no ad is detected, check for sponsored link
    if len(ad_elements_found) == 0:
        sponsored_link_text = check_sponsored_link(driver)
        if sponsored_link_text and sponsored_link_text not in unique_ads:
            unique_ads.add(sponsored_link_text)
            logging.info(f"Sponsored link detected: {sponsored_link_text}")
            sponsored_link_element = driver.find_element(By.CSS_SELECTOR, ".ytp-visit-advertiser-link")
            ad_elements_found.add(sponsored_link_element)

    if len(ad_elements_found) == 0:
        logging.warning("No clickable ad elements were found!")

    return ad_elements_found


# def click_on_detected_ads(driver, ad_elements, yt_screenshot_path):
    
#     ad_list = list(ad_elements)
#     logging.info(f"Ad elements found are:\t {ad_list}")
    
#     for i, ad in enumerate(ad_list):
#         take_element_screenshot(driver, ad, f"{yt_screenshot_path}/ad_{i}.png")
    
#     if ad_list:
#         clicked = False
#         for ad in ad_list:
#             if ad.is_displayed() and ad.is_enabled():
#                 ad.click()
#                 clicked = True
#                 take_element_screenshot(driver, ad, f"{yt_screenshot_path}/ad_clicked.png")
#                 break
#         if not clicked:
#             logging.warning(f"Clickable Ad element is not displayed or enabled.")
#     else:
    #     logging.warning("No Ad elements found.")
    #     return None
        
    # for i, ad in enumerate(ad_elements):
    #     try:
    #         if ad.is_displayed() and ad.is_enabled():
    #             ad.click()
    #             take_element_screenshot(driver, ad, f"{yt_screenshot_path}/ad_clicked_{i}.png")
    #             logging.info(f"Successfully clicked on ad {i}.")
    #             return  # Stop after a successful click
    #     except Exception as e:
    #         logging.warning(f"Failed to click on ad {i}: {e}")

    # logging.error("No clickable ad elements could be interacted with.")
    # raise Exception("No clickable ad elements found.")
    

def click_on_ad_and_capture_requests(video_id, driver, yt_url, yt_title, original_window, output_csv_path, landingchoice, timeout=10):
    
    base_path = os.path.dirname(output_csv_path)
    summary_txt_path = os.path.join(base_path, "summary.txt")
    yt_screenshot_path = os.path.join(base_path, "yt_screenshots", video_id)
    
    try:
        logging.info("Function: click_on_ad_and_capture_requests() -> Trying to detect ad....\n")
        
        ad_elements_found = detect_ads(driver)
        if ad_elements_found:
            # click_on_detected_ads(driver, ad_elements_found, yt_screenshot_path)
            ad_list = list(ad_elements_found)
            logging.info(f"Ad elements found are:\t {ad_list}")
            for i, ad in enumerate(ad_list):
                logging.info(f"Ad element {i} is {ad} and is displayed: {ad.is_displayed()} and is enabled: {ad.is_enabled()} \n Tag: {ad.tag_name} \n ID: {ad.get_attribute('id')} \n Class: {ad.get_attribute('class')} \n Outer HTML:\n{ad.get_attribute('outerHTML')}")
                take_element_screenshot(driver, ad, f"{yt_screenshot_path}/ad_{i}.png")   
            if ad_list:
                clicked = False
                for ad in ad_list:
                    if ad.is_displayed() and ad.is_enabled():
                        ad.click()
                        clicked = True
                        take_element_screenshot(driver, ad, f"{yt_screenshot_path}/ad_clicked.png")
                        break
                if not clicked:
                    logging.warning(f"Clickable Ad element is not displayed or enabled.")
            else:
                logging.warning("No Ad elements found.")
                return None
        else:
            logging.warning("No ad elements detected to click.")

        
        logging.info("Ad clicked ... \n Now storing (js)cookies, local/session storage and web requests for 'during' phase\n")
        
        
        # 7.b. Capture data 2: During ad click
        store_data_in_csv(timestamp=current_time(), video_id=video_id, phase='during', yt_url=yt_url, yt_title=yt_title, driver=driver, output_csv_path=output_csv_path)
        
        if len(driver.window_handles) > 1:
            # 7.c. Close youtube tabs and switch to landing page
            # Switch to the newly opened tab (landing page)
            WebDriverWait(driver, timeout).until(lambda d: len(d.window_handles) > 1)
            landing_handle = driver.window_handles[-1]
        
            # Close youtube tab # Not closing since in stateless mode i close the whole browser, and in stateful, i keep the browser open
            logging.info("Closing the YouTube tab...\n")
            driver.close()
        
            # Ensuring landing page url is stored
            # wait_for_page_load(driver)
            
            time.sleep(30)
        
            # 8. Driver handle on landing page
            logging.info(f"Switching driver handle to the Ad landing page\n")
            driver.switch_to.window(landing_handle)
        
            # Printing data of newly opened page
            landing_page_title = driver.title
            landing_page_url = driver.current_url
            landing_page_domain = extract_domain(landing_page_url)
            logging.info(f"New page title: {landing_page_title}")
            logging.info(f"Switched to the ad page: {landing_page_url}")
            
            if landing_page_url:
                summary_data["Total ad landing pages visited"] += 1
                summary_data["Successful ad interactions"] += 1
                if landing_page_domain not in summary_data["Unique ad landing pages"]:
                    summary_data["Unique ad landing count"] += 1
                    summary_data["Unique ad landing pages"].add(landing_page_domain)
        
            # 9. Sleeping 30 seconds
            logging.info("Sleeping for 30 seconds and storing cookies and web requests for phase 'landing'")
            time.sleep(15)
            store_data_in_csv(timestamp=current_time(), video_id=video_id, phase='landing', yt_url=yt_url, yt_title=yt_title, driver=driver, landing_page_url=landing_page_url, output_csv_path=output_csv_path)
            time.sleep(15)
        
        
            if landing_page_url is None:
                logging.info("Retrying to get landing page url")
                landing_page_url = driver.current_url
                landing_page_domain = extract_domain(landing_page_url)
                logging.info(f"New page title: {landing_page_title}")
                logging.info(f"Switched to the ad page: {landing_page_url}")
            
            # 10. Interacting with cookie banner on landing page
            logging.info(f"Trying to run bannerclick on {landing_page_url}....\n")
            # Integrate BannerClick
            bannerclick_init(web_driver=driver, domain=extract_domain(landing_page_url),season_dir= f"{base_path}/banner_screenshots/")
            # run_all_for_domain(DMN=extract_domain(landing_page_url), URL=landing_page_url)    
            run_all_for_domain(DMN=extract_domain(landing_page_url), URL=landing_page_url, CHOICE=landingchoice)
            logging.info(f"Bannerclick done for {landing_page_url}....\n")
            
            # 11. Sleeping 30 seconds
            time.sleep(15)
            take_page_screenshot(driver, f"{yt_screenshot_path}/ad_page.png")
            time.sleep(15)
            
            # 12. Refreshing the page
            driver.refresh()
            
            # 13. Sleeping 30 seconds
            time.sleep(15)
            logging.info("Sleeping for 30 seconds and storing requests for phase 'landing_refreshed'")
            store_data_in_csv(timestamp=current_time(), video_id=video_id, phase='landing_refreshed', yt_url=yt_url, yt_title=yt_title, driver=driver, landing_page_url=landing_page_url, output_csv_path=output_csv_path)
            time.sleep(15)
            
            logging.info("Closing the ad landing page...\n")
            driver.close()
            
            # Switching back to original window
            logging.info("Switching the driver handle over to original YouTube tab...\n")
            driver.switch_to.window(original_window)
            return landing_page_url
        
        else:
            logging.error("No new tab was opened after clicking on the ad.")
            return None
    
    except Exception as e:
        logging.error(f"Clickable Ad element cannot be found \t  : {e}")
