import argparse
import random
import time
import openai
import base64


from PIL import Image


import traceback
import sys
from selenium.webdriver.support import expected_conditions as EC

# TODO: Abhishek added code:
# from seleniumwire import webdriver
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions


try:
    from .utility.utilityMethods import *
    from .config import *
    from . import cmpdetection as cd
    from .subscriptiondetection import sub_detection
except ImportError as E:
    print("run the module as a script")
    from utility.utilityMethods import *
    from config import *
    import cmpdetection as cd
    from subscriptiondetection import sub_detection

# TODO: Abhishek code
# try:
#     from utility.utilityMethods import *
#     from config import *
#     import cmpdetection as cd
#     from subscriptiondetection import sub_detection
# except ImportError as E:
#     print("Ensure that the script is run within its package context, or adjust imports.")
#     raise


rej_flag = False
GPT_USED = 0

def MyExceptionLogger(err, file):
    # return
    traceback_details = traceback.format_exc()
    print(traceback_details, file=file)
    exc_type, exc_value, exc_traceback = sys.exc_info()
    print(f"Exception type: {exc_type}, Value: {exc_value}", file=file)
    traceback.print_tb(exc_traceback, file=file)


def is_semantically_correct_gpt(el, semantic):
    try:
        personal_key = "sk-1cbiPXcwJOMcCkA4rMDgxheQe59qB05hX0RJOykPnOT3BlbkFJBt4LXc_odM5I3qXxsooLHmOMl8qlCqck7_O43kGn0A"
        mpi_key = "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"
        openai.api_key = personal_key
        button_element = el.get_attribute("outerHTML")
        prompt = """
            You are a web scraping assistant. Given the following HTML content, if you think the following HTML element could be semantically related to a {semantic} button (regarding web cookies) return "yes" otherwise return "no".
            html element:
            {button_element}
            
            Return "yes" or "no".
            """.format(semantic=semantic, button_element=button_element)

        model = "gpt-4o-mini"
        # Call GPT-4 to get the XPath
        response = openai.ChatCompletion.create(
            model=model,  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are an expert in analyzing HTML for web scraping purposes."},
                {"role": "user", "content": prompt},
            ]
        )

        res = response['choices'][0]['message']['content'].strip()
        return "yes" in res
    except:
        return None


def remove_els_with_gpt(els: list[WebElement], choice):
    to_remove = []
    for el in els:
        if choice == 1:
            res = is_semantically_correct_gpt(el, semantic="positive")
            if not res and res is not None:
                to_remove.append(el)
    entries_to_remove(to_remove, els)



def find_reject_in_setting_html_gpt2(html_content):
    try:
        personal_key = "sk-1cbiPXcwJOMcCkA4rMDgxheQe59qB05hX0RJOykPnOT3BlbkFJBt4LXc_odM5I3qXxsooLHmOMl8qlCqck7_O43kGn0A"
        mpi_key = "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"
        openai.api_key = personal_key
        screenshot_binary = driver.get_screenshot_as_png()
        screenshot_base64 = base64.b64encode(screenshot_binary).decode('utf-8')

        prompt = f"""
        You are a web scraping assistant. The image is the screenshot of Webpage after clicking on the setting button of cookie banner. Now identify the text of the button which "reject all" or "confirm" the current selected preferences (i.e. any thing except accepting non essential cookies).
        Image (base64-encoded): {screenshot_base64}
        For response, if you found the button, return the plain text of it (without triple backticks) otherwise return "not found" and nothing else.
        """

        model = "gpt-4o-mini"

        # Call GPT-4 to analyze the screenshot
        response = openai.ChatCompletion.create(
            model=model,  # Assuming you have access to a version with image capabilities
            messages=[
                {"role": "system", "content": "You are an assistant that processes base64-encoded images."},
                {"role": "user", "content": prompt},
            ]
        )

        # Extract the text of the button from the response
        button_text = response['choices'][0]['message']['content'].strip()

        return button_text

    except Exception as ex:
        return None


# Step 1: Initialize GPT-4 to find the reject button
def find_reject_button_html_gpt(html_content):
    try:
        personal_key = "sk-1cbiPXcwJOMcCkA4rMDgxheQe59qB05hX0RJOykPnOT3BlbkFJBt4LXc_odM5I3qXxsooLHmOMl8qlCqck7_O43kGn0A"
        mpi_key = "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"
        openai.api_key = personal_key

        prompt = """
        You are a web scraping assistant. Given the following HTML content, identify the XPath of the "Reject" or "Decline" button typically found in cookie consent banners.
        HTML:
        {html_content}
        Return "JUST" XPath for the "Reject" button with no explanation. Put the XPath between ";".
        """.format(html_content=html_content)

        model = "gpt-4o-mini"
        # Call GPT-4 to get the XPath
        response = openai.ChatCompletion.create(
            model=model,  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are an expert in analyzing HTML for web scraping purposes."},
                {"role": "user", "content": prompt},
            ]
        )
        xpath = response['choices'][0]['message']['content'].strip(";")
        return xpath
    except:
        return None


def get_btns_gpt(el, choice):
    buttons = []
    html = to_html(el)
    if len(html) > 10000:
        html = extract_essential_html(html)
    html = extract_essential_html(html)
    xpath = find_btns_xpath_gpt(html, choice)
    if "not found" not in xpath:
        try:
            buttons = WebDriverWait(el, 2).until(
                EC.presence_of_all_elements_located((By.XPATH, xpath))
            )
            pruning_btns(buttons)
        except Exception as ex:
            pass
    return buttons

