from selenium import webdriver
from urllib.parse import urlparse
import time
import os
from PIL import Image
import openai
from datetime import datetime

# from bannerclick.bannerdetection import bannerclick_main
from bannerclick.utility.utilityMethods import *
from bannerclick.subscriptiondetection import sub_detection
from bannerclick import cmpdetection as cd

from selenium.webdriver.chrome.service import Service as chromeservice
from selenium.webdriver.chrome.options import Options as chromeoptions


ATTEMPTS = 3
ATTEMPT_STEP = 10
TRANSLATION = False # Translate the page using "Google Translate"; Turned off since Google detect the tool as bot
REJ_IN_SET = True       # enabling try to reject by searching in setting
SIMPLE_DETECTION = True     # enabling direct rejection for reject
NON_EXPLICIT = True      # enabling searching for works inside the HTML also, for example search for 'accept' in the class names of a element
SCREENSHOT = True      # take screenshot
ZOOMING = False
CHROME = False
NOBANNER_SC = True      # store screenshot of websites with no banner in another folder
GPT_REJ = True
PRUNE_GPT = False
GPT_USED = 0
SUB_DETECTION = True
MODIFIED_ADDON = True       # using modified neverconsent addon


directory_folder = "" 
this_banner_lang = None
sc_dir = "/screenshots/"
this_lang = None
rej_flag = False

# TODO: Banner Detection
def find_shadowdom_banners(driver):
    banners = []
    # root_copy_pairs_js = add_shadow_dom_to_body(driver)
    root_copy_pairs = add_shadow_dom_to_body(driver)
    for root_copy_pair in root_copy_pairs:
        shadow_dom_banner = find_cookie_banners(origin_el=root_copy_pair[1])
        if shadow_dom_banner:
            banners.append((root_copy_pair[0], shadow_dom_banner[0]))

    return banners


def find_cookie_banners(driver, origin_el=None, translate=False, stale_flag=False):
    global this_lang
    
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
            els_with_cookie = find_els_with_cookie(origin_el)  # find all the element with cookies related words
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
        frame_pairs = find_CMP_cookies_iframes(driver, detected_lang)  # check all the iframes to detect cookie banners
        for frame_pair in frame_pairs:
            if is_inside_viewport(frame_pair[0]):  # check if the banner is in viewport
                banners.append(frame_pair)
        if not banners and not shadowdom_flag:
            shadowdom_banners = find_shadowdom_banners(driver)
            for dom_pair in shadowdom_banners:
                banners.append(dom_pair)

        return banners
    except StaleElementReferenceException as e:  # handle specific exception
        time.sleep(1)
        if not stale_flag:
            return find_cookie_banners(stale_flag=True)
        raise e
    except Exception as e:  # Catch any other exceptions
        raise e
        # return banners


def detect_banners(driver):  # return banners of the current running url
    global this_url, this_domain, this_status, ttw, status, this_lang
    
    banners = []
    ttw = 0
    status = None
    
    try:
        if ZOOMING:
            zoom_out(3)
        print(f"1. Detecting banners function with url:\t {driver.current_url} \n")
        if not driver.current_url:
            return banners
        
        this_url = driver.current_url
        parsed_url = urlparse(this_url)
        this_domain = parsed_url.netloc
        this_lang = None
        
        banners = find_cookie_banners(driver)

        this_lang = page_lang(driver)
        if ATTEMPTS:
            for att in range(ATTEMPTS):
                if banners:
                    break
                time.sleep(ATTEMPT_STEP)
                if not banners:
                    banners = find_cookie_banners(driver)
                else:
                    return banners
                ttw = (att + 1) * ATTEMPT_STEP
        if not banners and TRANSLATION:
            if "en" not in this_lang and is_in_langlist(this_lang):   # if no banner is found and the language of site is not english then translate the page and check again
                translate_page(driver)
                banners = find_cookie_banners(driver, translate=True)
                this_status = 3
                status = this_status
    except Exception as ex:
        print("failed to continue detecting banner for domain: " + this_domain + " " + ex.__str__())
        this_status = -1
    return banners


# TODO : Screenshot functionality
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

