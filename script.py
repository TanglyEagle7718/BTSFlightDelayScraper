#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 11 16:59:13 2024

@author: practiceubuntu
"""

import os
import time
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

# Global parameters for tunings
start_month = 6
start_year = 2003

end_year = 2025 # Should be your end year + 1

debug_mode = True # To test for any crashes

# Set up download file names
download_dir = "/home/practiceubuntu/Documents/CS 4641 ML Data Download Sciprts/data_files"
chrome_options = Options()

if not debug_mode:
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")  # Optional: helps avoid some issues
    chrome_options.add_argument("--disable-dev-shm-usage")  # Optional: overcome limited resource problems

chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

# Set up the Selenium WebDriver
driver = webdriver.Chrome(options=chrome_options)    # or webdriver.Firefox()
driver.set_page_load_timeout(15*60)

# Open the webpage
driver.get('https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ&QO_fu146_anzr=')

# List of features to be pulled from db
feature_list = ["YEAR", "QUARTER", "MONTH", "DAY_OF_MONTH", "DAY_OF_WEEK", 
                "FL_DATE", "OP_UNIQUE_CARRIER", "OP_CARRIER_AIRLINE_ID", 
                "OP_CARRIER", "TAIL_NUM", "OP_CARRIER_FL_NUM", "ORIGIN_AIRPORT_ID", 
                "ORIGIN_AIRPORT_SEQ_ID", "ORIGIN_CITY_MARKET_ID", "DEST_AIRPORT_ID", 
                "DEST_AIRPORT_SEQ_ID", "DEST_CITY_MARKET_ID", "DEST", "DEST_CITY_NAME", 
                "DEST_STATE_ABR", "CRS_DEP_TIME", "DEP_TIME", "DEP_DELAY", "DEP_DELAY_NEW", 
                "DEP_DEL15", "DEP_DELAY_GROUP", "DEP_TIME_BLK", "TAXI_OUT", "WHEELS_OFF", 
                "CANCELLED", "CANCELLATION_CODE", "DIVERTED", "CARRIER_DELAY", "WEATHER_DELAY", 
                "NAS_DELAY", "SECURITY_DELAY", "LATE_AIRCRAFT_DELAY"]



def select_month(id: int) -> None:
    """Select the month you want to download from
    ID's:
    1. January
    2. February
    3. March
    ...
    12. December
    """
    select_element = Select(driver.find_element(By.ID, "cboPeriod"))  # Use the actual ID
    select_element.select_by_value(str(id)) #if you have the value attribute

def select_year(year: int) -> None:
    """Select the year you want to download from
    'year' can be from [1987, 2024]
    """
    if year < 1987:
        return
    elif year > 2024:
        return
    select_element = Select(driver.find_element(By.ID, "cboYear"))
    select_element.select_by_value(str(year))

def select_features() -> None:
    """Ensures that specific features are selected in the list"""
    for feature in feature_list:
        checkbox = driver.find_element(By.ID, feature)
        if not checkbox.is_selected():
            checkbox.click()
    

# Function to download data for a specific month
def download_data(year: int, month: int):

    select_year(year)
    select_month(month)
    select_features()


    # Click the download button
    download_button = driver.find_element(By.ID, 'btnDownload')  # Use the actual ID
    print("downloading")
    download_button.click()
    
    time.sleep(10*60)

    # Changing the name of the downloaded file
    original_file_name = os.path.join(download_dir, "DL_SelectFields.zip")
    new_file_name = os.path.join(download_dir, f"{month}_{year}_data.zip")

    # Check if the original file exists before renaming
    if os.path.exists(original_file_name):
        os.rename(original_file_name, new_file_name)




# Loop through the months
for year in range(2024, start_year-1, -1):
    for month in range(1,13):
        if year == start_year and month < start_month: # hardcoded for starting at 6/2003 (last available date for delays)
            continue
        download_data(year, month)

        
# Close the browser
driver.quit()
