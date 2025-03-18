# from selenium import webdriver
from seleniumwire import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import TimeoutException

# import undetected_chromedriver as uc


import os
import uuid
import json
import time
import argparse
import logging
from datetime import datetime


from yt_api import youtube_api_call
from ad_click import click_on_ad_and_capture_requests
from csv_storage import initialize_csv, store_data_in_csv
from utils import capture_browser_data, wait_for_page_load, extract_domain, play_pause_button_click, current_time, take_page_screenshot, take_element_screenshot
from yt_logging import start_logging, log_video_info
from yt_config import summary_data
from db_storage import initialize_db, store_csv_in_db

# TODO: Bannerclick
from updated_bannerclick.bannerclick.bannerdetection import init as bannerclick_init, run_all_for_domain


def setup_measurement_directory():
    """
    Create a new directory structure for storing measurement data.
    """
    # run_id = str(uuid.uuid4())
    run_id = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    
    os.makedirs("yt_measurements", exist_ok=True)
    
    base_path = os.path.join("yt_measurements", f"{run_id}")
    os.makedirs(base_path, exist_ok=True)
    
    # os.makedirs(os.path.join(base_path, "banner_screenshots", "youtube"), exist_ok=True)
    # os.makedirs(os.path.join(base_path, "banner_screenshots", "ad_landing"), exist_ok=True)

    session_csv_path = os.path.join(base_path, "session.csv")
    session_db_path = os.path.join(base_path, "measurements.db")
    summary_txt_path = os.path.join(base_path, "summary.txt")
    logfile_path = os.path.join(base_path, "logfile.log")
    browser_profile_path = os.path.join(base_path, "browser_profile")

    return run_id, base_path, session_csv_path, session_db_path, summary_txt_path, logfile_path, browser_profile_path