def find_btns_xpath_gpt(html_content, choice):
    global  rej_flag
    personal_key = "sk-1cbiPXcwJOMcCkA4rMDgxheQe59qB05hX0RJOykPnOT3BlbkFJBt4LXc_odM5I3qXxsooLHmOMl8qlCqck7_O43kGn0A"
    mpi_key = "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"
    openai.api_key = personal_key

    if choice == 2:
        if rej_flag:
            prompt = """
            I have clicked on the settings button of a cookie banner. Below is the current HTML DOM of the cookie banner. Your task is to search the DOM and identify the possible XPath of elements that related to buttons which either "confirm" the current selected preferences or "reject all" non-essential cookies, leading to the closing of the banner. Avoid selecting buttons related to "accepting all" cookies.
            HTML:
            {html_content}

            If such elements exist in the above DOM, return their XPath (separated by | if multiple), otherwise, return "not found" and nothing else.
            
            (if you found the xpaths of the elements:
            your response is possibly correct if its text contains something similar to: "Save and Exit", "Submit preferences", "Reject All", "Accept selected" or any thing semantically related
            your response is possibly wrong if its text contains something similar to: "Accept All", "Manage Settings", "More Information", "Return" or any thing semantically related)
            """.format(html_content=html_content)
        else:
            prompt = """
            You are a web scraping assistant, please ANSWER following query. Below is the HTML DOM of a cookie banner. Identify the XPath of buttons that either "refuse" or "reject all" non-essential cookies, leading to the closing of the banner. Avoid selecting buttons related to "accepting all" cookies or "settings" of cookie banners.
    
            HTML:
            {html_content}

            If you find such buttons in the DOM, return their XPath (separated by | if multiple). If not, return "not found" and nothing else.
            
            (if you found the xpaths of the elements:
            your response is possibly correct if its text contains something similar to: "reject", "disagree", "do not agree", "continue without accept", "only essential" or any thing semantically related
            your response is possibly wrong if its text contains something similar to:  "Accept All", "Manage Settings", "More Information", "dismiss", "Adjust", "ok" or cross sign (X) resulting in implicitly accepting the banner or any thing semantically related)
            """.format(html_content=html_content)
    elif choice == 3:
        prompt = """
        You are a web scraping assistant, please ANSWER following query. Below is the HTML DOM of a cookie banner. Identify the XPath of buttons that is related to "settings" or "options" of the cookies, leading to the opening cookie banner setting. Avoid selecting buttons related to "accepting" or "rejecting" cookies.
        (the text in the xpath "ANSWER" might be similar as: "Manage Settings", "More Information", "More Preferences" or any thing semantically related
        example of wrong ANSWER are: buttons text contains "Accept All", "Reject all", "Deny", "Privacy Policy" or any thing semantically related)
        HTML:
        {html_content}

        If you find such buttons in the DOM, return their XPath (separated by | if multiple). If not, return "not found" and nothing else.
        """.format(html_content=html_content)
    try:
        model = "gpt-4o-mini"
        # Call GPT-4 to get the XPath
        response = openai.ChatCompletion.create(
            model=model,  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are an expert in analyzing HTML for web scraping purposes."},
                {"role": "user", "content": prompt},
            ]
        )
    except:
        return "not found"
    try:
        res = response['choices'][0]['message']['content']
        res = res.replace("```", "").replace("xpath", "").replace("\n", "")
        return res.strip('"')
        # if not ("xpath" in res or "'''" in res):
        #     return res.strip('"')
        pattern = r"/.*?\](?!.*\])"
        matches = re.findall(pattern, res)
        xpath = ""
        first_flag = False
        # Check if any matches were found and print them
        if matches:
            for match in matches:
                if first_flag:
                    xpath += " | "
                xpath += match
                first_flag = True
            return xpath
        else:
            return "not found"
    except:
        return "not found"


def is_sub_gpt(html_content):
    try:
        personal_key = "sk-1cbiPXcwJOMcCkA4rMDgxheQe59qB05hX0RJOykPnOT3BlbkFJBt4LXc_odM5I3qXxsooLHmOMl8qlCqck7_O43kGn0A"
        mpi_key = "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"
        openai.api_key = personal_key

        prompt = """
        You are a web scraping assistant. Given the following HTML content, identify if the following HTML dom is related to a cookie paywall banner.
        HTML:
        {html_content}
           Just return "yes" if it is cookie paywall and "no" otherwise.
        """.format(html_content=html_content)

        model = "gpt-4o-mini"
        # Call GPT-4 to get the XPath
        response = openai.ChatCompletion.create(
            model=model,  # or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are an expert in analyzing HTML for web scraping purposes."},
                {"role": "user", "content": prompt},
            ]
        )

        res = response['choices'][0]['message']['content'].strip()
        return "yes" in res
    except Exception as ex:
        return None




def reset():
    global counter, driver, visit_db, domains, this_domain, this_url, banner_db, html_db, this_lang, this_banner_lang, this_run_url
    counter = 0
    driver = None
    visit_db = None
    banner_db = None
    html_db = None
    domains = []
    this_domain = None
    this_url = None
    this_run_url = None
    this_lang = None
    this_banner_lang = None


def run_webdriver_old(page_load_timeout=TIME_OUT, profile=None):
    global driver, HEADLESS
    options = Options()
    driver_path = "./geckodriver.exe"
    if profile is None:
        # path = '/mnt/c/Users/arasaii/AppData/Roaming/Mozilla/Firefox/Profiles/xob6l1yb.cookies'
        path = r'C:\Users\arasaii\AppData\Roaming\Mozilla\Firefox\Profiles\xob6l1yb.cookies'
        if not os.path.isdir(path):
            # path = r'/mnt/c/Users/arasaii/AppData/Roaming/Mozilla/Firefox/Profiles/xob6l1yb.cookies'
            driver_path = "./geckodriver"
            # options.binary_location = r'/mnt/c/Program Files/Mozilla Firefox/firefox.exe'
            # check when the system is not my own system and therefore does not have this firefox profile.
            if not os.path.isdir(path):
                path = None
                HEADLESS = True
            # path = None
        # profile = webdriver.FirefoxProfile(
        #     path)
        options.add_argument(path)
    # desired, prof = avoid_bot_detection(profile, MOBILE_AGENT)
    # options.set_preference("browser.privatebrowsing.autostart", True)
    # options.add_argument("--incognito")
    options.headless = HEADLESS
    options.add_argument("-profile")

    # prefs = { "translate_whitelists": {"fr": "en", "it": "en"}, "translate": {"enabled": "true"}}
    # options.add_experimental_option("prefs", prefs)
    d = DesiredCapabilities.FIREFOX
    d['loggingPrefs'] = {'browser': 'ALL'}
    try:
        driver = webdriver.Firefox(options=options)
    except WebDriverException as Ex:
        print("Error while run webdriver: ", Ex.__str__())

    driver.set_page_load_timeout(page_load_timeout)
    if MOBILE_AGENT:
        driver.set_window_size(340, 695)
    else:
        driver.maximize_window()
    # Must be the full path to an XPI file!
    never_consent_extension_win_path = r'..\neverconsent\N1.xpi'
    # id = driver.install_addon(never_consent_extension_win_path, temporary=True)
    # translate_extension_path = r'C:\Users\TwilighT\AppData\Roaming\Mozilla\Firefox\Profiles\24jg4ggm.default-release\extensions\jid1-93WyvpgvxzGATw@jetpack.xpi'  # Must be the full path to an XPI file!
    # driver.install_addon(translate_extension_path, temporary=True)

    return driver


def set_zoom(driver, zoom_level):
    # Ensure the zoom level is a decimal like 0.8 for 80%, 1.0 for 100%, etc.
    driver.execute_script(f"document.body.style.zoom='{zoom_level}';")


def run_webdriver(page_load_timeout=30, profile=None):
    global HEADLESS
    
    geckodriver_path = '../browser_drivers/geckodriver.exe'
    
    options = FirefoxOptions()
    if HEADLESS:
        options.headless = True
    
    service = FirefoxService(geckodriver_path)
    driver = webdriver.Firefox(options=options, service=service)        
    driver.set_page_load_timeout(page_load_timeout)
    driver.maximize_window()
    
    return driver


def run_chrome(page_load_timeout=TIME_OUT):
    global driver
    options = webdriver.ChromeOptions()
    
    if HEADLESS:
        options.add_argument('--headless')
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(page_load_timeout)
    driver.maximize_window()
    return driver


def set_webdriver(web_driver=None):
    global driver
    try:
        if web_driver is None:
            web_driver = run_webdriver()
        if driver != webdriver:
            driver = web_driver
            if MOBILE_AGENT:
                driver.set_window_size(340, 695)
            else:
                driver.maximize_window()

        # TODO: Added by ME for Cookie SRC Saver
        # COOKIESRC_SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'CookieSrcSaver/dist')
        # driver.install_addon(path=COOKIESRC_SAVE_PATH, temporary=True)

        if UBLOCK_ADDON:
            install_ublock(driver)
    except Exception as ex:
        with open(log_file, 'a+') as f:
            print(f"failed in bc.set_webdriver: f{ex.__str__()}", file=f)
            MyExceptionLogger(err=ex, file=f)
    return driver


