from time import sleep
import atexit
from collections import namedtuple
from flask import current_app, flash
from selenium import webdriver
from selenium.webdriver import ChromeOptions, ActionChains
from selenium.common.exceptions import (WebDriverException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from typing import List

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


def click(path: str, check_path: str = None, retries: int = 4):
    repeat = 0
    while repeat < retries:
        sleep(.2)
        if click_element(path):
            current_app.logger.debug("clicked %s", path)
            try:
                if check_path:
                    driver_wait.until(
                        ec.presence_of_element_located(
                            (By.XPATH, check_path)))
                    current_app.logger.debug("found %s", path)
                break
            except TimeoutException:
                current_app.logger.warning("retrying {}".format(path))
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
        # options.headless = True
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


def return_to_classes():
    driver.refresh()
    click(find_text("Continue"), find_text("Make a Booking"))
    click(find_text("Make a Booking"), find_text("Book a Class"))
    click(find_text("Book a Class"), find_text("Select a time to book"))


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
        return_to_classes()

    except WebDriverException as e:
        # clear out the driver so we can retry
        current_app.log_exception(e)
        cleanup()
        return None
    return driver.get_cookies()


def element_to_class_info(element, day, index, serializable):
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
            class_info = element_to_class_info(class_element, day, idx, False)
        class_list.append(class_info)
    return class_list


def which_result(paths: List[str], retries=2):
    x_paths = [find_text(path) for path in paths]
    for retry in range(retries):
        for i, path in enumerate(x_paths):
            if driver.find_elements_by_xpath(path):
                return i
    return None


def book_class(day, times, title):
    current_app.logger.debug("book_class(day=%d, time=%s, title=%s)",
                             day, times, title)
    classes: ClassInfo = get_classes(day, False)

    result = None
    found_class = None
    for a_class in classes:
        if a_class.times == times and a_class.title == title:
            current_app.logger.info('found class %s', a_class.element.text)
            found_class = a_class

    if found_class:
        current_app.logger.debug("clicking booking ...")
        found_class.element.click()
        current_app.logger.debug("confirming booking ...")
        sleep(1)
        click(find_text('Confirm'), find_text('Booking Confirmed'))
        current_app.logger.debug("awaiting booking confirmation ...")

        answers = [
            'Booking Confirmed',
            'You are already booked for this class and time.',
            'Sorry we are only able to book this activity up to'
            ' 2 days in advance'
        ]
        result = which_result(answers)

        if result is not None:
            flash(answers[result])
        else:
            flash("booking failed.")

    return_to_classes()
    return result == 0