def get_sc_file_name(driver, index=None, choice=None, url=None):
    
    if url is None:
        url = this_url
        # print(f"Function get_sc_file_name 1st if loop: {url}\n")
    
    if index == 1: # Folder
        # print("Inside get sc file name function when index is 1")
        ret = get_current_domain(driver, url)
        return ret

    if index == 2: # Banner
        # print("Inside get sc file name function when index is 2")
        ret = get_current_domain(driver, url) + "_banner" + suffix(choice=choice)
        return ret
    
    if index == 3: # Page SS
        # print("Inside get sc file name function when index is 3")
        ret = get_current_domain(driver, url) + "_page" + suffix(choice=choice) + "_after"
        return ret
    
    if index == 4: # Button
        # print("Inside get sc file name function when index is 4")
        ret = get_current_domain(driver, url) + "_button" + suffix(choice=choice)
        return ret
    
    if index is None:
        # print("get_sc_file_name index is none IF condition")
        ret = str(1234) + " " + get_current_domain(driver, url)
        # print(f" Returning function get_sc_file_name 2st if loop: {ret}\n")
        return ret

    else:
        print("get_sc_file_name index is NOT none ELSE condition")
        ret = str(index+1) + " " + get_current_domain(driver, url)
        # ret = str(index+1) + " " + this_domain
        # print(f" Returning function get_sc_file_name else loop: {ret}\n")
        return ret
    

def create_foldername(driver, choice):
    global directory_folder
    
    ret = get_sc_file_name(driver, index=1) + suffix(choice)
    
    if not os.path.exists(sc_dir):
        os.makedirs(sc_dir)
    
    directory = os.path.join(os.getcwd(), f"screenshots/{ret}")
    if not os.path.exists(directory):
            os.makedirs(directory)
            
    print(f"Creating button filename:\t {ret} \n")
    directory_folder = directory
    

def take_current_page_sc(driver, choice):
    global directory_folder, this_url
    
    if SCREENSHOT:
        try:
            page_filename = os.path.join(f"{directory_folder}", f"{get_sc_file_name(driver, index=3, choice=choice)}.png")
            print(f"Page screenshot saved as:\t {page_filename} \n")
            driver.save_screenshot(page_filename)
        # except Exception as ex:
        #     print("failed to take screenshot for domain: " + this_url + " " + ex.__str__())
        except Exception as ex:
            if "cross-origin" in  ex.__str__():
                try:
                    driver.switch_to.default_content()
                    driver.save_screenshot(
                        directory_folder + get_sc_file_name(index=3, choice=choice) + suffix + ".png")
                    return
                except Exception as ex:
                    pass
            # with open(log_file, 'a+') as f:
            print("failed to take screenshot for url: " + this_url + " " + ex.__str__())
            
def chrome_element_sc(banner, j, index):
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


def take_banner_sc(driver, banner_item, choice, data, j=None):
    """
    Takes a screenshot of a single banner element.
    """
    global directory_folder, this_url
    if banner_item:
        try:
            banner, _ = get_banner_obj(driver, banner_item)  # Updated to use the `driver` context
        except Exception as ex:
            # print(f"Failed to process banner for screenshot at URL {this_url}. Error: {ex}")
            print("failed in switching in banner_sc section for : " + this_url + " " + ex.__str__())
            return
        
        try:
            if j is not None:
                if CHROME:
                    # chrome does not have built-in function for taking screenshot of an element.
                    chrome_element_sc(banner, j, index=2)
                else:
                    banner.screenshot(
                        sc_dir + get_sc_file_name(driver, index=2, choice=choice) + "_banner" + str(j + 1) + ".png")
                
                # banner_filename = os.path.join(f"{directory_folder}", f"{get_sc_file_name(driver, index=2, choice=choice)}.png")
                # # print(f"1. Banner filename:\t {banner_filename} \n")
                # banner.screenshot(banner_filename)
                # print(f"1. Banner screenshot saved as: {banner_filename} \n")
            else:
                banner_filename = os.path.join(f"{directory_folder}", f"{get_sc_file_name(driver, index=2, choice=choice)}.png")
                # print(f"2. Banner filename:\t {banner_filename} \n")
                banner.screenshot(banner_filename)
                print(f"2. Banner screenshot saved as: {banner_filename} \n")
            if type(banner_item) is tuple:
                driver.switch_to.default_content()
        except Exception as ex:
            print(f"Failed to save banner screenshot for URL {this_url}. Error: {ex}")

        

