# import os
# import time
#
# from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium import webdriver
import selenium


from utility.utilityMethods import *
from config import *
from bannerdetection import *
#
# print(selenium.__version__)
# HEADLESS = False
#
#
# def run_webdriver(page_load_timeout=30, profile=None):
#     global HEADLESS
#     options = Options()
#     driver_path = "./geckodriver.exe"
#     # binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
#     binary_location = r'C:\Program Files\Firefox Nightly\firefox.exe'
#     # if profile is None:
#     #     profile_path = r'C:\Users\arasaii\AppData\Roaming\Mozilla\Firefox\Profiles\xob6l1yb.cookies'
#     #     if not os.path.isdir(profile_path):
#     #         profile_path = r'/mnt/c/Users/arasaii/AppData/Roaming/Mozilla/Firefox/Profiles/xob6l1yb.cookies'
#     #         driver_path = "./geckodriver"
#     #         binary_location = r'/mnt/c/Program Files/Mozilla Firefox/firefox.exe'
#     #         if not os.path.isdir(profile_path): # check when the system is not my own system and therefore does not have this firefox profile.
#     #             profile_path = None
#     #             HEADLESS = True
#     binary_location = r'C:\Program Files\Firefox Nightly\firefox.exe'
#     options.set_preference("browser.privatebrowsing.autostart", True)
#     options.add_argument("--incognito")
#     if HEADLESS:
#         options.add_argument('-headless')
#     options.binary_location = binary_location
#     # options.set_preference('profile', profile_path)
#     # options.add_argument("-profile")
#     # options.add_argument(profile_path)
#     service = Service(driver_path)
#     driver = webdriver.Firefox(options=options, service=service)
#     driver.set_page_load_timeout(page_load_timeout)
#     driver.maximize_window()
#     return driver
#
#
# def run_chrome(page_load_timeout=20):
#     options = webdriver.ChromeOptions()
#     # options.add_argument('--headless')
#     # options.set_binary("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
#     # options.binary_location = "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
#     # options.add_argument("/mnt/c/Users/arasaii/AppData/Local/Google/Chrome/User Data/Default")
#     driver = webdriver.Chrome(executable_path="./chromedriver.exe", options=options)
#     driver.set_page_load_timeout(page_load_timeout)
#     driver.maximize_window()
#     return driver
#
#
# def add_shadow_dom_to_body(driver):
#     js_code = """
# // Returns HTML of given shadow DOM.
# const getShadowDomHtml = (shadowRoot) => {
#     let shadowHTML = '';
#     for (let el of shadowRoot.childNodes) {
#         shadowHTML += el.nodeValue || el.outerHTML;
#     }
#     return shadowHTML;
# };
#
# // Recursively replaces shadow DOMs with their HTML.
# const replaceShadowDomsWithHtml = (rootElement) => {
#     for (let el of rootElement.querySelectorAll('*')) {
#         if (el.shadowRoot) {
#             replaceShadowDomsWithHtml(el.shadowRoot)
#             el.innerHTML += getShadowDomHtml(el.shadowRoot);
#         }
#     }
# };
#
# replaceShadowDomsWithHtml(document.body);
#
# """
#
#     js_code = """
#
#     // Recursively replaces shadow DOMs with their HTML.
#     const replaceShadowDomsWithHtml = (rootElement) => {
#         for (let el of rootElement.querySelectorAll('*')) {
#             if (el.shadowRoot) {
#                 chs = el.shadowRoot.childNodes
#                 for (let el2 of chs) {
#                     el3 = el2.cloneNode(true)
#                     rootElement.appendChild(el3)
#                 }
#             }
#         }
#     };
#
#     replaceShadowDomsWithHtml(document.body);
#
#     """
#     driver.execute_script(js_code)
#
#
# def find_shadowdom_banners(driver, lang='en'):
#     # shadow_dom_to_div(driver)
#     elem = driver.find_element(By.ID, "cmpwrapper")
#     elem_id = get_attribute(driver, elem, "id")
#     elem_id = elem.get_attribute("id")
#     shadow_root = elem.shadow_root
#     elem_in_shadow_dom = shadow_root.find_element(By.ID, "cmpbntyestxt")
#     elem_in_shadow_dom.screenshot("ss.png")
#     elem_in_shadow_dom.click()
#     # banners = find_cookie_banners(driver, translate=False, stale_flag=False)
#     # els = find_els_with_cookie2(driver)
#     # temp = driver.execute_script("return arguments[0].shadowRoot.childNodes", elem)
#     # temp[0].find_element(By.ID, "cmpbox")
#     return elem_in_shadow_dom
#     # return banners
#
#
#
# # d = run_webdriver()
# # # d = run_chrome()
# #
# # # d.get('http://watir.com/examples/shadow_dom.html')
# # d.get('https://www.plantopedia.de')
# #
# # time.sleep(2)
# #
# # shadowdom_pairs = find_shadowdom_banners(d)
# #
# #
# # d.close()
# #
# # elem = driver.find_element(By.ID, "cmpwrapper")
# # elem_id = elem.get_attribute("id")
#
#
# li = [1,2,3,4,5,6]
#
# l = li[0:3]
# l2 = li[3:]
# l3 = li[3:10]
#
# i = 0
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import wait

binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
options = Options()
options.binary_location = binary_location
options.add_argument("-headless")

driver = webdriver.Firefox(options=options)
# driver.get("https://www.plantopedia.de/")
# driver.get("https://www.torgranate.de/")
# driver.get("https://www.fortiguard.com/webfilter")


driver.implicitly_wait(3)


def create_shadow_hosts_div(driver):
    js_code = """
    const replaceShadowDomsWithHtml = () => {
        body_el = document.body;
        els_arr = [];
        var shadow_hosts = document.createElement("div");
        shadow_hosts.id = "shadow_host_els";
        body_el.appendChild(shadow_hosts);
    };

    replaceShadowDomsWithHtml();
    """
    driver.execute_script(js_code)


def add_shadow_dom_to_body(driver):
    # create_shadow_hosts_div(driver)
    host_children = get_shadowhost_children_list(driver)

    js_code = """
    const replaceShadowDomsWithHtml = (rootElement) => {
        host_children = arguments[0];
        console.log(host_children);
        body_el = document.body;
        els_arr = [];
        var shadow_hosts = document.createElement("div");
        shadow_hosts.id = "shadow_host_els";
        body_el.appendChild(shadow_hosts);
        for (let el of host_children) {
            host_node = el[0]
            cloned_host = host_node.cloneNode(false);
            shadow_hosts.appendChild(cloned_host);
            els_arr.push([host_node,cloned_host]);
            children = el[1]
            for (let child of children) {
                cloned_child = child.cloneNode(true);
                cloned_host.appendChild(cloned_child);
            }
        }
        return els_arr;
    };

    return replaceShadowDomsWithHtml();
    """
    return driver.execute_script(js_code, host_children)


def get_shadowhost_children_list(driver):
    all = driver.find_elements(By.XPATH, "/html/body/*")
    all.extend(driver.find_elements(By.XPATH, "/html/body/*/*"))
    host_children = []
    for el in all:
        shadow_root = None
        try:
            shadow_root = el.shadow_root
        except:
            shadow_root = None
        if (shadow_root):
            realchild = []
            children = el.shadow_root.find_elements(By.CSS_SELECTOR, "*")
            first_child = None
            for child in children:
                if child.get_attribute("id"):
                    first_child = child
                    break
            if first_child:
                realchild.append(first_child)
                fc_id = first_child.get_attribute("id")
                if fc_id:
                    siblings = el.shadow_root.find_elements(By.CSS_SELECTOR, "#" + fc_id + " ~ *")
                    realchild.extend(siblings)
                    host_children.append([el, realchild])
    return host_children


# body_el = driver.find_element(By.TAG_NAME, "body")
# children = body_el.find_elements(By.XPATH, "./*")

# root_copy_pairs = add_shadow_dom_to_body(driver)
i = 0
# banners = find_cookie_banners(root_copy_pairs[0][1], translate=False, stale_flag=False, driver=driver)
url = "https://www.cookiebot.com/"



def get_category_with_selenium(url):
    try:
        time.sleep(4)
        wait = WebDriverWait(driver, 5)
        xpath = "//*[@id='webfilter_search_form']/div/div[1]/input"
        input = wait.until(ec.visibility_of_element_located((By.XPATH, xpath)))
        input.send_keys(url)
        xpath = "//*[@id='webfilter_search_form_submit']"
        search = wait.until(ec.visibility_of_element_located((By.XPATH, xpath)))
        search.click()
        xpath = "//*[@id='webfilter-result']/div/div/h4"
        category_el = wait.until(ec.visibility_of_element_located((By.XPATH, xpath)))
        category = category_el.text.split(": ")[1]
        return category
    except:
        return "error"

urls = []

with open('for_cat.txt', 'r') as f:
    for line in f:
        urls.append(line.strip())


cat_dict = {}
for url in urls:
    driver.get("https://www.fortiguard.com/webfilter")
    cat = get_category_with_selenium(url)
    cat_dict[url] = cat
    print(url, cat)


import csv

with open('url_cat_old.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    for key, value in cat_dict.items():
        writer.writerow([key, value])

time.sleep(10)
driver.quit()

