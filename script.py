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
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException



# Global parameters for tunings
start_month = 12
start_year = 2003

end_year = 2025 # Should be your end year + 1

beginning_year = 2003
beginning_month = 1


year_reached: bool = False
month_reached: bool = False


debug_mode = True # To test for any crashes


# Set up download file names
download_dir = "/home/practiceubuntu/Documents/BTSFlightDelayScraper/data_files"
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
driver.get('https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr')

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

us_states = [
                "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", 
                "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", 
                "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", 
                "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", 
                "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", 
                "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", 
                "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", 
                "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", 
                "Washington", "West Virginia", "Wisconsin", "Wyoming", "U.S. Pacific Trust Territories and Possessions", "U.S. Virgin Islands"
            ]
beginning_state = 0


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

def select_state(state: int) -> None:
    """Select 1 of 50 states (ignores territories)"""
    if state >= len(us_states) or state < 0:
        return
    select_element = Select(driver.find_element(By.ID, "cboGeography"))
    select_element.select_by_value(us_states[state])

    
# Setting up observer for directory
# File event handler
class MyHandler(FileSystemEventHandler):
    def __init__(self, filename, event, state, month, year):
        self.filename = filename
        self.event = event
        self.state = state
        self.month = month
        self.year = year

    def on_created(self, event):
        # Check if the created file matches the target filename
        
        if event.src_path.endswith(".zip"):
            # Changing the name of the downloaded file

            newest_file_name = str(event.src_path).split("/")[-1]
            time.sleep(2)

            original_file_name = os.path.join(download_dir, newest_file_name)
            new_file_name = os.path.join(download_dir, f"{self.month}_{self.year}_{us_states[self.state]}_data.zip")

            # Check if the original file exists before renaming
            if os.path.exists(original_file_name):
                os.rename(original_file_name, new_file_name)
            print("A file has been renamed from", original_file_name, "to", new_file_name)
            self.event.set() # tell parent that we are done

# Function to start monitoring
def monitor_directory(directory, filename, event, state: int, month: int, year: int):
    event_handler = MyHandler(filename, event, state, month, year)
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=False)
    observer.start()
    return observer


# Function to download data for a specific month
def download_data(month: int, year: int, state: int):

    # Create an event to signal when the file has been detected
    file_detected_event = threading.Event()
    observer = monitor_directory(download_dir, "DL_SelectFields.zip", file_detected_event, state, month, year)

    select_year(year)
    select_month(month)
    select_features()
    select_state(state)


    # Click the download button
    download_button = driver.find_element(By.ID, 'btnDownload')  # Use the actual ID
    print("downloading", month, ",", year, "at", us_states[state])
    download_button.click()

    try:
        lbl_note = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'lblNote'))
        )
        
        # Check the text of lblNote for error indication
        if lbl_note.text:
            #print("Download error detected:", lbl_note.text)
            file_detected_event.set()
            observer.stop()
            observer.join()
            driver.get('https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr')
            print("Unable to download info for", us_states[state])
            return
        else:
            pass
    except TimeoutException:
        print("The lblNote element did not appear; assuming download was successful.")
    
    # Wait for the download to complete
    file_detected_event.wait()
    observer.stop()
    observer.join()





# Loop through the months
for year in range(start_year, 2025):

    if year < beginning_year:
        continue
    else:
        year_reached = True

    for month in range(1,13):

        if not year_reached:
            continue
        else:
            if not month_reached and month < beginning_month:
                continue
            month_reached = True

        for state in range(len(us_states)):
            if year == start_year and month < start_month: # hardcoded for starting at 6/2003 (last available date for delays)
                continue
            if not month_reached:
                continue
            else:
                if state < beginning_state:
                    continue

            download_data(month, year, state)

# Close the browser
driver.quit()
