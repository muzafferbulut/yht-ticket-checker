from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from selenium.webdriver.support import expected_conditions as EC
from PyQt5.QtCore import QDateTime, QThread, pyqtSignal
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from datetime import datetime
from PyQt5.uic import loadUi
import pandas as pd
import time
import sys
import json

class TicketChecker(QMainWindow):

    def __init__(self):
        super(TicketChecker, self).__init__()
        loadUi("files/ticket_checker.ui", self)
        self.setDate2departureStationDateEdit()
        self.readDependencies()

        self.addChromeDriverButton.clicked.connect(self.addChromeDriver)
        self.startControlButton.clicked.connect(self.startControl)
        self.clearPlainTextEdit.clicked.connect(self.clear)

    def clear(self):
        self.logPlainTextEdit.clear()

    def startControl(self):
        departureStation = self.departureStationCombo.currentText()
        arrivalStation = self.arrivalStationCombo.currentText()
        travelDate = self.departureStationDateTimeEdit.date().toString("dd.MM.yyyy")
        travelTime = self.departureStationDateTimeEdit.time().toString("HH:mm")
        controlTime = self.controlTimeSpinBox.value()

        self.progressBar.setRange(0, 0)
        self.progressBar.show()
        
        self.worker = Controller(self.dependencies, departureStation, arrivalStation, travelDate, travelTime, controlTime)
        self.worker.controlMessage.connect(self.checkControl)
        self.worker.finished.connect(self.onControlFinished)
        self.worker.start()

    def checkControl(self, controlMessage):
        now = datetime.now()
        now = now.strftime("%H:%M:%S")
        message = f"Kontrol zamanı : {now}, {controlMessage}"
        self.logPlainTextEdit.appendPlainText(message)

    def onControlFinished(self):
        QMessageBox.information(self, "Kontrol Tamamlandı", "Bilet kontrolü tamamlandı!")

    def addChromeDriver(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Exe Dosyası Seç", "", "Exe Files (*.exe)")
        if file_path:
            self.chromeDriverLineEdit.setText(file_path)
            self.changeDriverPath(file_path)
        else:
            QMessageBox.warning(self, "Uyarı", "Driver seçmeden kontrol uygulamasını çalıştıramazsınız!")
        self.startControlButton.setEnabled(True)

    def setDate2departureStationDateEdit(self):
        self.departureStationDateTimeEdit.setDateTime(QDateTime.currentDateTime())

    def changeDriverPath(self, driver_path):
        self.dependencies["driver_path"] = driver_path
        with open("files/dependencies.json", "w") as file:
            json.dump(self.dependencies, file, ensure_ascii=False, indent=4)

    def readDependencies(self):
        with open("files/dependencies.json", "r") as file:
            self.dependencies = json.load(file)
        self.chromeDriverLineEdit.setText(self.dependencies["driver_path"])
        if self.dependencies["driver_path"] != "":
            self.startControlButton.setEnabled(True)

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
            options.add_argument("--headless")
            driver = webdriver.Chrome(service=service, options=options)

            driver.get(self.dependencies["tcdd_link"])
            time.sleep(3)

            wait = WebDriverWait(driver, 10)
            
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    checker = TicketChecker()
    checker.show()
    sys.exit(app.exec_())