def install_ublock(web_driver):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ublock_xpi_path = current_dir + "/ublock/uBlock0@raymondhill.net.xpi"
    web_driver.install_addon(ublock_xpi_path)


def get_data_dir_name():
    global data_dir
    return data_dir


def set_data_dir_name(dir_name):
    global data_dir
    data_dir = dir_name

def run_bing(page_load_timeout=TIME_OUT):
    global driver
    
    edge_path = '../browser_drivers/msedgedriver.exe'
        
    options = webdriver.EdgeOptions()
    
    if HEADLESS:
        options.add_argument('--headless')
    
    # service = webdriver.EdgeService(edge_path)
    
    driver = webdriver.Edge(options=options)
    
    driver.set_page_load_timeout(page_load_timeout)
    driver.maximize_window()
    
    return driver

def get_browser_name(driver):
    # Check the type of WebDriver and return the browser name in lowercase
    if isinstance(driver, webdriver.Firefox):
        return 'firefox'
    elif isinstance(driver, webdriver.Chrome):
        return 'chrome'
    elif isinstance(driver, webdriver.Edge):
        return 'edge'
    elif isinstance(driver, webdriver.Safari):
        return 'safari'
    else:
        return 'unknown'
    

# TODO: domain added in the function signature
def init(season_dir=None, headless=HEADLESS, input_file=None, num_browsers=NUM_BROWSERS, num_repetitions=1, domains_file=None, web_driver=None, domain=None, v_db=None,
         b_db=None, h_db=None):  # initialize bannerdetection by setting url file and webdriver instance
    global domains, driver, file, input_files_dir, UBLOCK_ADDON, browser, custom_dir, time_dir, \
            time_or_custom, data_dir, sc_dir, nobanner_sc_dir, sc_file_name, log_file, banners_log_file
    
    driver = web_driver
    browser = get_browser_name(driver)
    
    # url_dir = "." + input_files_dir
    # print(f"URL dir from config file is being set: {url_dir}\n")
        
    
    time_or_custom = datetime.now().date().__str__() + \
            datetime.now().strftime(" %H-%M-%S").__str__()

    if season_dir is not None:
        # data_dir = season_dir + time_or_custom
        data_dir = season_dir + time_or_custom + "-" + domain
        sc_dir = data_dir + "/screenshots/"
        nobanner_sc_dir = sc_dir + "nobanner/"
        sc_file_name = ""
        log_file = data_dir + '/logs.txt'
        banners_log_file = data_dir + '/banners_log.txt'
    
    create_data_dirs()
    
    if not domain:
        if os.path.isfile(file):
            domains = file_to_list(file)
    set_database(v_db, b_db, h_db)

    cd.init(driver, get_database()[0])
    
    TRANSLATION = True
    
    if input_file:
        file = input_file
    init_str = f"""Crawl initialized for: {file} in {datetime.now().strftime("%H-%M-%S").__str__()}
    START_POINT:STEP_SIZE: {START_POINT}:{STEP_SIZE}
    headless: {headless}
    input_file: {input_file}
    num_browsers: {num_browsers}
    num_repetitions: {num_repetitions}
    timeout: {TIME_OUT}
    translation: {TRANSLATION}
    delay_time: {SLEEP_TIME}
    ATTEMPTS:ATTEMPT_STEP: {ATTEMPTS}:{ATTEMPT_STEP}
    Chrome: {CHROME}
    openwpm.xpi: {XPI}
    Watchdog: {WATCHDOG}
    interaction choice: {"ALL"}
    non explicit: {NON_EXPLICIT}
    SIMPLE_DETECTION: {SIMPLE_DETECTION}
    search for reject btn in setting: {REJ_IN_SET}
    NC_ADDON: {NC_ADDON}
    mobile agent: {MOBILE_AGENT}
    CMP detection: {CMPDETECTION}
    banner interaction: {BANNERINTERACTION} \n\n""" + "__"*30 + "\n"
    print(init_str)

    try:
        with open(log_file, 'a+') as f:
            print(init_str, file=f)
    except:
        pass
    


def get_domains():
    global domains
    return domains


def create_data_dirs():
    if not os.path.exists(season_dir):
        os.makedirs(season_dir)
    print(f"Data directory: {data_dir} in create_data_dirs function")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    if not os.path.exists(sc_dir):
        os.makedirs(sc_dir)
    if not os.path.exists(nobanner_sc_dir):
        os.makedirs(nobanner_sc_dir)


def file_to_list(path):
    file = set_urls_file(path)
    global domains
    while True:
        domain = file.readline().strip('\n')
        if not domain:
            break
        if domain == "#":
            break
            # continue
        if domain == "$":
            break
        domains.append(domain)
    return domains


def set_database(v_db, b_db, h_db):
    global visit_db, banner_db, html_db
    if v_db is None:
        visit_db = pd.DataFrame({
            'visit_id': pd.Series([], dtype='int'),
            'domain': pd.Series([], dtype='str'),
            'url': pd.Series([], dtype='str'),
            'run_url': pd.Series([], dtype='str'),
            'status': pd.Series([], dtype='int'),
            'btn_status': pd.Series([], dtype='int'),
            'lang': pd.Series([], dtype='str'),
            'banners': pd.Series([], dtype='int'),
            'ttw': pd.Series([], dtype='int'),
            '__cmp': pd.Series([], dtype='bool'),
            '__tcfapi': pd.Series([], dtype='bool'),
            '__tcfapiLocator': pd.Series([], dtype='bool'),
            'cmp_id': pd.Series([], dtype='int'),
            'cmp_name': pd.Series([], dtype='str'),
            'pv': pd.Series([], dtype='bool'),
            'dnsmpi': pd.Series([], dtype='str'),
            'body_html': pd.Series([], dtype='str'),
        })
        banner_db = pd.DataFrame({
            'banner_id': pd.Series([], dtype='int'),
            'visit_id': pd.Series([], dtype='int'),
            'domain': pd.Series([], dtype='str'),
            'lang': pd.Series([], dtype='str'),
            'iFrame': pd.Series([], dtype='bool'),
            'shadow_dom': pd.Series([], dtype='bool'),
            'captured_area': pd.Series([], dtype='float'),
            'x': pd.Series([], dtype='float'),
            'y': pd.Series([], dtype='float'),
            'w': pd.Series([], dtype='float'),
            'h': pd.Series([], dtype='float'),
        })
        html_db = pd.DataFrame({
            'banner_id': pd.Series([], dtype='int'),
            'visit_id': pd.Series([], dtype='int'),
            'domain': pd.Series([], dtype='str'),
            'html': pd.Series([], dtype='str'),
        })
    else:
        visit_db = v_db
        banner_db = b_db
        html_db = h_db
    return visit_db, banner_db, html_db


def get_database():
    global visit_db, banner_db, html_db
    return visit_db, banner_db, html_db