def take_banners_sc(driver, banners, choice, data):
    """
    Takes screenshots of all detected banners.
    """
    global SCREENSHOT, nobanner_sc_dir
    nobanner_sc_dir = sc_dir + "nobanner/"
    if SCREENSHOT:
        if banners:
            for j, banner_item in enumerate(banners):
                try:
                    take_banner_sc(driver, banner_item, choice, data, j)
                except Exception as ex:
                    # print(f"Failed to take banner screenshot for URL {this_url}. Error: {ex}")
                    print("failed to continue in taking banner sc for domain: " + this_url + " " + ex.__str__())
        elif NOBANNER_SC:
            take_current_page_sc(data, nobanner_sc_dir)
        else:
            print("No banners detected for taking screenshots.")




# TODO: BANNER INTERACTION

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

def extract_btns(element, choice, shadow_root=None, non_explicit=False):
    global this_banner_lang, rej_flag, GPT_USED
    
    # PREVIOUS CODE
    # if choice == 1:
    #     btns = find_btns_by_list(element, accept_words, this_banner_lang, non_explicit)
    #     remove_els_with_words(btns, non_acceptable, this_banner_lang)
    # elif choice == 2:
    #     btns = find_btns_by_list(element, reject_words, this_banner_lang, non_explicit)
    # elif choice == 3:
    #     btns = find_btns_by_list(element, setting_words, this_banner_lang, non_explicit)
    # elif choice == 4:
    #     btns = find_btns_by_list(element, login_words, this_banner_lang, non_explicit)

    # if shadow_root is not None:
    #     btns = get_els_from_root(shadow_root, btns)
        
    # # print(f"Extracted buttons: {len(btns)}")
    # # for btn in btns:
    # #     print(f"Button text: {btn.text}, Button attributes: {btn.get_attribute('class')}")
    # return btns
    
    # UPDATED CODE:
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

def click_continue_btn(driver, i):
    wait = WebDriverWait(driver, 3)
    continue_btn = wait.until(ec.visibility_of_element_located(
        (By.XPATH, '//*[@id="container"]/div/div[2]/div/div/div[1]/div[2]/div/div/form/div/button')))
    take_current_page_sc(driver, suffix=suffix(5) + "__before" + str(i + 1))
    continue_btn.click()
    time.sleep(0.5)
    body_el = wait.until(ec.visibility_of_element_located(
        (By.TAG_NAME, 'body')))
    time.sleep(0.5)
    take_current_page_sc(driver, suffix=suffix(5) + "_after" + str(i + 1))
    

def enter_user_pass(driver):
    wait = WebDriverWait(driver, 3)
    email_in = wait.until(ec.visibility_of_element_located(
        (By.XPATH, '//*[@id="email"]')))
    pass_in = driver.find_element(By.XPATH, '//*[@id="password"]')
    email_in.send_keys("aarasaa01@gmail.com")
    pass_in.send_keys("@ASD123123asd")
    login_btn = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div/div/div[1]/div[2]/div/div[1]/form/button')
    login_btn.click()

def click_on_contentpass_continue(driver, i):
    try:
        click_continue_btn(driver, i)
        return True
    except:
        try:
            take_current_page_sc(driver, suffix=suffix(6) + "_after" + str(i + 1))
            enter_user_pass(driver)
            click_continue_btn(driver, i)
            return True
        except Exception as ex:
            print("failed in clicking on contentpass continue for : " + this_url + " in interact with banner. " + ex.__str__())
            return False


def get_banner_obj(driver, banner_item):
    # print("3. Inside get_banner_obj function ...\n")
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
    # print(f"Banner:\t {banner} \n\n Shadow Host:\t {shadow_host}\n\n\n")
    return banner, shadow_host

def create_btn_filename(driver, choice, i):
    global this_index
    return sc_dir + get_sc_file_name(driver, index=4, choice=choice) + suffix(choice) + "_" + str(i + 1)


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
    
    
def interact_with_cmp_banner(el: WebElement):
    global driver, MODIFIED_ADDON
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # never_consent_extension_win_path = r'C:\Users\arasaii\AppData\Roaming\Mozilla\Firefox\Profiles\jf3srcbq.cookiesprofile\extensions\{816c90e6-757f-4453-a84f-362ff989f3e2}.xpi'  # Must be the full path to an XPI file!
    # Must be the full path to an XPI file!
    never_consent_extension_win_path = r'C:\Drives\Education\MPI\Intern\Codes\Workstation\bannerdetection\neverconsent\neverconsent.xpi'
    never_consent_extension_path = current_dir + "/bannerclick/neverconsent/neverconsent.xpi"
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