def write_summary(summary_txt_path, summary_data):
    """
    Write measurement summary details to a text file.
    """
    with open(summary_txt_path, 'w') as f:
        f.write("YouTube Ad Measurement Summary\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for key, value in summary_data.items():
            f.write(f"{key}: {value}\n")
        

def setup_webdriver(browser, headless=True, stateful=False, browser_profile_path=None):
    """
    Set up the WebDriver based on the selected browser and headless mode.
    """
    logging.info(f"Setting up WebDriver for browser: {browser}")
    
    if browser == "firefox":
        options = FirefoxOptions()
        if stateful and browser_profile_path:
            os.makedirs(browser_profile_path, exist_ok=True)
            # 1. Profile 
            # options.add_argument(f"-profile {browser_profile_path}")
            
            # 2. Profile
            # options.set_preference("profile", browser_profile_path)
            
            # 3. Profile
            firefox_profile = FirefoxProfile(profile_directory="D:\\Saarland University\\Master's Thesis\\February 2025\\Firefox profiles\\61storpa.profile1")
            options.profile = firefox_profile
            
            logging.info(f"Using Firefox profile path: {browser_profile_path}")
        if headless:
            options.add_argument("--headless") 
        # options.set_preference("intl.accept_languages", "en-US, en")

        # Set the path to geckodriver (Firefox driver)
        geckodriver_path = 'drivers\\geckodriver.exe'
        logging.info(f"Using geckodriver path: {geckodriver_path}")
        
        try:
            service = FirefoxService(executable_path=geckodriver_path)
            driver = webdriver.Firefox(service=service, options=options)
            logging.info("Firefox WebDriver initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing Firefox WebDriver: {e}")
            raise
    
    # elif browser == "chrome":
    #     options = uc.ChromeOptions()
        
    #     if headless:
    #         options.add_argument("--headless")
            
    #     try:
    #         driver = uc.Chrome(use_subprocess=False,options=options,seleniumwire_options={})
    #         logging.info("Chrome WebDriver initialized successfully.")
    #     except Exception as e:
    #         logging.error(f"Error initializing Chrome WebDriver: {e}")
    #         raise   
        
         
    elif browser == "chrome":
        options = ChromeOptions()
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        chrome_driver_path = "drivers\\chromedriver.exe"
        if headless:
            options.add_argument("--headless")
        logging.info(f"Using Chrome Webdriver")
        try: 
            service = ChromeService(chrome_driver_path)
            driver = webdriver.Chrome(options=options)
            logging.info("Chrome WebDriver initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing Chrome WebDriver: {e}")
            raise
        
    elif browser == 'brave':
        options = ChromeOptions()
        try:
            options.binary_location = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
            driver = webdriver.Chrome(options=options)
            logging.info("Brave WebDriver initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing Brave WebDriver: {e}")
    
    elif browser == 'edge':
        options = webdriver.EdgeOptions()
        if headless:
            options.add_argument('--headless')
        try:
            # service = webdriver.EdgeService(edge_path)
            driver = webdriver.Edge(options=options)
            logging.info("Edge WebDriver initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing Edge WebDriver: {e}")
        
    elif browser == 'duckduckgo':
        options = ChromeOptions()
        try:
            options.binary_location = "C:\\Users\\Abhishek Shinde\\AppData\\Local\\Microsoft\\WindowsApps\\DuckDuckGo.exe"
            driver = webdriver.Chrome(options=options)
            logging.info("DuckDuckGo WebDriver initialized successfully.")
        except Exception as e:
            logging.error(f"Error initializing DuckDuckGo WebDriver: {e}")
    
    
    else:
        raise ValueError(f"Unsupported browser: {browser}")
    
    driver.maximize_window()
    return driver


def close_browser(driver):
    driver.quit()


def main(browser, country, ytMaxResults, choice, landingchoice, headless, stateful):
    """
    Main function which starts the browser - visits youtube videos - perform measurements - closes browser
    """
    
    # 1. Setup measurement directory
    run_id, base_path, session_csv_path, session_db_path, summary_txt_path, logfile_path, browser_profile_path = setup_measurement_directory() 
    
    # Setup logging before further processing
    start_logging(logfile_path)
    
    # Get the combined videos for 3 days:
    videos_json_path = "videos_to_watch.json"

    try:
        with open(videos_json_path, "r", encoding="utf-8") as file:
            unique_videos = json.load(file)
    except FileNotFoundError:
        logging.warning(f"{videos_json_path} not found. Proceeding without it.")
        unique_videos = {}
    
    try: 

        logging.info("Script started with the following command-line arguments:")
        # logging.info(f"Output CSV file: {args.outfile}")
        logging.info(f"Country: {country}")
        logging.info(f"Youtube Cookie Banner Choice: {choice}")
        logging.info(f"Ad Landing Page Cookie Banner Choice: {landingchoice}")
        logging.info(f"Browser: {browser}")
        logging.info(f"YouTube video to be watched : {ytMaxResults}")
        logging.info(f"Headless mode: {'Enabled' if headless else 'Disabled'}")
        logging.info(f"Measurement Mode: {'Stateful' if stateful else 'Stateless'}")
        
        # HAD TODO: As requests and responses from seleniumwire were getting captured automatically, I had to suppress them
        # Suppress Selenium Wire logging by setting logging level to ERROR
        logging.getLogger('seleniumwire').setLevel(logging.ERROR)

        # Or redirect selenium-wire logs to null (disable completely)
        # logging.getLogger('seleniumwire').propagate = False
        
        # Initialize summary data
        summary_data["Number of videos watched"] = 0
        summary_data["Country"] = country
        summary_data["Browser"] = browser
        summary_data["Measurement mode"] = "Stateful" if stateful else "Stateless"
        summary_data["Headless mode"] = "Enabled" if headless else "Disabled"
        summary_data["YouTube banner choice"] = "Accept" if choice == 1 else "Reject"
        summary_data["Landing page banner choice"] = "Accept" if landingchoice == 1 else "Reject"
        summary_data["Successful ad interactions"] = 0
        summary_data["Total ad landing pages visited"] = 0
        summary_data["Unique ad landing count"] = 0
        summary_data["Unique ad landing pages"] = set()
        
        if stateful: 
            # 1. Initialize csv and database
            initialize_csv(session_csv_path)

            initialize_db(session_db_path)
            # 2. Get Trending Videos
            trending_videos = youtube_api_call(country=country, maxResults=ytMaxResults)
            logging.info(f"Length of Trending video is: \t {len(trending_videos)}")
            
            trending_videos = dict(list(trending_videos.items())[:])
            
            # Starting the browser instance
            driver = setup_webdriver(browser, headless=headless, stateful=stateful, browser_profile_path=browser_profile_path)
            
            # Opening youtube.com
            driver.get("https://youtube.com")
            
            #Waiting for page to load & Interacting with the cookie banner 
            # wait_for_page_load(driver)
            
            # 2. 
            logging.info("Sleeping for 30 seconds and storing requests for phase 'yt'")
            time.sleep(15)
            store_data_in_csv(timestamp=current_time(),video_id=run_id+"_stateful", phase='yt', yt_url="https://www.youtube.com", yt_title=None, driver=driver, output_csv_path=session_csv_path)
            time.sleep(15)
            
            # 3. Interacting with cookie banner
            logging.info(f"Trying to run bannerclick on youtube.com")
            # Integrate BannerClick
            bannerclick_init(web_driver=driver, domain=extract_domain("https://www.youtube.com"),season_dir=f"{base_path}/banner_screenshots/")
            # run_all_for_domain(DMN=extract_domain(video_url), URL=video_url)
            run_all_for_domain(DMN=extract_domain("https://www.youtube.com"), URL="https://www.youtube.com", CHOICE=choice)
            logging.info(f"Bannerclick done for youtube.com")
            
            for i in range(0, len(trending_videos)):
                video_id = list(trending_videos.keys())[i]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                video_title = list(trending_videos.values())[i]
                
                time.sleep(2)
                
                log_video_info(video_url, video_title)
            
                try: 
                    driver.get(video_url)
                except TimeoutException:
                    logging.error(f"Timeout occurred, for video with url : {video_url} retrying in 10 seconds...")
                    time.sleep(10)
                    driver.get(video_url)  # Retry once
                    
                summary_data["Number of videos watched"] += 1  # Increment video count
                logging.info(f"Storing requests for phase 'yt_video' for video url is: \t {video_url} ")
                store_data_in_csv(timestamp=current_time(), video_id=video_id,phase='yt_video', yt_url=video_url, yt_title=video_title, driver=driver, output_csv_path=session_csv_path)        
                play_pause_button_click(driver)
                
                # Take screenshot of the youtube page
                yt_screenshot_path = os.path.join(base_path, "yt_screenshots", video_id)
                os.makedirs(yt_screenshot_path, exist_ok=True)
                take_page_screenshot(driver, f"{yt_screenshot_path}/{video_id}.png")
                
                # To avoid bot detection
                driver.execute_script("window.scrollBy(0, 300);")
                
                # current window handle i.e., youtube tab
                original_window = driver.current_window_handle
                landing_page_url = click_on_ad_and_capture_requests(video_id, driver, video_url, video_title, original_window, output_csv_path=session_csv_path, landingchoice=landingchoice)

                
                # 4. Sleeping 10 seconds
                # logging.info("Sleeping for 10 seconds and then refreshing the page")
                # time.sleep(10)
                
                # 5. Refreshing the youtube page YOUTUBE VIDEO STOPS, SO YOU HAVE TO CLICK; ALSO THE VIDEO AD BANNER DISAPPEARS AND ONLY ONE SPONSORED AD IS SHOWN
                # driver.requests.clear()
                # driver.refresh()
                
                # 6. Waiting 30 seconds
                # logging.info("Sleeping for 30 seconds and storing requests for phase 'yt_refreshed_after_ad_visit'")
                # time.sleep(15)
                # store_data_in_csv(timestamp=current_time(), video_id=video_id,phase='yt_refreshed_after_ad_visit', yt_url=video_url, yt_title=video_title, driver=driver, landing_page_url=landing_page_url, output_csv_path=session_csv_path)        
                # TODO: Check if this has to be done here of later
                # play_pause_button_click(driver)
                time.sleep(15)
                
                # Updating summary after each video
                write_summary(summary_txt_path, summary_data)

                # Clear requests after each video
                #driver.requests.clear()
            # close the browser
            close_browser(driver)
        
        # STATELESS    
        else: 
        
            # 2. Initialize csv
            initialize_csv(session_csv_path)
            
            # 3. Initialize database
            initialize_db(session_db_path)
            
            # 4. Get Trending Videos

            # trending_videos = youtube_api_call(country=country, maxResults=ytMaxResults)
            trending_videos = {**unique_videos}
            logging.info(f"Length of Trending video is: \t {len(trending_videos)}")
            
            trending_videos = dict(list(trending_videos.items())[:])
            
            for i in range(0, len(trending_videos)):
                video_id = list(trending_videos.keys())[i]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                video_title = list(trending_videos.values())[i]
                
                time.sleep(2)
                
                # Starting the browser instance
                driver = setup_webdriver(browser, headless=headless)
                
                log_video_info(video_url, video_title)
                
                # Not TODO: If I directly go to the video link, I can't get ads being played, they are auto skipped by the time we sleep
                # Opening youtube.com
                try:
                    driver.get("https://youtube.com")
                except TimeoutException:
                    logging.error(f"Timeout occurred, for https://youtube.com : retrying in 10 seconds...")
                    time.sleep(10)
                    driver.get("https://youtube.com")
                
                #Waiting for page to load & Interacting with the cookie banner 
                # wait_for_page_load(driver)
                
                # 2. 
                logging.info("Sleeping for 30 seconds and storing requests for phase 'yt'")
                time.sleep(15)
                store_data_in_csv(timestamp=current_time(), video_id=video_id,phase='yt', yt_url=video_url, yt_title=video_title, driver=driver, output_csv_path=session_csv_path)
                time.sleep(15)
                
                # 3. Interacting with cookie banner
                logging.info(f"Trying to run bannerclick on youtube.com")
                # Integrate BannerClick
                bannerclick_init(web_driver=driver, domain=extract_domain(video_url),season_dir=f"{base_path}/banner_screenshots/")
                # run_all_for_domain(DMN=extract_domain(video_url), URL=video_url)
                run_all_for_domain(DMN=extract_domain(video_url), URL=video_url, CHOICE=choice)
                logging.info(f"Bannerclick done for youtube.com")

                time.sleep(30)
                
                try: 
                    driver.get(video_url)
                except TimeoutException:
                    logging.error(f"Timeout occurred, for video with url : {video_url} retrying in 10 seconds...")
                    time.sleep(10)
                    driver.get(video_url)  # Retry once
                    
                summary_data["Number of videos watched"] += 1  # Increment video count
                logging.info(f"Storing requests for phase 'yt_video' for video url is: \t {video_url} ")
                store_data_in_csv(timestamp=current_time(), video_id=video_id,phase='yt_video', yt_url=video_url, yt_title=video_title, driver=driver, output_csv_path=session_csv_path)        
                play_pause_button_click(driver)
                
                # Take screenshot of the youtube page
                yt_screenshot_path = os.path.join(base_path, "yt_screenshots", video_id)
                os.makedirs(yt_screenshot_path, exist_ok=True)
                take_page_screenshot(driver, f"{yt_screenshot_path}/{video_id}.png")
                
                # To avoid bot detection
                driver.execute_script("window.scrollBy(0, 300);")
                
                # current window handle i.e., youtube tab
                original_window = driver.current_window_handle
                landing_page_url = click_on_ad_and_capture_requests(video_id, driver, video_url, video_title, original_window, output_csv_path=session_csv_path, landingchoice=landingchoice)

                
                # 4. Sleeping 10 seconds
                # logging.info("Sleeping for 10 seconds and then refreshing the page")
                # time.sleep(10)
                
                # 5. Refreshing the youtube page YOUTUBE VIDEO STOPS, SO YOU HAVE TO CLICK; ALSO THE VIDEO AD BANNER DISAPPEARS AND ONLY ONE SPONSORED AD IS SHOWN
                # driver.requests.clear()
                # driver.refresh()
                
                # 6. Waiting 30 seconds
                # logging.info("Sleeping for 30 seconds and storing requests for phase 'yt_refreshed_after_ad_visit'")
                # time.sleep(15)
                # store_data_in_csv(timestamp=current_time(), video_id=video_id,phase='yt_refreshed_after_ad_visit', yt_url=video_url, yt_title=video_title, driver=driver, landing_page_url=landing_page_url, output_csv_path=session_csv_path)        
                # TODO: Check if this has to be done here of later
                # play_pause_button_click(driver)
                time.sleep(15)
            
                # Updating summary after each video
                write_summary(summary_txt_path, summary_data)    
                        
                # close the browser
                close_browser(driver)
    
    except KeyboardInterrupt:
        logging.warning("Keyboard Interrupt detected. Closing the browser.")    
        
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    
    finally:
        # Store csv to a database
        store_csv_in_db(session_csv_path, session_db_path)
        
        # Write the Summary details to summary.txt
        write_summary(summary_txt_path, summary_data)

        logging.info("Summary written successfully. Exiting program.")
        
        
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run YouTube ad script with specified output file.")
    # parser.add_argument("--outfile", type=str, required=True, help="Output CSV file for storing data")
    parser.add_argument("--browser", choices=["firefox", "chrome", "brave", "egde", "duckduckgo"], default="firefox", help="Browser to use: Firefox/Chrome/Edge/Brave/Duckduckgo (default: Firefox).")
    parser.add_argument("--country", type=str, required=True, help="Country for which trending videos are to be fetched")
    parser.add_argument("--choice", type=int, choices=[1, 2], default=2, help="1: Accept, 2: Reject (default: Reject).")
    parser.add_argument("--landingchoice", type=int, choices=[1, 2], default=2, help="For Ad Landing Page. 1: Accept, 2: Reject (default: Reject).")
    parser.add_argument("--ytMaxResults", type=int, default=20, required=False, help="How many videos you want to watch on youtube. (Max: 200, Default: 20)")
    parser.add_argument("--headless", action="store_true", default=False, help="Run browser in headless mode. (default: headful)")
    parser.add_argument("--stateful", action="store_true", default=False, help="Enable stateful measurements (default: stateless)")
    args = parser.parse_args()
    

    # output_csv = args.outfile
    country = args.country
    choice = args.choice
    landingchoice = args.landingchoice
    browser = args.browser
    ytMaxResults = args.ytMaxResults
    headless = args.headless
    stateful = args.stateful
    
    
    main(browser=browser, country=country, ytMaxResults=ytMaxResults, choice=choice, landingchoice = landingchoice, headless=headless, stateful=stateful)
    
    
    # Close logging
    logging.info("Session completed.")
    logging.info(f"Closing logging session. {datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
    logging.shutdown()
    
    # main() 