def open_domain_page(domain, sleep=TEST_MODE_SLEEP):
    global driver, this_url, this_domain, this_status
    mode = 1
    while True:
        url = make_url(domain, mode)
        if url == '':
            break
        try:
            driver.get(url)
            this_status = 0
            time.sleep(sleep)
            break
        except TimeoutException as ex:
            with open(log_file, 'a+') as f:
                print("failed to get (TimeOut): " +
                      url + " " + ex.__str__(), file=f)
                MyExceptionLogger(err=ex, file=f)
            this_status = 1
        except WebDriverException as ex:
            with open(log_file, 'a+') as f:
                print("failed to get (unreachable): " +
                      url + " " + ex.__str__(), file=f)
                MyExceptionLogger(err=ex, file=f)
            this_status = 2
        finally:
            mode += 1
    this_domain = domain
    this_url = url
    return url


def find_cookie_banners(origin_el=None, translate=False, stale_flag=False):
    # TODO: WITHOUT EXCEPTION HANDLING
    global driver, this_lang
    try:
        banners = []
        banners_map = dict()

        if origin_el is None:
            wait = WebDriverWait(driver, 2)
            body_el = wait.until(
                ec.visibility_of_element_located((By.TAG_NAME, "body")))
            # set_zoom(driver, 0.7)
            time.sleep(0.2)
            WebDriverWait(driver, 1).until(lambda d: d.execute_script(
                'return document.readyState') == 'complete')
            # body_el = driver.find_element(By.TAG_NAME, "body")
            origin_el = body_el
            shadowdom_flag = False
        else:
            shadowdom_flag = True
        if translate:
            detected_lang = this_lang
            els_with_cookie = find_els_with_cookie(origin_el, detected_lang)
        else:
            detected_lang = "en"
            # find all the element with cookies related words
            els_with_cookie = find_els_with_cookie(origin_el)
        if els_with_cookie:
            banners_map = find_fixed_ancestors(els_with_cookie)
            if not banners_map:
                banners_map = find_by_zindex(els_with_cookie)
            if not banners_map:
                banners_map[origin_el] = find_deepest_el(els_with_cookie)
            for item in banners_map.items():
                optimal_el = find_optimal(driver, item)
                if is_inside_viewport(optimal_el) and has_enough_word(optimal_el) and not is_signin_banner(optimal_el):
                    banners.append(optimal_el)
        # check all the iframes to detect cookie banners
        frame_pairs = find_CMP_cookies_iframes(driver, detected_lang)
        for frame_pair in frame_pairs:
            # check if the banner is in viewport
            if is_inside_viewport(frame_pair[0]):
                banners.append(frame_pair)
        if not banners and not shadowdom_flag:
            shadowdom_banners = find_shadowdom_banners(driver)
            for dom_pair in shadowdom_banners:
                banners.append(dom_pair)
                # if is_inside_viewport(dom_pair[0]):  # check if the banner is in viewport

        return banners
    except StaleElementReferenceException as e:  # handle specific exception
        time.sleep(1)
        if not stale_flag:
            return find_cookie_banners(stale_flag=True)
        raise e
    except Exception as e:  # Catch any other exceptions
        raise e
        # return banners


def find_shadowdom_banners(driver):
    banners = []
    # root_copy_pairs_js = add_shadow_dom_to_body(driver)
    root_copy_pairs = add_shadow_dom_to_body(driver)
    for root_copy_pair in root_copy_pairs:
        shadow_dom_banner = find_cookie_banners(origin_el=root_copy_pair[1])
        if shadow_dom_banner:
            banners.append((root_copy_pair[0], shadow_dom_banner[0]))

    return banners


def detect_banners(data):  # return banners of the current running url
    global driver, this_url, this_domain, this_status, visit_db, this_lang, this_index
    banners = []
    inc_counter()
    try:
        if ZOOMING:
            zoom_out(3)
        if not data.url:
            return banners
        this_index = data.index
        this_url = data.url
        this_domain = data.domain
        this_lang = None
        time.sleep(2.5)
        banners = find_cookie_banners()

        # with open(banners_log_file, 'a+') as f:
        #     init_str = this_domain + " banner detection finished within: " + str(
        #         completion_time.microseconds)
        #     print(init_str, file=f)

        this_lang = page_lang(driver)
        data.lang = this_lang
        if ATTEMPTS:
            for att in range(ATTEMPTS):
                if banners:
                    break
                time.sleep(ATTEMPT_STEP)
                if not banners:
                    banners = find_cookie_banners()
                else:
                    return banners
                data.ttw = (att + 1) * ATTEMPT_STEP
        if not banners and TRANSLATION:
            # if no banner is found and the language of site is not english then translate the page and check again
            if "en" not in this_lang and is_in_langlist(this_lang):
                translate_page(driver)
                banners = find_cookie_banners(translate=True)
                this_status = 3
                data.status = this_status
    except Exception as ex:
        with open(log_file, 'a+') as f:
            print("failed to continue detecting banner for domain: " +
                  data.domain + " " + ex.__str__(), file=f)
            # MyExceptionLogger(err=ex, file=f)
        this_status = -1
        data.status = this_status
    return banners


# first opens the domain then detects banners of that domain
def open_domain_plus_detect_banner(domain):
    open_domain_page(domain)
    return detect_banners()


def interact_with_cmp_banner(el: WebElement):
    global driver, MODIFIED_ADDON
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # never_consent_extension_win_path = r'C:\Users\arasaii\AppData\Roaming\Mozilla\Firefox\Profiles\jf3srcbq.cookiesprofile\extensions\{816c90e6-757f-4453-a84f-362ff989f3e2}.xpi'  # Must be the full path to an XPI file!
    # Must be the full path to an XPI file!
    never_consent_extension_win_path = r'C:\Drives\Education\MPI\Intern\Codes\Workstation\bannerdetection\neverconsent\neverconsent.xpi'
    never_consent_extension_path = current_dir + "/neverconsent/neverconsent.xpi"
    if MODIFIED_ADDON:
        run_addon_js(driver)
    else:
        try:
            id = driver.install_addon(
                never_consent_extension_path, temporary=True)
        except:
            id = driver.install_addon(
                never_consent_extension_win_path, temporary=True)
    time.sleep(2)
    if not MODIFIED_ADDON:
        driver.uninstall_addon(id)
    try:
        if el.is_displayed():
            return False
        else:
            return True
    except Exception as E:
        return True