def interact_with_banner(driver, banner_item, choice, status, i, total_search=False):
    global rej_flag, this_banner_lang, directory_folder, this_index, NON_EXPLICIT, rej_flag, NC_ADDON, SIMPLE_DETECTION, SCREENSHOT, GPT_USED
    
    flag = False
    explicit_coeff = 1
    addon_interaction = False
    gpt_interaction = False
    gpt_setting_interaction = False
    html = ""
    this_banner_lang = "en"
    body_el = driver.find_element(By.TAG_NAME, "body")
    
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
        # with open(log_file, 'a+') as f:
        print("failed in switching frame for : " + this_url + " in interact with banner. " + ex.__str__())
            # MyExceptionLogger(err=ex, file=f)
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
        file_name = create_btn_filename(driver, choice, i)

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
                file_name = create_btn_filename(driver, 8, i)
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
        print("failed in interact with banner for : " +
                  this_url + "  " + ex.__str__())
            # MyExceptionLogger(err=ex, file=f)
        try:
            driver.switch_to.default_content()
        except:
            pass
    # status['gpt_usage'] = GPT_USED
    return flag


def run_banner_detection(driver, choice, data):
    global num_banners, this_start_time
    domain = get_current_domain(driver, this_url)
    banners = detect_banners(driver)
    take_banners_sc(driver, banners, choice, data)
    # num_banners = len(banners)

    return banners

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

def extract_banner_data(banner_item):
    global driver
    banner_data = {}

    try:
        banner, shadow_host = get_banner_obj(banner_item)
    except Exception as ex:
        # with open(log_file, 'a+') as f:
        print("failed in switching frame for : " + this_url + " in exctact banner data. " + ex.__str__())
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
        # with open(log_file, 'a+') as f:
        print("failed in extracting banner for : " + this_url + " " + ex.__str__())
            # MyExceptionLogger(err=ex, file=f)
        return

    return banner_data


def extract_banners_data(banners):
    banners_data = []
    for banner_item in banners:
        banner_data = extract_banner_data(banner_item)
        if banner_data:
            banners_data.append(banner_data)
    return banners_data


def interact_with_banners(driver, banners, banners_data, choice, btn_status, nc_cmp_name, interact_time):  # choices: 1.accept 2.reject
    global rej_flag, this_banner_lang, this_interact_time, GPT_USED
    try:
        btn_flag = False
        for i, banner in enumerate(banners):
            # btn_status: 1. accept 2. reject; btn_set_status: 3. setting 1. add-on; for all if neg then it is non-explicit;
            # btn_status = {"btn_status": 0, "btn_set_status": 0, "gpt_usage": 0}
            btn_status = {"btn_status": 0, "btn_set_status": 0}
            if choice:
                interact_with_banner(banner, banners_data, choice, btn_status, i)
                nc_cmp_name = get_cmp_name_nc(driver)

            if not btn_flag or (abs(btn_status["btn_status"]) != choice and abs(btn_status["btn_status"]) == choice) or abs(btn_status["btn_set_status"]) == 1:
                btn_status = btn_status
                interact_time = time.time() * 1000
                test_time = datetime.now().timestamp() * 1000
                btn_flag = True

            rej_flag = False
            GPT_USED = 0

    except Exception as ex:
        # with open(log_file, 'a+') as f:
        print('error during banner interaction loop: ' + this_domain + "  " + ex.__str__(),)
            # MyExceptionLogger(err=ex, file=f)


# TODO: Logic to start webdriver, visit website, sending code to bannerClick

# TODO: Chrome Driver
# Configure Chrome options
options = chromeoptions()
# options.add_argument("--lang=en")  # Uncomment to set language preference
options.headless = False  # Set to True for headless operation

# Step 1: Initialize WebDriver
# service = chromeservice('../bannerclick/chromedriver')  # Update this to the path of your ChromeDriver
driver = webdriver.Chrome(options=options)

driver.get("https://www.youtube.com/watch?v=7lml_eXqx-M")

# Firefox Driver
# options = Options()
# # options.set_preference("intl.accept_languages", "en")
# options.headless = False  # Set to True for headless operation

# # Step 1: Initialize WebDriver
# driver = webdriver.Firefox(options=options)

# # Step 2: Open YouTube video
# # driver.get("https://www.youtube.com/?hl=en")
# driver.get("https://www.youtube.com/watch?v=7lml_eXqx-M")

