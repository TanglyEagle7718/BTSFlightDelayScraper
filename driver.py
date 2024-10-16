import os
import threading

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


class Driver:
    def __init__(self, month: int, year: int, debug_mode: bool = False):
        self.month = month
        self.year = year
        self.debug_mode = debug_mode

        # Set up download file names
        self.download_dir = "/home/practiceubuntu/Documents/CS 4641 ML Data Download Sciprts/data_files"
        self.chrome_options = Options()

        if not debug_mode:
            self.chrome_options.add_argument("--headless")  # Run in headless mode
            self.chrome_options.add_argument("--no-sandbox")  # Optional: helps avoid some issues
            self.chrome_options.add_argument("--disable-dev-shm-usage")  # Optional: overcome limited resource problems

        self.chrome_options.add_experimental_option("prefs", {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })

        # Set up the Selenium WebDriver
        self.driver = webdriver.Chrome(options=self.chrome_options)    # or webdriver.Firefox()
        self.driver.set_page_load_timeout(15*60)

        # Open the webpage
        self.driver.get('https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr')

        # List of features to be pulled from db
        self.feature_list = ["YEAR", "QUARTER", "MONTH", "DAY_OF_MONTH", "DAY_OF_WEEK", 
                        "FL_DATE", "OP_UNIQUE_CARRIER", "OP_CARRIER_AIRLINE_ID", 
                        "OP_CARRIER", "TAIL_NUM", "OP_CARRIER_FL_NUM", "ORIGIN_AIRPORT_ID", 
                        "ORIGIN_AIRPORT_SEQ_ID", "ORIGIN_CITY_MARKET_ID", "DEST_AIRPORT_ID", 
                        "DEST_AIRPORT_SEQ_ID", "DEST_CITY_MARKET_ID", "DEST", "DEST_CITY_NAME", 
                        "DEST_STATE_ABR", "CRS_DEP_TIME", "DEP_TIME", "DEP_DELAY", "DEP_DELAY_NEW", 
                        "DEP_DEL15", "DEP_DELAY_GROUP", "DEP_TIME_BLK", "TAXI_OUT", "WHEELS_OFF", 
                        "CANCELLED", "CANCELLATION_CODE", "DIVERTED", "CARRIER_DELAY", "WEATHER_DELAY", 
                        "NAS_DELAY", "SECURITY_DELAY", "LATE_AIRCRAFT_DELAY"]

        self.us_states = [
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



    def select_month(self, id: int) -> None:
        """Select the month you want to download from
        ID's:
        1. January
        2. February
        3. March
        ...
        12. December
        """
        select_element = Select(self.driver.find_element(By.ID, "cboPeriod"))  # Use the actual ID
        select_element.select_by_value(str(id)) #if you have the value attribute

    def select_year(self, year: int) -> None:
        """Select the year you want to download from
        'year' can be from [1987, 2024]
        """
        if year < 1987:
            return
        elif year > 2024:
            return
        select_element = Select(self.driver.find_element(By.ID, "cboYear"))
        select_element.select_by_value(str(year))

    def select_features(self) -> None:
        """Ensures that specific features are selected in the list"""
        for feature in self.feature_list:
            checkbox = self.driver.find_element(By.ID, feature)
            if not checkbox.is_selected():
                checkbox.click()
    
    def select_state(self, state: int) -> None:
        """Select 1 of 50 states (ignores territories)"""
        if state >= len(self.us_states) or state < 0:
            return
        select_element = Select(self.driver.find_element(By.ID, "cboGeography"))
        select_element.select_by_value(self.us_states[state])

        
    # Setting up observer for directory
    # File event handler
    class MyHandler(FileSystemEventHandler):
        def __init__(self, filename, event, download_dir: str, month: int, year: int, driver):
            self.filename = filename
            self.event = event
            self.download_dir = download_dir
            self.month = month
            self.year = year
            self.driver = driver

        def on_created(self, event):
            # Check if the created file matches the target filename
            if event.src_path.endswith(self.filename):
                # Changing the name of the downloaded file
                original_file_name = os.path.join(self.download_dir, "DL_SelectFields.zip")
                new_file_name = os.path.join(self.download_dir, f"{self.month}_{self.year}_data.zip")

                # Check if the original file exists before renaming
                if os.path.exists(original_file_name):
                    os.rename(original_file_name, new_file_name)

                self.event.set() # tell parent that we are done

    # Function to start monitoring
    def monitor_directory(self, directory, filename, event):
        event_handler = Driver.MyHandler(filename, event, self.download_dir, self.month, self.year, self.driver)
        observer = Observer()
        observer.schedule(event_handler, directory, recursive=False)
        observer.start()
        return observer


    # Function to download data for a specific month
    def download_data(self):

        # Create an event to signal when the file has been detected
        file_detected_event = threading.Event()
        observer = self.monitor_directory(self.download_dir, "DL_SelectFields.zip", file_detected_event)

        self.select_year(self.year)
        self.select_month(self.month)
        self.select_features()
        self.select_state(self.state)


        # Click the download button
        download_button = self.driver.find_element(By.ID, 'btnDownload')  # Use the actual ID
        print("downloading")
        download_button.click()
        
        # Wait for the download to complete
        file_detected_event.wait()
        observer.stop()
        observer.join()

