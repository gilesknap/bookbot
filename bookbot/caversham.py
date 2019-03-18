from time import sleep
import atexit
from collections import namedtuple
from flask import current_app
from selenium import webdriver
from selenium.webdriver import ChromeOptions, ActionChains
from selenium.common.exceptions import (WebDriverException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

CHROME_DRIVER_PATH = 'chromedriver'
SITE_URL = 'https://indma01.clubwise.com/caversham/index.html'
driver: webdriver = None
driver_wait = None

ClassInfo = namedtuple(
    'ClassInfo', ['day', 'times', 'title', 'instructor', 'element', 'index'])


def cleanup():
    global driver, driver_wait
    try:
        driver.close()
    except WebDriverException:
        pass
    driver = None
    driver_wait = None


atexit.register(cleanup)


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
        current_app.logger.error("click fail: %s", path)
        current_app.log_exception(e)
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
                current_app.logger.warning("retrying {}".format(path))
        sleep(.2)
        repeat += 1
    if retries == repeat:
        raise RuntimeError(
            'Click on {} failed to find {}'.format(path, check_path))


def find_text(text: str, tag='*') -> str:
    return '//{1}[text()="{0}"]'.format(text, tag)


def find_text_starts(text: str, tag='*') -> str:
    return '//{1}[starts-with(text(),"{0}")]'.format(text, tag)


def find_attribute(attribute: str, value: str):
    return '//*[@{0}="{1}"]'.format(attribute, value)


def setup_browser(restart=False):
    global driver, driver_wait
    if not driver or restart:
        current_app.logger.debug("setup_browser - making new driver")
        options = ChromeOptions()
        options.headless = True
        driver = webdriver.Chrome(CHROME_DRIVER_PATH,
                                  options=options)
        driver_wait = WebDriverWait(driver, 2)
        driver.implicitly_wait(1)
        driver.get(SITE_URL)


def set_cookies(cookies: str):
    setup_browser()
    try:
        for cookie in cookies:
            driver.add_cookie(cookie)
    except WebDriverException:
        cleanup()


def site_logged_in():
    result = driver.find_elements_by_xpath(
        find_text("Select a time to book")) != []
    current_app.logger.debug("site_logged_in() returning %s", result)
    return result


def site_login(name, password):
    try:
        current_app.logger.debug("site_login(name=%s)", name)
        setup_browser()
        if not site_logged_in():
            if not driver.find_elements_by_xpath(find_text_starts('Welcome')):
                current_app.logger.debug("site_login() authenticating ...")
                element = driver.find_element_by_name('oLoginName')
                element.send_keys(name)
                element = driver.find_element_by_name('oPassword')
                element.send_keys(password)
                click(find_text("Sign In"), find_text("Continue"))

            click(find_text("Continue"), find_text("Make a Booking"))
            click(find_text("Make a Booking"), find_text("Book a Class"))
            click(find_text("Book a Class"), find_text("Select a time to book"))
    except WebDriverException as e:
        # clear out the driver so we can retry
        current_app.log_exception(e)
        cleanup()
        return None
    return driver.get_cookies()


def element_to_class_info(element, day, index, serializable=False):
    class_parts = element.text.split('\n')
    instructor = class_parts[len(class_parts) - 1]
    class_info = ClassInfo(
        day=day,
        times=class_parts[0],
        title=class_parts[1],
        instructor=instructor,
        element=None if serializable else element,
        index=index
    )
    return class_info


def get_classes(day, serializable=True):
    current_app.logger.debug("get_classes(day=%d)", day)
    path = find_attribute('class', 'Diaryslots ')
    days = driver.find_elements_by_xpath(path)
    classes = days[day].find_elements_by_tag_name('td')
    class_list = []
    for idx, class_element in enumerate(classes):
        if serializable:
            # convert to dict for serialization
            class_info = element_to_class_info(
                class_element, day, idx, True)._asdict()
        else:
            class_info = element_to_class_info(class_element, day, idx)
        class_list.append(class_info)
    return class_list


def book_class(day, time, title):
    current_app.logger.debug("book_class(day=%d, time=%s, title=%s)",
                             day, time, title)
    classes: ClassInfo = get_classes(day, True)
    for a_class in classes:
        if a_class.times == time and a_class.title == title:
            current_app.logger.info('found class %s', a_class.element.text)
            a_class.element.click()
            # Todo click on confirm and verify success
            return True
    return False