def interact_with_gpt(el, file_name, choice=2):
    global GPT_USED
    try:
        flag = False
        # Wait for the button to be present and visible
        btns = get_btns_gpt(el, choice)
        if btns:
            flag = click_func(el, btns, file_name, SCREENSHOT)
            if GPT_USED:
                GPT_USED = 6
            else:
                GPT_USED = -6
        return flag

    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def interact_with_banner(banner_item, banners_data, choice, status, i, total_search=False):
    global driver, this_index, NON_EXPLICIT, rej_flag, NC_ADDON, SIMPLE_DETECTION, SCREENSHOT, GPT_USED
    flag = False
    addon_interaction = False
    gpt_interaction = False
    gpt_setting_interaction = False
    explicit_coeff = 1
    html = ""
    this_banner_lang = "en"

    try:
        this_banner_lang = banners_data[i].get('lang', "en")
        html = banners_data[i].get('html_short', "")
        if banners_data[i].get('is_sub', False) and choice == 2:
            return False
    except:
        pass

    try:
        WebDriverWait(driver, 1).until(lambda d: d.execute_script(
            'return document.readyState') == 'complete')
    except:
        try:
            driver.switch_to.default_content()
            WebDriverWait(driver, 0.5).until(lambda d: d.execute_script(
                'return document.readyState') == 'complete')
        except:
            return False

    try:
        banner, shadow_host = get_banner_obj(banner_item)
    except Exception as ex:
        with open(log_file, 'a+') as f:
            print("failed in switching frame for : " + this_url + " in interact with banner. " + ex.__str__(),
                  file=f)
            MyExceptionLogger(err=ex, file=f)
        driver.switch_to.default_content()
        return
    try:
        body_el = driver.find_element(By.TAG_NAME, "body")
        if total_search:       # search the whole body DOM for the words, this is because sometimes for example after clicking on setting the banner DOM disappears or the page redirect to another page.
            el = body_el
        else:
            el = banner
    except:
        return False

    try:
        file_name = create_btn_filename(choice, i)

        ex_btns = extract_btns(el, choice, shadow_root=shadow_host)
        if choice == 2 and rej_flag and len(ex_btns) > 3:
            keep_els_with_words(
                ex_btns, ['all'], this_banner_lang, check_attr=False)
        ex_btns_temp = list(ex_btns)
        if SIMPLE_DETECTION or choice != 2 or rej_flag:
            flag = click_func(el, ex_btns, file_name, SCREENSHOT)
            if not flag and NON_EXPLICIT:
                nex_btns = extract_btns(
                    el, choice, shadow_root=shadow_host, non_explicit=True)
                entries_to_remove(ex_btns_temp, nex_btns)
                flag = click_func(el, nex_btns, file_name, SCREENSHOT)
                explicit_coeff = -1
            if rej_flag and (not flag or is_availble(driver, el)):  # user gpt iteraction if the button is not cliked or is still visible or enable
                file_name = create_btn_filename(8, i)
                gpt_setting_interaction = interact_with_gpt(el, file_name, choice)
                if gpt_setting_interaction:
                    flag = False

        if choice == 2 and not flag and not rej_flag:
            if NC_ADDON:
                addon_interaction = interact_with_cmp_banner(el)

            if REJ_IN_SET and not addon_interaction:
                set_flag = interact_with_banner(el, banners_data, 3, status, i)
                if set_flag:
                    time.sleep(1)
                    rej_flag = True
                    is_total_search = False
                    # this total_search causes click on wrong reject btns like: statista.com, politico.com, sap.com
                    if not is_availble(driver, el):
                        is_total_search = True
                    flag = interact_with_banner(
                        el, banners_data, choice, status, i, is_total_search)
                    if not flag:
                        is_total_search = True
                        flag = interact_with_banner(
                            el, banners_data, choice, status, i, is_total_search)
                    if not flag:
                        try:
                            driver.switch_to.default_content()
                            iframes = get_iframes(driver)
                            iframes.reverse()
                            for iframe in iframes:
                                try:
                                    driver.switch_to.default_content()
                                    driver.switch_to.frame(iframe)
                                    flag = interact_with_banner(
                                        el, banners_data, choice, status, i, is_total_search)
                                    if flag:
                                        break
                                except:
                                    pass
                        except:
                            pass


        if type(banner_item) is tuple:
            driver.switch_to.default_content()
        if flag:
            time.sleep(0.1)
            if choice == 1 or choice == 2:
                driver.switch_to.default_content()
                status['btn_status'] = choice * explicit_coeff
                take_current_page_sc(suffix=suffix(
                    choice) + "_after" + str(i + 1))
            elif choice == 3:
                status['btn_set_status'] = choice * explicit_coeff
                take_current_page_sc(suffix=suffix(
                    choice) + "_after" + str(i + 1))
            elif choice == 4:
                status['btn_status'] = choice * explicit_coeff
                click_on_contentpass_continue(driver, i)
            if shadow_host:
                del_cloned_shadow_hosts(driver)
        if addon_interaction:
            status['btn_set_status'] = 1
            take_current_page_sc(suffix="_Xnc_after" + str(i + 1))
        if gpt_interaction:
            status['btn_status'] = choice
            status['btn_set_status'] = 2
            take_current_page_sc(suffix="_Xgpt_after" + str(i + 1))
        if gpt_setting_interaction:
            driver.switch_to.default_content()
            status['btn_set_status'] = -1
            take_current_page_sc(suffix="_XXgptrejINset_after" + str(i + 1))

    except Exception as ex:
        with open(log_file, 'a+') as f:
            print("failed in interact with banner for : " +
                  this_url + "  " + ex.__str__(), file=f)
            MyExceptionLogger(err=ex, file=f)
        try:
            driver.switch_to.default_content()
        except:
            pass
    # status['gpt_usage'] = GPT_USED
    return flag


def extract_btns(element, choice, shadow_root=None, non_explicit=False):
    global this_banner_lang, rej_flag, GPT_USED
    if choice == 1:
        btns = find_btns_by_list(
            element, accept_words, this_banner_lang, non_explicit)
        remove_els_with_words(btns, non_acceptable, this_banner_lang)
    elif choice == 2:
        if rej_flag:
            rej_words = reject_setting_words
            if non_explicit:
                return []
        else:
            rej_words = reject_words
        btns = find_btns_by_list(
            element, rej_words, this_banner_lang, non_explicit)
        if btns and non_explicit:
            remove_els_with_words(btns, accept_words, this_banner_lang, False)
        if not btns and not non_explicit:
            btns = find_btns_by_list(
                element, accept_words, this_banner_lang, non_explicit)
            keep_els_with_words(btns, non_acceptable, this_banner_lang)
            if not btns and GPT_REJ and not rej_flag:
                btns = get_btns_gpt(element, choice)
                if btns:
                    GPT_USED = 2
    elif choice == 3:
        words = list(setting_words)
        if not non_explicit:
            words.extend(more_setting_words)
        btns = find_btns_by_list(
            element, words, this_banner_lang, non_explicit)
        if not btns and not non_explicit:
            btns = get_btns_gpt(element, choice)
            if btns:
                GPT_USED = 3
    elif choice == 4:
        btns = find_btns_by_list(element, login_words,
                                 this_banner_lang, non_explicit)
    if PRUNE_GPT:
        remove_els_with_gpt(btns, choice)
    if shadow_root is not None:
        btns = get_els_from_root(shadow_root, btns)
    return btns


def suffix(choice):
    global rej_flag
    if choice == 1:
        return "_XX" + 'acc'
    elif choice == 2:
        return "_XX" + 'rej' + ('INset' if rej_flag else '')
    elif choice == 3:
        return "_X" + 'set'
    elif choice == 4:
        return "_X" + 'log'
    elif choice == 5:
        return "_XX" + 'conbtn'
    elif choice == 6:
        return "_X" + 'log'
    elif choice == 7:
        return "_XX" + 'login'
    elif choice == 8:
        return "_XX" + 'gptrej' + ('INset' if rej_flag else '')


def create_btn_filename(choice, i):
    global this_index
    return sc_dir + get_sc_file_name(this_index) + suffix(choice) + "_" + str(i + 1)


def get_banner_obj(banner_item):
    global driver
    shadow_host = None
    if type(banner_item) is tuple:
        frame = banner_item[0]
        banner = banner_item[1]
        try:
            driver.switch_to.frame(frame)
            if type(banner) is tuple:
                frame = banner[0]
                banner = banner[1]
                driver.switch_to.frame(frame)
        except:  # for shadow root
            banner = banner_item[1]
            shadow_host = banner_item[0]
    else:
        banner = banner_item
    return banner, shadow_host


