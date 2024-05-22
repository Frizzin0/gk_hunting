
import streamlit as st
import time
import pandas as pd
import os
from tqdm.notebook import tqdm


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from multiprocessing import Pool


def enlist_restaurants(url):  
    # Initialize the WebDriver (e.g., Chrome)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

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

        # Wait for the main button to be clickable and click it
        try:
            main_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.ccl-b91164e9bf573ff0')))
            main_button.click()
            print("Main button clicked.")
        except Exception as e:
            print("Main button not found or not clickable:", e)

        # Wait for the elements to load after clicking the button
        time.sleep(3)  # Adjust the sleep time as necessary or use more sophisticated waits

        # Get the page source after the elements have loaded
        page_source = driver.page_source

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Find all list elements with the specified class
        list_items = soup.find_all('li', class_='home-map__card-spacer HomeMapCards-67670a91a1d402aa')

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

        # Print the DataFrame

    finally:
        # Close the WebDriver
        driver.quit()

    return df


def collect_info_on_restaurants(df):
    count = 0
    for res in tqdm(df['href'][0:20]):
        # Initialize WebDriver (this will automatically download the correct version of ChromeDriver)
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

        # Define the URL to test
        url = res  # Replace with the actual URL from your DataFrame

        # Open the URL
        driver.get(url)

        # Wait for the page to load completely
        time.sleep(5)  # Adjust this time as necessary

        try:
            # Handle the cookie pop-up if it appears
            # Accept cookies if the popup is present
            try:
                cookie_button = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Accetta") or contains(text(), "accetto")]')))
                cookie_button.click()
                time.sleep(1)  # Adjust this time if necessary
                print("Cookie button clicked.")
            except Exception as e:
                print("No cookie pop-up detected or unable to close it:", e)

            
            #Handle "Restaurant can't accept orders"
            #time.sleep(1)
            #try:
            #    close_button = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.CLASS_NAME, "ccl-388f3fb1d79d6a36.ccl-9ed29b91bb2d9d02.ccl-59eced23a4d9e077.ccl-7be8185d0a980278")))
            #    close_button.click()
            #    time.sleep(1)  # Adjust this time if necessary
            #    print("Close button clicked.")
            #except Exception as e:
            #    print("Close button for 'Restaurant can't accept orders' pop-up not found:", e)
        

                
            # Locate the parent element that contains the button
            parent_element = driver.find_element(By.CLASS_NAME, "UIHeaderInfoRows-023104015d7355b8.ccl-a5e1512b87ef2079")
            
            # Find and click the button within this parent element
            button = parent_element.find_element(By.CLASS_NAME, "ccl-4704108cacc54616.ccl-4f99b5950ce94015.ccl-724e464f2f033893")
            button.click()
            
            # Wait for the pop-up to load
            time.sleep(1)  # Adjust this time as necessary
            
            # Find the parent element of the popup
            popup_element = driver.find_element(By.CLASS_NAME, "ccl-9237ff225b0d2789.ccl-e770a464a394226e.ccl-bae50209245d2304")
        
            # Find all elements with the class name "UIContentCard-32d54d142ca96f5c" within the popup
            link_elements = popup_element.find_elements(By.CLASS_NAME, "UIContentCard-32d54d142ca96f5c")
            
            # Extract the href attribute from the second link element
            if len(link_elements) >= 2:
                link = link_elements[1].get_attribute("href")
                df.loc[df['href']==res, 'Link'] = link
                
                # Find all elements with the class name "UILines-eb427a2507db75b3" within the popup
                text_elements = popup_element.find_elements(By.CLASS_NAME, "UILines-eb427a2507db75b3")
                
                # Extract the text from the second text element
                tex = ''
                for t in text_elements:
                    tex = tex + '^' + t.text
                aux.append(tex)
                df.loc[df['href']==res, 'text'] = tex
            else:
                print("Second link element not found")

        except Exception as e:
            print("Error:", e)

        # Close the WebDriver
        count += 1
        st.write(count)
        driver.quit()


def main():

    st.title("Ghostkitchen Hunting")
    url = st.text_input("Enter the URL:", "https://deliveroo.it/it/restaurants/cosenza/cosenza/?fulfillment_method=COLLECTION&geohash=sqgx9exh8hsc&delivery_time=1716402600")

    if st.button("Fetch Data"):
        df = enlist_restaurants(url)
        df = collect_info_on_restaurants(df)
    
    st.write(df)

if __name__ == "__main__":
    main()