#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 11 16:59:13 2024

@author: practiceubuntu
"""

import os
import time

from driver import Driver

# Global parameters for tunings
start_month = 6
start_year = 2003

end_year = 2025 # Should be your end year + 1

debug_mode = True # To test for any crashes

# Loop through the months
for year in range(start_year, 2025):
    for month in range(1,13):
        if year == start_year and month < start_month: # hardcoded for starting at 6/2003 (last available date for delays)
            continue
        driver = Driver(month, year, True)
        driver.download_data()

# Close the browser
driver.quit()