def get_sc_file_name(index=None, url=None):
    global driver, visit_db, this_url
    if url is None:
        url = this_url
    if index is None:
        return str(visit_db.shape[0]) + " " + get_current_domain(driver, url)
    else:
        return str(index+1) + " " + get_current_domain(driver, url)


def take_current_page_sc(data=None, directory=None, suffix=""):
    global driver, SCREENSHOT
    if SCREENSHOT:
        if data is None:
            index = this_index
            url = this_url
        else:
            index = data.index
            url = data.url
        if directory is None:
            directory = sc_dir
        try:
            driver.save_screenshot(
                directory + get_sc_file_name(index, url) + suffix + ".png")
        except Exception as ex:
            if "cross-origin" in  ex.__str__():
                try:
                    driver.switch_to.default_content()
                    driver.save_screenshot(
                        directory + get_sc_file_name(index, url) + suffix + ".png")
                    return
                except Exception as ex:
                    pass
            with open(log_file, 'a+') as f:
                print("failed to take screenshot for url: " +
                      url + " " + ex.__str__(), file=f)


def inc_counter():
    global counter
    counter += 1


def take_banner_sc(banner_item, data, j=None):
    if banner_item:
        try:
            banner, _ = get_banner_obj(banner_item)
        except Exception as ex:
            with open(log_file, 'a+') as f:
                print("failed in switching in banner_sc section for : " +
                      this_url + " " + ex.__str__(), file=f)
                MyExceptionLogger(err=ex, file=f)
            return
        try:
            if j is not None:
                if CHROME:
                    # chrome does not have built-in function for taking screenshot of an element.
                    chrome_element_sc(banner, data.index, j)
                else:
                    banner.screenshot(
                        sc_dir + get_sc_file_name(this_index) + "_banner" + str(j + 1) + ".png")
            else:
                banner.screenshot(
                    sc_dir + get_sc_file_name(this_index) + "_banner" + ".png")
            if type(banner_item) is tuple:
                driver.switch_to.default_content()
        except Exception as ex:
            with open(log_file, 'a+') as f:
                print("failed in switching in banner_sc section for : " +
                      this_url + " " + ex.__str__(), file=f)
                # MyExceptionLogger(err=ex, file=f)
        return banner


def chrome_element_sc(banner, index, j):
    location = banner.location
    size = banner.size
    ax = location['x']
    ay = location['y']
    width = location['x'] + size['width']
    height = location['y'] + size['height']
    crop_image = Image.open(sc_dir + get_sc_file_name(index) + ".png")
    crop_image = crop_image.crop((int(ax), int(ay), int(width), int(height)))
    crop_image.save(sc_dir + get_sc_file_name(index) +
                    "_banner" + str(j + 1) + "_ch.png")


def is_sub(text, html):
    if SUB_DETECTION:
        tuple = sub_detection(text, html)
        if tuple:
            is_sub = is_sub_gpt(text)
            if is_sub or is_sub is None:
                return True
        else:
            return False
    return False

import html.parser
class EssentialHTMLParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.essential_html = ""
        self.in_footer = False
        self.in_img = False
        self.in_script = False
        self.in_hidden = False

    def handle_starttag(self, tag, attrs):
        if tag in ['footer', 'img', 'script', 'hidden']:
            self.in_footer = tag == 'footer'
            self.in_img = tag == 'img'
            self.in_script = tag == 'script'
            self.in_hidden = tag == 'hidden'
            return

        if not self.in_footer and not self.in_img and not self.in_script and not self.in_hidden:
            attributes = []
            for attr, value in attrs:
                if attr in ['id', 'name']:
                    attributes.append(f'{attr}="{value}"')
                elif attr == 'class' and ('btn' in value or 'button' in value):
                    attributes.append(f'{attr}="{value}"')

            self.essential_html += f"<{tag} {' '.join(attributes)}>".replace(" ", " ")

    def handle_endtag(self, tag):
        if tag in ['footer', 'img', 'script', 'hidden']:
            self.in_footer = False
            self.in_img = False
            self.in_script = False
            self.in_hidden = False
            return

        if not self.in_footer and not self.in_img and not self.in_script and not self.in_hidden:
            self.essential_html += f"</{tag}>"

    def handle_data(self, data):
        if not self.in_footer and not self.in_img and not self.in_script and not self.in_hidden:
            self.essential_html += data


def is_missed(html):
    soup = bs(html, "html.parser")
    plain_text = soup.get_text()
    character_count = len(plain_text)
    return character_count < 100;


def extract_essential_html(html_dom):
    try:
        parser = EssentialHTMLParser()
        parser.feed(html_dom)
        html = parser.essential_html
        if is_missed(html):
            return html_dom
        return html
    except Exception as ex:
        return html_dom


def simplify_html(dom_html):
    soup = bs(dom_html)
    cmp_main = soup.find(id='cmp-main')
    def simplify_tag(tag):
        # Create a new tag with the same name
        simplified_tag = soup.new_tag(tag.name)

        # Copy the 'id' and 'class' attributes if they exist
        if tag.has_attr('id'):
            simplified_tag['id'] = tag['id']
            if tag['id'] == "cmp-main":
                i = 0
        if tag.has_attr('class'):
            simplified_tag['class'] = tag['class']

        # Preserve text content
        if tag.string:
            simplified_tag.string = tag.string
        children = tag.children
        if children:
            for child in tag.children:
                child_text = child.get_text(strip=True)
                child_name = child.name
                if "cookies" in child_text:
                    print(child_text)
                if "p" == child_name:
                    print(child_text)
                if child_name:  # Check if the child is a tag
                    simplified_tag.append(simplify_tag(child))
                else:
                    simplified_tag.append(child)
        else:
            simplified_tag.text = tag.text

        return simplified_tag

    simplified_soup = simplify_tag(soup)
    return simplified_soup.prettify()


def get_html_short(html):
    html_short = simplify_html(html)
    return html_short


def extract_banner_data(banner_item):
    global driver
    banner_data = {}

    try:
        banner, shadow_host = get_banner_obj(banner_item)
    except Exception as ex:
        with open(log_file, 'a+') as f:
            print("failed in switching frame for : " + this_url +
                  " in exctact banner data. " + ex.__str__(), file=f)
            # MyExceptionLogger(err=ex, file=f)
        driver.switch_to.default_content()
        return

    try:
        banner_data["captured_area"] = calc_area(
            list(banner.size.values())) / calc_area(list(get_win_inner_size(driver)))
        banner_data["x"] = banner.location["x"]
        banner_data["y"] = banner.location["y"]
        banner_data["w"] = banner.size["width"]
        banner_data["h"] = banner.size["height"]
        html = to_html(banner)
        banner_data['html'] = html
        # html_short = get_html_short(html)
        html_short = extract_essential_html(html)
        banner_data['html_short'] = html_short
        banner_data['is_sub'] = is_sub(banner.text, html)
        banner_data['lang'] = detect_lang(banner.text)
        if type(banner_item) is tuple:
            if shadow_host is not None:
                banner_data["shadow_dom"] = True
            else:
                banner_data["iFrame"] = True
                driver.switch_to.default_content()
        else:
            banner_data["iFrame"] = False
            banner_data["shadow_dom"] = False
    except Exception as ex:
        with open(log_file, 'a+') as f:
            print("failed in extracting banner for : " +
                  this_url + " " + ex.__str__(), file=f)
            # MyExceptionLogger(err=ex, file=f)
        return

    return banner_data


