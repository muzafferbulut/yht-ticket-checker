from selenium.webdriver.support import expected_conditions as EC
from PyQt5.QtCore import QThread, pyqtSignal
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
import pandas as pd
import time

class Controller(QThread):
    finished = pyqtSignal()
    controlMessage = pyqtSignal(str)

    def __init__(self, dependencies, departureStation, arrivalStation, travelDate, travelTime, controlTime):
        super().__init__()
        self.dependencies = dependencies
        self.departureStation = departureStation
        self.arrivalStation = arrivalStation
        self.date = travelDate
        self.time = travelTime
        self.controlTime = controlTime

    def run(self):
        try:
            service = Service(self.dependencies["driver_path"])
            options = webdriver.ChromeOptions()
            driver = webdriver.Chrome(service=service, options=options)

            driver.get(self.dependencies["tcdd_link"])
            time.sleep(5)

            wait = WebDriverWait(driver, 15)
            
            # departure
            departure = wait.until(EC.presence_of_element_located((By.ID, self.dependencies["departure_element_id"])))
            departure.clear()
            departure.send_keys(self.departureStation)
            time.sleep(3)
            departure.send_keys(Keys.ENTER)

            # arrival
            arrival = driver.find_element(By.ID, self.dependencies["arrival_element_id"])
            arrival.clear()
            arrival.send_keys(self.arrivalStation)
            time.sleep(3)
            arrival.send_keys(Keys.ENTER)
            
            time.sleep(3)

            # date input
            dateInput = driver.find_element(By.ID, self.dependencies["departure_date_element_id"])
            dateInput.clear()
            dateInput.send_keys(self.date)
            dateInput.send_keys(Keys.ENTER)

            time.sleep(3)

            # close date tab
            close_date_tab = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.dependencies["departure_date_element_close_button_css_selector"]))
            )    
            close_date_tab.click()

            searchButton = driver.find_element(By.ID, self.dependencies["search_button_id"])
            searchButton.click()
            time.sleep(5)

            rows = driver.find_elements(By.CSS_SELECTOR, self.dependencies["ticket_control_css_selector"])
            data = []

            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                row_data = [cell.text for cell in cells]
                data.append(row_data)

            df = pd.DataFrame(data)
            filtered_df = df[df[0].str.contains(self.time)].values

            self.controlMessage.emit(filtered_df[0][4])

        except Exception as e:
            self.controlMessage.emit(f"Hata: {e}")
        
        finally:
            driver.quit()
            self.finished.emit()
