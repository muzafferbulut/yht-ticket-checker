from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from selenium.webdriver.support import expected_conditions as EC
from PyQt5.QtCore import QDateTime, QThread, pyqtSignal
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
from PyQt5.uic import loadUi
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

    def startControl(self):
        departureStation = self.departureStationCombo.currentText()
        arrivalStation = self.arrivalStationCombo.currentText()
        travelDate = self.departureStationDateTimeEdit.date().toString("dd.MM.yyyy")
        travelTime = self.departureStationDateTimeEdit.time().toString("HH:mm")
        controlTime = self.controlTimeSpinBox.value()
        
        self.worker = Controller(self.dependencies, departureStation, arrivalStation, travelDate, travelTime, controlTime)
        self.worker.controlMessage.connect(self.checkControl)
        self.worker.finished.connect(self.onControlFinished)
        self.worker.start()

    def checkControl(self, controlMessage):
        pass

    def onControlFinished(self):
        pass

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
        self.dependencies = dependencies
        self.departureStation = departureStation
        self.arrivalStation = arrivalStation
        self.date = travelDate
        self.time = travelTime
        self.controlTime = controlTime

    def run(self):
        service = Service(self.dependencies["driver_path"])
        options = webdriver.ChromeOptions()
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

        dateInput = driver.find_element(By.ID, self.dependencies["departure_date_element_id"])
        dateInput.clear()
        dateInput.send_keys(self.date)
        dateInput.send_keys(Keys.ENTER)

        time.sleep(3)

        close_date_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, self.dependencies["departure_date_elemen_close_button_css_selector"]))
        )    
        close_date_tab.click()

        searchButton = driver.find_element(By.ID, self.dependencies["search_button_id"])
        searchButton.click()
        time.sleep(10)

        bilet_durumu = driver.find_elements(By.CSS_SELECTOR, self.dependencies["ticket_control_css_selector"])

        etiketler = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, self.dependencies["ticket_control_row_label_class"]))
        )

        bilet_list = []
        for etiket in etiketler:
            bilet_list.append(etiket.text)
            print(etiket.text)

        print(bilet_list[-7])
        print(bilet_list[-8])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    report = TicketChecker()
    report.show()
    sys.exit(app.exec_())