def get_data_dicts(banner_data, visit_id):
    global this_domain, visit_db, banner_db, html_db, this_index
    try:
        # visit_id = this_index
        banner_id = random.getrandbits(53)
        b_row_dict = {'banner_id': banner_id,
                      'visit_id': visit_id, 'domain': this_domain}
        h_row_dict = {'banner_id': banner_id,
                      'visit_id': visit_id, 'domain': this_domain}
        b_row_dict.update(banner_data)
        h_row_dict['html'] = banner_data["html"]
        h_row_dict['html_short'] = banner_data["html_short"]
        del b_row_dict['html']
        del b_row_dict['html_short']

        try:
            banner_db.loc[banner_db.shape[0],
                          b_row_dict.keys()] = b_row_dict.values()
            html_db.loc[html_db.shape[0], h_row_dict.keys()] = h_row_dict.values()
        except:
            pass
    except Exception as ex:
        with open(log_file, 'a+') as f:
            print("failed to continue extracting banner data for domain: " +
                  this_url + " " + ex.__str__(), file=f)
            MyExceptionLogger(err=ex, file=f)
    finally:
        return b_row_dict, h_row_dict


def take_banners_sc(banners, data):
    global driver, SCREENSHOT
    if SCREENSHOT:
        if banners:
            for j, banner_item in enumerate(banners):
                try:
                    take_banner_sc(banner_item, data, j)
                except Exception as ex:
                    with open(log_file, 'a+') as f:
                        print("failed to continue in taking banner sc for domain: " + this_url + " " + ex.__str__(),
                              file=f)
                        MyExceptionLogger(err=ex, file=f)
        elif NOBANNER_SC:
            take_current_page_sc(data, nobanner_sc_dir)


def extract_banners_data(banners):
    banners_data = []
    for banner_item in banners:
        banner_data = extract_banner_data(banner_item)
        if banner_data:
            banners_data.append(banner_data)
    return banners_data


def set_data_in_db_error(data):
    global this_domain
    try:
        set_data_in_db(data)
    except Exception as ex:
        with open(log_file, 'a+') as f:
            print("failed to continue setting data in DB for domain: " +
                  data.domain + " " + ex.__str__(), file=f)
            MyExceptionLogger(err=ex, file=f)


def set_data_in_db(data):
    global driver, this_url, this_domain, this_status, this_lang, visit_db, this_run_url
    if data.openwpm:
        visit_id = data.visit_id
        site_rank = data.index
        this_status = data.status
        this_url = data.url
        this_domain = get_current_domain(driver, this_url)
        this_lang = data.lang
    else:
        visit_id = visit_db.shape[0] + 1
        site_rank = visit_id
    try:
        run_url = driver.current_url
    except Exception as ex:
        run_url = None
    v_dict = {'visit_id': visit_id, 'site_rank': site_rank, 'domain': this_domain, 'url': this_url, 'run_url': run_url, 'status': this_status, 'lang': this_lang, 'banners': len(data.banners_data)
              , 'interact_mode': data.choice, 'interact_time': data.interact_time, 'goal': data.goal,  'ttw': data.start_time.timestamp()*1000, '__tcfapi': False, '__tcfapiLocator': False, 'pv': False, 'nc_cmp_name': data.nc_cmp_name}
    v_dict.update(data.btn_status)
    try:
        body_html = to_html(driver.find_element(By.TAG_NAME, "body"))
    except:
        body_html = None
    if DNSMPI_DETECTION:
        v_dict['dnsmpi'] = dnsmpi_detection(body_html)
    else:
        v_dict['dnsmpi'] = None
    if SAVE_BODY:
        v_dict['body_html'] = body_html
    else:
        v_dict['body_html'] = None
    v_dict['with_sub'] = False

    b_dict = {}
    h_dict = {}
    # not equal with: visit_db = visit_db.append(row_dict, ignore_index=True), using second one, new dataframe with new address will be created.

    try:
        for banner_data in data.banners_data:
            b_dict, h_dict = get_data_dicts(banner_data, visit_id)
            if b_dict['is_sub']:
                v_dict['with_sub'] = True
            if data.openwpm:
                data.save_record_in_sql("banners", b_dict)
                if SAVE_HTML:
                    data.save_record_in_sql("htmls", h_dict)

        CMP_dict = cd.extract_CMP_data(data.CMP)
        v_dict.update(CMP_dict)
    except:
        pass
    if data.openwpm:
        data.save_record_in_sql("visits", v_dict)
    else:
        visit_db.loc[visit_db.shape[0], v_dict.keys()] = v_dict.values()

    return v_dict, b_dict, h_dict


def halt_for_sleep(start_time, time_to_wait):
    if start_time:
        while True:
            cur_time = datetime.now()
            completion_time = cur_time - start_time
            insec = completion_time.total_seconds()
            if insec < time_to_wait:
                time.sleep(0.5)
            else:
                return cur_time



def enter_user_pass(driver):
    wait = WebDriverWait(driver, 3)
    email_in = wait.until(ec.visibility_of_element_located(
        (By.XPATH, '//*[@id="email"]')))
    pass_in = driver.find_element(By.XPATH, '//*[@id="password"]')
    email_in.send_keys("aarasaa01@gmail.com")
    pass_in.send_keys("@ASD123123asd")
    login_btn = driver.find_element(
        By.XPATH, '/html/body/div[1]/div/div[2]/div/div/div[1]/div[2]/div/div[1]/form/button')
    login_btn.click()


def click_on_contentpass_continue(driver, i):
    try:
        click_continue_btn(driver, i)
        return True
    except:
        try:
            take_current_page_sc(suffix=suffix(6) + "_after" + str(i + 1))
            enter_user_pass(driver)
            click_continue_btn(driver, i)
            return True
        except Exception as ex:
            with open(log_file, 'a+') as f:
                print("failed in clicking on contentpass continue for : " + this_url + " in interact with banner. " + ex.__str__(),
                      file=f)
                MyExceptionLogger(err=ex, file=f)
            return False


def click_continue_btn(driver, i):
    wait = WebDriverWait(driver, 3)
    continue_btn = wait.until(ec.visibility_of_element_located(
        (By.XPATH, '//*[@id="container"]/div/div[2]/div/div/div[1]/div[2]/div/div/form/div/button')))
    take_current_page_sc(suffix=suffix(5) + "__before" + str(i + 1))
    continue_btn.click()
    time.sleep(0.5)
    body_el = wait.until(ec.visibility_of_element_located(
        (By.TAG_NAME, 'body')))
    time.sleep(0.5)
    take_current_page_sc(suffix=suffix(5) + "_after" + str(i + 1))


