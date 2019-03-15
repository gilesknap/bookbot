from requests import session
from time import sleep
from bs4 import BeautifulSoup
from flask import Flask
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.common.exceptions import WebDriverException
from urllib.parse import urlparse, parse_qs

CHROME_DRIVER_PATH = 'chromedriver'

app = Flask(__name__)

site_url = 'https://indma01.clubwise.com/caversham/index.html'
session_requests = session()

driver: webdriver = None


def click_element(path):
    retries = 5
    for i in range(retries, 0, -1):
        try:
            element = driver.find_element_by_xpath(path)
            element.click()
        except WebDriverException as e:
            app.logger.error("click fail %s", e)
            if i == 1:
                raise
            else:
                sleep(.2)


def click_table_row(text):
    path = '//tr[text()="{0}"]'.format(text)
    click_element(path)


def click_button(text):
    path = '//div[@data-dfobj="{0}"]'.format(text)
    click_element(path)


def click_div(text):
    path = '//div[text()="{0}"]'.format(text)
    click_element(path)


def site_login():
    global driver
    options = ChromeOptions()
    # options.headless = True
    driver = webdriver.Chrome(CHROME_DRIVER_PATH,
                              chrome_options=options)
    driver.implicitly_wait(8)
    driver.get(site_url)

    element = driver.find_element_by_name('oLoginName')
    element.send_keys("tishtashpalmer@gmail.com")
    element = driver.find_element_by_name('oPassword')
    element.send_keys('***')
    sleep(.2)

    click_button('oLoginDialog.oMainPanel.oLoginButtonContainer.oLoginButtonCard.oLoginButton')
    #click_button('oWelcomeScreen.oWebMainPanel.oContinue')
    # click_button('Continue')
    click_table_row('Make a Booking')
    click_table_row('Book a Class')

    title = driver.find_element_by_class_name("DiaryHeading")
    app.logger.info("got to page %s", title.text)