# Detect ad and navigate to the landing page
# ad_url = "https://example.com/ad_landing_page"  # Extracted ad URL
# driver.get(ad_url)

time.sleep(10)

# # Step 3: Detect Cookie Banners
# banners = detect_banners(driver)

# Step 3: Call run banner detection which internally calls detect banners and retruns banners objet
banners = run_banner_detection(driver, choice=1, data=None)

create_foldername(driver, choice=1)

# Step 4: Take Screenshots of Banners
# take_banners_sc(driver, banners, choice=1, data=None)

# Step 4:# Extract banners data
banners_data = extract_banners_data(banners)

# Step 5: CMPD Deteection
CMP = cd.run_cmp_detection()

btn_status = None
nc_cmp_name = None
interact_time = None
# Step 6: Interact with banners
interact_with_banners(driver, banners=banners, banners_data=banners_data, choice=1, btn_status=btn_status, nc_cmp_name=nc_cmp_name, interact_time=interact_time)

# # Step 4: Interact with the Cookie Banner
# if banners:
#     lang = page_lang(driver)
#     for i, banner in enumerate(banners):
        
        
#         # Interact with the banner (e.g., Accept)
#         interact_with_banner(driver, banner, choice=1, status={}, i=i)


# TODO: AlexaTop1kGlobal

# def setup_driver():
#     """Set up and return a new Selenium WebDriver instance."""
#     options = Options()
#     options.headless = True 
#     return webdriver.Firefox(options=options)

# def process_domain(domain):
#     """
#     Process a single domain for both accept and reject cookies, 
#     restarting the browser for reject (stateless mode).
#     """
#     global directory_folder

#     print(f"Processing domain: {domain}")
    
#     # ACCEPT COOKIES OPERATION
#     try:
#         # Start WebDriver
#         driver = setup_driver()

#         # Open the website
#         driver.get(f"https://{domain}")
#         time.sleep(5)

#         # Detect banners
#         banners = detect_banners(driver)

#         # Create folder for Accept operation
#         create_foldername(driver, choice=1)
#         print(f"Folder created for Accept: {directory_folder}")

#         # Take banner screenshots for Accept
#         take_banners_sc(driver, banners, choice=1, data=None)

#         # Interact with banners for Accept
#         if banners:
#             for i, banner in enumerate(banners):
#                 interact_with_banner(driver, banner, choice=1, status={}, i=i)

#         # Close the browser (stateless mode)
#         driver.quit()

#     except Exception as ex:
#         print(f"Error processing Accept cookies for domain {domain}: {ex}")

#     # REJECT COOKIES OPERATION (Stateless mode)
#     try:
#         # Start a new WebDriver instance
#         driver = setup_driver()

#         # Reopen the website
#         driver.get(f"https://{domain}")
#         time.sleep(5)

#         # Detect banners again
#         banners = detect_banners(driver)

#         # Create folder for Reject operation
#         create_foldername(driver, choice=2)
#         print(f"Folder created for Reject: {directory_folder}")

#         # Take banner screenshots for Reject
#         take_banners_sc(driver, banners, choice=2, data=None)

#         # Interact with banners for Reject
#         if banners:
#             for i, banner in enumerate(banners):
#                 interact_with_banner(driver, banner, choice=2, status={}, i=i)

#         # Close the browser
#         driver.quit()

#     except Exception as ex:
#         print(f"Error processing Reject cookies for domain {domain}: {ex}")


# def main():
#     # Read domains from AlexaTop1kGloballist.txt
#     file_path = os.path.join("bannerclick\input-files", "AlexaTop1kGlobal.txt")
#     with open(file_path, "r") as file:
#         domains = [line.strip() for line in file if line.strip()]

#     print(f"Total domains to process: {len(domains)}")

#     for domain in domains:
#         process_domain(domain)
        
# if __name__ == "__main__":
#     main()


# TODO: For Youtube Integration:

# def bannerclick_main(driver, choice):
#     print("Detecting and interacting with the Cookie Banner\n")
    
#     # Detect Banners
#     banners = detect_banners(driver)
    
#     # Create folders inside screenshots/ for banner ss
#     create_foldername(driver, choice=choice)
    
#     # Interacting with the banner
    
#     if banners:
#         lang = page_lang(driver)
#         for i, banner in enumerate(banners):
#             # Interact with the banner (e.g., Accept)
#             interact_with_banner(driver, banner, choice=choice, status={}, i=i)