def interact_with_banners(data, choice):  # choices: 1.accept 2.reject
    global rej_flag, this_banner_lang, this_interact_time, GPT_USED
    try:
        btn_flag = False
        for i, banner in enumerate(data.banners):
            # btn_status: 1. accept 2. reject; btn_set_status: 3. setting 1. add-on; for all if neg then it is non-explicit;
            # btn_status = {"btn_status": 0, "btn_set_status": 0, "gpt_usage": 0}
            btn_status = {"btn_status": 0, "btn_set_status": 0}
            if choice:
                interact_with_banner(banner, data.banners_data, choice, btn_status, i)
                data.nc_cmp_name = get_cmp_name_nc(driver)

            if not btn_flag or (abs(data.btn_status["btn_status"]) != choice and abs(btn_status["btn_status"]) == choice) or abs(btn_status["btn_set_status"]) == 1:
                data.btn_status = btn_status
                data.interact_time = time.time() * 1000
                test_time = datetime.now().timestamp() * 1000
                btn_flag = True

            rej_flag = False
            GPT_USED = 0

    except Exception as ex:
        with open(log_file, 'a+') as f:
            print('error during banner interaction loop: ' + data.domain + "  " + ex.__str__(),
                  file=f)
            MyExceptionLogger(err=ex, file=f)


def take_page_sc(data):
    take_current_page_sc(data)


def run_banner_detection(data):
    global num_banners, driver, this_start_time
    data.domain = get_current_domain(driver, data.url)
    banners = detect_banners(data)
    take_banners_sc(banners, data)
    # num_banners = len(banners)

    return banners


def save_database():
    global visit_db, banner_db, html_db
    if visit_db is not None:
        visit_db.to_csv(data_dir + '/visits.csv', index=False)
        banner_db.to_csv(data_dir + '/banners.csv', index=False)
        html_db.to_csv(data_dir + '/htmls.csv', index=False)

        init_str = "(saving) visits_db id is: {},\n db is: {}".format(
            id(visit_db), visit_db)
        with open(data_dir + "/sites.txt", 'a+') as f:
            print(init_str, file=f)


def set_mode(file_name, var, run_mode=0):
    global browser, season_dir, custom_dir, time_dir, time_or_custom, data_dir, sc_dir, nobanner_sc_dir, sc_file_name, log_file, banners_log_file
        
    if run_mode:
        DETECT_MODE = run_mode  # fixed = 1, z-index = 2, custom set = 0
        if run_mode == 1:
            custom_dir = "fixed"
        elif run_mode == 2:
            custom_dir = "zindex"
        time_or_custom = custom_dir
    else:
        time_or_custom = datetime.now().date().__str__() + \
            datetime.now().strftime(" %H-%M-%S").__str__() + "--" + file_name + "-" + var

    # data_dir = season_dir + time_or_custom
    data_dir = season_dir + time_or_custom + "-" + browser
    print(f"Data directory: {data_dir} in set_mode function")
    sc_dir = data_dir + "/screenshots/"
    nobanner_sc_dir = sc_dir + "nobanner/"
    sc_file_name = ""
    log_file = data_dir + '/logs.txt'
    banners_log_file = data_dir + '/banners_log.txt'


def run_all(dmns=None):   # this function is used for run the banner detection module only (Not through OpenWPM)
    global driver, counter
    if dmns is None:
        dmns = get_domains()

    for domain in dmns:
        # banners = open_domain_plus_detect_banner(domain)
        url = open_domain_page(domain)
        run_all_for_domain(domain, url)
    else:
        time.sleep(2)
        close_driver()


def run_all_for_domain(DMN, URL, CHOICE):
    global counter, SLEEP_TIME
    try:
        class Data:
            url = URL
            domain = DMN
            choice = CHOICE
            banners = []
            banners_data = []
            CMP = {}
            index = None
            sleep = SLEEP_TIME
            ttw = 0   # time to wait (to show the banner)
            status = None
            btn_status = None
            openwpm = False
            btn_status = {"btn_status": 0, "btn_set_status": 0, "gpt_usage": 0}
            nc_cmp_name = None
            interact_time = None
            goal = "something"
            start_time = datetime.now()
            finish_time = 0


        Data.index = visit_db.shape[0]
        Data.visit_id = visit_db.shape[0]
        if BANNERCLICK:
            banners = run_banner_detection(Data)
            take_page_sc(Data)
            Data.banners = banners
            Data.banners_data = extract_banners_data(banners)
        if CMPDETECTION:
            Data.CMP = cd.run_cmp_detection()
        if BANNERINTERACTION:
            interact_with_banners(Data, CHOICE)
        if SLEEP_AFTER_INTERACTION:
            Data.start_time = datetime.now()
        set_data_in_db(Data)
        halt_for_sleep(Data.start_time, 10)

    except MemoryError as ex:
        visit_db.loc[visit_db.index[-1], 'status'] = -1
        with open(log_file, 'a+') as f:
            print('Memory Error happened for: ' + DMN + "  " + ex.__str__(),
                  file=f)
            MyExceptionLogger(err=ex, file=f)
    except InvalidSessionIdException as ex:
        visit_db.loc[visit_db.index[-1], 'status'] = -1
        with open(log_file, 'a+') as f:
            print('InvalidSessionIdException happened for: ' + DMN + "  " + ex.__str__(),
                  file=f)
            MyExceptionLogger(err=ex, file=f)
        raise
    except Exception as ex:
        visit_db.loc[visit_db.index[-1], 'status'] = -1
        with open(log_file, 'a+') as f:
            print('Exception happened for: ' + DMN + "  " + ex.__str__(),
                  file=f)
            MyExceptionLogger(err=ex, file=f)
    # finally:
    #     if not (counter % 100):
    #         print(str(counter) + ' websites have been crawled successfully! The last one was: ', domain)


def close_driver():
    global driver
    save_database()
    driver.quit()
    reset()


def run_all_with_browser(files, variable):
    """Run the main logic for each file with the selected browser."""
    global driver
    try:
        for f in files:
            set_mode(f, variable, 0)
            init(f, input_file=f)
            cd.init(driver, get_database()[0])
            run_all()
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        raise

if __name__ == '__main__':
    # this function is used for run the banner detection module only (Not through OpenWPM)
    global browser
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", nargs='+',
                        help="list of file paths contains URLs that will be run sequentially \
                        (attached to the name of data folder)")
    parser.add_argument(
        "-v", "--variable", help="variable of run (attached to the name of data folder)")
    parser.add_argument("--browser", choices=["firefox", "chrome", "bing", "duckduckgo", "qwant", "startpage", "brave"], default="firefox",
                        help="Browser to use (default: firefox).")
    parser.add_argument("--choice", type=int, choices=[1,2], default=2,
                        help="Choice of action for banners: accept or reject.")
    parser.add_argument('--headless', action='store_true',
                        help="start on headless mode")
    
    args = parser.parse_args()
    file = args.file
    variable = args.variable or "test"
    browser = args.browser
    headless = args.headless
    choice = args.choice
    
    HEADLESS = headless
    CHOICE = choice
    
    
    if browser == 'chrome':
        CHROME = True
    

    # if not files:
    #     files = [urls_file, "AlexaTop1kGlobal.txt", "addon_urls.txt"]
    #     files = [urls_file]
    #     variable = 'test'
    # try:
    #     for f in files:
    #         set_mode(f, variable, 0)
    #         init(f)
    #         cd.init(driver, get_database()[0])
    #         run_all()
    # except:
    #     if driver:
    #         close_driver()
    #     raise
    
    # TODO: Abhishek code
    run_all_with_browser(file, variable)

