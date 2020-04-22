import sys, os, re, requests, time, argparse
import itertools
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait
from twilio.rest import Client
from random import randint
import datetime

from creds import * 


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
chromedriver = ROOT_DIR + "/chromedriver"

## amazon credentials
#amazon_username = "aospi533@gmail.com"
#amazon_password = "Bl@zee88"
#
## twilio configuration
#to_mobilenumber = "+13475750726"
#from_mobilenumber = "+12563049369"
#account_sid = "AC2483bd55f92901a1f0de81fb063f2b1d"
#auth_token = "1b8f81c157c1a268c2ed22663d9071d7"
#client = Client(account_sid, auth_token)

client = Client(account_sid, auth_token)


def launch_driver():
    browser_options = webdriver.ChromeOptions()
    browser_options.add_argument("--incognito")
    driver = webdriver.Chrome(chromedriver, options=browser_options)
    return driver

def terminate(driver):
    driver.quit()


def find_available(args):
    try:
        print('Launching Incognito Chrome Browser ...')
        driver = launch_driver()

        print('Logging into Amazon ...')
        driver.get('https://www.amazon.com/gp/sign-in.html')
        your_email = driver.find_element_by_css_selector('#ap_email')
        your_email.send_keys(amazon_username)
        driver.find_element_by_css_selector('#continue').click()
        time.sleep(1.5)
        your_password = driver.find_element_by_css_selector('#ap_password')
        your_password.send_keys(amazon_password)
        driver.find_element_by_css_selector('#signInSubmit').click()
        time.sleep(1.5)

        print('Redirecting to AmazonFresh ...')
        driver.get('https://www.amazon.com/gp/cart/view.html?ref_=nav_cart')
        time.sleep(1.5)
        print('Continuing to date availability page ...')
        driver.find_element_by_name('proceedToALMCheckout-QW1hem9uIEZyZXNo').click()
        time.sleep(1.5)
        print('Checking for dates ...')
        driver.find_element_by_name('proceedToCheckout').click()


        dates_available = True
        spaces_free = False
        free_spaces = ""
        while not spaces_free:
            while dates_available:
                time.sleep(1.5)
                spots = driver.find_elements_by_css_selector('.ss-carousel-item')
                for spot in spots:
                    if spot.value_of_css_property('display') != 'none':
                        spot.click()
                        available_dates = driver.find_elements_by_css_selector('.Date-slot-container')
                        for available_date in available_dates:
                            if available_date.value_of_css_property('display') != 'none':
                                selected_spot = available_date.find_element_by_css_selector('#slot-container-UNATTENDED')
                                if 'No doorstep delivery' not in selected_spot.text:
                                    radiobtn=wait(driver,10).until(EC.element_to_be_clickable((By.XPATH,"//span[contains(.,'Soonest available time with all items')]/preceding-sibling::input[1]")))
                                    driver.execute_script("arguments[0].click();", radiobtn)
                                    free_spaces = driver.find_element_by_css_selector('#success-sub-header')
                                    delivery_date = free_spaces.text
                                    spaces_free = True
                                    dates_available = False
                                else:
                                    print(selected_spot.text.replace('Select a time', '').strip())
                                    dates_available = False
#                next_page = driver.find_element_by_css_selector('#nextButton')
#                dates_available = next_page.get_property('disabled')
#                if dates_available: next_page.click()
                

            if spaces_free:
                print('Slots Available!')
                if args.checkout:
                    client.messages.create(to=to_mobilenumber, 
                        from_=from_mobilenumber, 
                        body="Your order will be delivered on " + delivery_date)
                    
                    coninuebtn=wait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@class='a-button-text' and @type='submit']")))
                    driver.execute_script("arguments[0].click();", coninuebtn)

                    place_order_title = "Place Your Order - Amazon.com Checkout"
                    select_payment_title = "Select a Payment Method - Amazon.com Checkout"

                    wait(driver, 10).until(lambda x: driver.title in [select_payment_title, place_order_title])

                    if driver.title == select_payment_title:

                        top_continue_button = wait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@class='a-button-text ' and @type='submit']")))
                        top_continue_button.click()


                    wait(driver, 10).until(lambda x: driver.title == place_order_title)
                    if driver.title == place_order_title:

                        place_order_button = wait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@class='a-button-text place-your-order-button']")))
                        place_order_button.click()

                else:
                    client.messages.create(to=to_mobilenumber, 
                        from_=from_mobilenumber, 
                        body="A slot was found on " + delivery_date)
                    print('Your order time will be held for the next hour.  Check your date and confirm!')

            if not dates_available:
                print('No slots available. Will check again shortly ...')
                dates_available = True
                time.sleep(5)
                driver.refresh()
        
    except Exception as e:
        raise ValueError(str(e))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="fresh-checkout")
    parser.add_argument('--checkout', '-c', action='store_true',
                        help="Select first available slot and checkout")
    args = parser.parse_args()
    find_available(args)