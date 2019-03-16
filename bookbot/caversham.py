from time import sleep
import logging
import sys
from flask import Flask
from selenium import webdriver
from selenium.webdriver import ChromeOptions, ActionChains
from selenium.common.exceptions import (WebDriverException,
                                        StaleElementReferenceException)


app = Flask(__name__)

CHROME_DRIVER_PATH = 'chromedriver'
SITE_URL = 'https://indma01.clubwise.com/caversham/index.html'
driver: webdriver = None


def click_element(path):
    result = True
    sleep(.2)
    ac = ActionChains(driver)
    try:
        element = driver.find_element_by_xpath(path)
        if element:
            ac.move_to_element(element).move_by_offset(
                0, 0).click().perform()
    except (WebDriverException, StaleElementReferenceException) as e:
        app.logger.error("click fail %s", e)
        result = False
    return result


def check_text(text, tag='*'):
    path = '//{1}[text()="{0}"]'.format(text, tag)
    return driver.find_elements_by_xpath(path) != []


def click_text(text, tag='*'):
    path = '//{1}[text()="{0}"]'.format(text, tag)
    return click_element(path)


def site_login():
    global driver
    options = ChromeOptions()
    # options.headless = True
    driver = webdriver.Chrome(CHROME_DRIVER_PATH,
                          options=options)

    driver.implicitly_wait(2)
    driver.get(SITE_URL)

    element = driver.find_element_by_name('oLoginName')
    element.send_keys("tishtashpalmer@gmail.com")
    element = driver.find_element_by_name('oPassword')
    element.send_keys('Spider00')

    # Holy mackerel !! (could be refactored)
    step = 1
    for _ in range(10):
        if step == 1:
            click_text("Sign In")
            if check_text("Continue"):
                step += 1
            else:
                continue
        if step == 2:
            click_text("Continue")
            if check_text("Make a Booking"):
                step += 1
            else:
                continue
        if step == 3:
            click_text("Make a Booking")
            if check_text("Book a Class"):
                step += 1
            else:
                continue
        if step == 4:
            click_text("Book a Class")
            if check_text("Select a time to book"):
                break
            else:
                continue
        app.logger.warning('retrying step %d', step)

    title = driver.find_element_by_class_name("DiaryHeading")
    app.logger.info("got to page %s", title.text)


# for individual testing of this module
if __name__ == "__main__":
    app.logger.addHandler(logging.StreamHandler(sys.stdout))
    site_login()

