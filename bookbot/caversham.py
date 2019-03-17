from time import sleep
import logging
from collections import namedtuple
from enum import IntEnum
from flask import Flask
from selenium import webdriver
from selenium.webdriver import ChromeOptions, ActionChains
from selenium.common.exceptions import (WebDriverException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

app = Flask(__name__)

# todo this module needs to be a class?

CHROME_DRIVER_PATH = 'chromedriver'
SITE_URL = 'https://indma01.clubwise.com/caversham/index.html'
driver: webdriver = None
driver_wait = None
cookie_file = None

ClassInfo = namedtuple(
    'ClassSession', ['time', 'title', 'instructor', 'element', 'index'])

Weekdays = IntEnum('Weekdays', 'sun mon tue wed thu fri sat', start=0)


def click_element(path):
    result = True
    try:
        driver_wait.until(ec.presence_of_element_located((By.XPATH, path)))
        element = driver.find_element_by_xpath(path)
        driver_actions = ActionChains(driver)
        driver_actions.move_to_element(element).move_by_offset(
            0, 0).click().perform()
    except (WebDriverException, StaleElementReferenceException,
            TimeoutError) as e:
        app.logger.error("click fail %s", e)
        result = False
    return result


def click(path, check_path, retries: int = 8):
    repeat = 0
    while repeat < retries:
        if click_element(path):
            try:
                driver_wait.until(
                    ec.presence_of_element_located(
                        (By.XPATH, check_path)))
                break
            except TimeoutException:
                app.logger.warning("retrying {}".format(path))
        sleep(.2)
        repeat += 1
    if retries == repeat:
        raise RuntimeError('Click on {} failed to find {}', path, check_path)


def find_text(text: str, tag='*') -> str:
    return '//{1}[text()="{0}"]'.format(text, tag)


def find_attribute(attribute: str, value: str):
    return '//*[@{0}="{1}"]'.format(attribute, value)


def setup_browser():
    global driver
    global driver_wait
    global cookie_file
    if not driver:
        app.logger.debug("setup_browser - making new driver")
        options = ChromeOptions()
        # options.headless = True
        driver = webdriver.Chrome(CHROME_DRIVER_PATH,
                                  options=options)
        driver_wait = WebDriverWait(driver, 2)
        driver.implicitly_wait(.2)
        driver.get(SITE_URL)


def set_cookies(cookies: str):
    setup_browser()
    for cookie in cookies:
        driver.add_cookie(cookie)


def site_logged_in():
    result = driver.find_elements_by_xpath(
        find_text("Sign In")) == []
    app.logger.debug("site_logged_in() returning %s", result)
    return result


def site_ready():
    result = driver.find_elements_by_xpath(
        find_text("Select a time to book")) != []
    app.logger.debug("site_ready() returning %s", result)
    return result


def site_login(name, password):
    app.logger.debug("site_login(name=%s)", name)
    setup_browser()
    if not site_logged_in():
        if not driver.find_elements_by_xpath(find_text('Continue')):
            app.logger.debug("site_login() authenticating ...")
            element = driver.find_element_by_name('oLoginName')
            element.send_keys(name)
            element = driver.find_element_by_name('oPassword')
            element.send_keys(password)

        click(find_text("Sign In"), find_text("Continue"))
        return_to_classes()
    return driver.get_cookies()


def return_to_classes():
    app.logger.debug("return_to_classes()")
    setup_browser()
    if not site_ready():
        driver.refresh()
        sleep(.2)
        click(find_text("Continue"), find_text("Make a Booking"))
        click(find_text("Make a Booking"), find_text("Book a Class"))
        click(find_text("Book a Class"), find_text("Select a time to book"))


def element_to_class_info(element, index):
    class_parts = element.text.split('\n')
    instructor = class_parts[len(class_parts) - 1]
    class_info = ClassInfo(
        time=class_parts[0],
        title=class_parts[1],
        instructor=instructor,
        element=None,
        index=index
    )
    return class_info


def get_classes(day):
    app.logger.debug("get_classes(day=%d)", day)
    path = find_attribute('class', 'Diaryslots ')
    days = driver.find_elements_by_xpath(path)
    classes = days[day].find_elements_by_tag_name('td')
    class_list = []
    for idx, class_element in enumerate(classes):
        # convert to dict for serialization
        class_info = element_to_class_info(class_element, idx)._asdict()
        class_list.append(class_info)
    return class_list


def book_class(day, time, title):
    app.logger.debug("book_class(day=%d, time=%s, title=%s)",
                     day, time, title)
    classes = get_classes(day)
    for a_class in classes:
        if a_class.time == time and a_class.title == title:
            app.logger.info('found class %s', a_class.element.text)
            a_class.element.click()
            # Todo click on confirm and verify success
            return True
    return False


# for individual testing of this module
if __name__ == "__main__":
    app.logger.setLevel(logging.INFO)
    site_login()
    cl = get_classes(6)
    for c in cl:
        app.logger.info(c)

    t = '9.00am to 9.45am'
    c = 'Spin'
    book_class(6, t, c)
