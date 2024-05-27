pip install playwright --upgrade
pip install selenium --upgrade
pip install BeautifulSoup --upgrade

from playwright.sync_api import sync_playwright
import pandas as pd
import time
from tqdm import tqdm
import re


#selenium components
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_experimental_option(
        "prefs", {
            # block image loading
            "profile.managed_default_content_settings.images": 2,
        }
    )



def enlist_restaurants(url):  
    # Initialize the WebDriver (e.g., Chrome)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # Open the webpage
        driver.get(url)

        # Accept cookies if the popup is present
        try:
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Accetta") or contains(text(), "accetto")]')))
            cookie_button.click()
            time.sleep(1)  # Adjust this time if necessary
            print("Cookie button clicked.")
        except Exception as e:
            print("No cookie pop-up detected or unable to close it:", e)

        # Handle the popup after accepting cookies
        try:
            popup_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'ccl-388f3fb1d79d6a36.ccl-6d2d597727bd7bab.ccl-59eced23a4d9e077.ccl-7be8185d0a980278')))
            popup_button.click()
            time.sleep(1)  # Adjust this time if necessary
            print("Popup button clicked.")
        except Exception as e:
            print("No popup detected or unable to close it:", e)

        # Wait for the elements to load after clicking the button
        time.sleep(3)  # Adjust the sleep time as necessary or use more sophisticated waits

        # Get the page source after the elements have loaded
        page_source = driver.page_source

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Find all list elements with the specified class
        list_items = soup.find_all('li', class_='HomeFeedGrid-b0432362335be7af')

        # Extract href and aria-label from the desired elements within each list item
        result = []
        for item in list_items:
            a_element = item.find('a', class_='HomeFeedUICard-3e299003014c14f9')
            if a_element:
                href = "https://deliveroo.it" + a_element.get('href')
                aria_label = a_element.get('aria-label')
                result.append({'href': href, 'aria-label': aria_label})

        # Create a DataFrame from the result list
        df = pd.DataFrame(result)


    finally:
        # Close the WebDriver
        driver.quit()

        return df


def handle_dialog(dialog):
    if "non può ricevere ordini" in dialog.message:
        print(f'clicking "Yes" to {dialog.message}')
        dialog.accept()  # press "Yes"
    else:
        dialog.dismiss()  # press "No"


def collect_info_on_restaurants(df):
    all_res = []

    for res in tqdm(df['href']):
        
        # Running Playwright & open website
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        page.on("dialog", lambda dialog: handle_dialog(dialog))


        page.goto(res, wait_until='networkidle')
        time.sleep(0.5)
        data_item = ""
        
        page.get_by_text("Allergeni e tanto altro").click()
        items = page.locator('//span[@class="ccl-649204f2a8e630fd ccl-6f43f9bb8ff2d712"]').all()
        phones = page.locator('//span[@class="ccl-649204f2a8e630fd ccl-98a86d2cf2dd0739"]').all()
        
        for item in items:
            data_item += "^" + item.inner_text()

        for phone in phones:
            data_item += "^" + phone.inner_text()

        all_res.append(data_item)
        
        #
        browser.close()
        playwright.stop()

    #print(len(all_res))
    #print(all_res)
    df['text'] = all_res
    
    return df



def data_cleaning(df):
    df['text'] = df['text'].map(lambda x: str(x).split('^')[1:])

    def extract_phone_number(text_list):
        phone_pattern = re.compile(r'\+?\d[\d -]{8,12}\d')
        for text in text_list:
            match = phone_pattern.search(text)
            if match:
                return match.group()
        return None


    def extract_address(text_list):
        address_pattern = re.compile(r'.*[a-zA-Z].*\d{5}$')
        for text in text_list:
            if address_pattern.match(text) and not text.startswith("Chiama"):
                return text
        return None

    df['phone_number'] = df['text'].apply(extract_phone_number)
    df['address'] = df['text'].apply(extract_address)

    # Function to handle the aggregation logic
    def aggregate_column(series):
        if series.nunique() == 1:
            return series.iloc[0]
        else:
            return series.unique().tolist()

    #Select only the columns needed for aggregation
    columns_to_aggregate = ['href', 'aria-label', 'text', 'phone_number']

    # Group by "address" and aggregate
    grouped = df.groupby('address')[columns_to_aggregate].agg({
        'text': 'count',  # Count the number of occurrences for "n°"
        'aria-label': aggregate_column,
        'href': aggregate_column,
        'phone_number': aggregate_column
    }).reset_index()

    # Add the 'text' column with a custom aggregation
    grouped['description'] = df.groupby('address')['text'].apply(lambda x: ', '.join(map(str, x))).values

    # Rename the columns as needed
    grouped.rename(columns={'text': 'n°'}, inplace=True)
    # Sort the DataFrame by the "n°" column
    grouped = grouped.sort_values(by='n°', ascending=False)
    return grouped

def main():

    print("input url")
    url = input()
    df = enlist_restaurants(url)
    df = collect_info_on_restaurants(df)
    df = data_cleaning(df)

    print("output file name")
    output = input()
    df.to_excel(output)

main()
