from time import sleep
import logging
import sys
from flask import Flask
from selenium import webdriver
from selenium.webdriver import ChromeOptions, ActionChains
from selenium.common.exceptions import (WebDriverException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

CHROME_DRIVER_PATH = 'chromedriver'
SITE_URL = 'https://indma01.clubwise.com/caversham/index.html'
driver: webdriver = None
actions = None


def click_element(path):
    result = True
    sleep(.2)
    try:
        element = driver.find_element_by_xpath(path)
        if element:
            actions.move_to_element(element).move_by_offset(
                0, 0).click().perform()
    except (WebDriverException, StaleElementReferenceException) as e:
        app.logger.error("click fail %s", e)
        result = False
    return result


def click(path, check_text, retries: int = 5):
    check_path = '//*[text()="{0}"]'.format(check_text)
    repeat = 0
    while repeat < retries:
        if click_element(path):
            wait = WebDriverWait(driver, 2)
            try:
                wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, check_path)))
                break
            except TimeoutException:
                app.logger.warning("retrying {}".format(path))
        repeat += 1
    if retries == repeat:
        raise RuntimeError('Click on {} failed to find {}', path, check_path)


def click_button():
    path = ''


def click_text(text: str, check_text: str, tag: str = '*', retries: int = 5):
    path = '//{1}[text()="{0}"]'.format(text, tag)
    click(path, check_text, retries)


def site_login():
    global driver
    global actions
    options = ChromeOptions()
    # options.headless = True
    driver = webdriver.Chrome(CHROME_DRIVER_PATH,
                          options=options)
    actions = ActionChains(driver)
    driver.implicitly_wait(2)
    driver.get(SITE_URL)

    element = driver.find_element_by_name('oLoginName')
    element.send_keys("tishtashpalmer@gmail.com")
    element = driver.find_element_by_name('oPassword')
    element.send_keys('***')

    click_text("Sign In", "Continue")


def return_to_classes():
    # driver.refresh()
    click_text("Continue", "Make a Booking")
    click_text("Make a Booking", "Book a Class")
    click_text("Book a Class", "Select a time to book")

    # this is the home b
    # data-serveronclick="back-click"


# for individual testing of this module
if __name__ == "__main__":
    # app.logger.addHandler(logging.StreamHandler(sys.stdout))
    app.logger.setLevel(logging.INFO)
    site_login()

    return_to_classes()