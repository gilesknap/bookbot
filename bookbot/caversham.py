from time import sleep
import logging
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

CHROME_DRIVER_PATH = 'chromedriver'
SITE_URL = 'https://indma01.clubwise.com/caversham/index.html'
driver: webdriver = None
driver_wait = None


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


def click(path, check_path, retries: int = 5):
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


def site_login():
    global driver
    global driver_wait
    options = ChromeOptions()
    options.headless = True
    driver = webdriver.Chrome(CHROME_DRIVER_PATH,
                              options=options)
    driver_wait = WebDriverWait(driver, 2)
    driver.implicitly_wait(2)
    driver.get(SITE_URL)

    element = driver.find_element_by_name('oLoginName')
    element.send_keys("tishtashpalmer@gmail.com")
    element = driver.find_element_by_name('oPassword')
    element.send_keys('***')

    click(find_text("Sign In"), find_text("Continue"))
    return_to_classes()


def return_to_classes():
    driver.refresh()
    sleep(.2)
    click(find_text("Continue"), find_text("Make a Booking"))
    click(find_text("Make a Booking"), find_text("Book a Class"))
    click(find_text("Book a Class"), find_text("Select a time to book"))


def get_classes(day):
    path = find_attribute('class', 'Diaryslots ')
    days = driver.find_elements_by_xpath(path)
    classes = days[day].find_elements_by_tag_name('td')
    class_list = []
    for c in classes:
        time_class = c.text.split('\n')
        class_list.append((time_class[0], time_class[1]))
    return class_list


# for individual testing of this module
if __name__ == "__main__":
    app.logger.setLevel(logging.INFO)
    site_login()
    cl = get_classes(1)
    for c in cl:
        app.logger.info(c)
