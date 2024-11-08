from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5.QtCore import QDateTime, QTimer
from datetime import datetime
from PyQt5.uic import loadUi
from Controller import Controller
import json
import sys
import os

class TicketChecker(QMainWindow):

    def __init__(self):
        super(TicketChecker, self).__init__()
        loadUi("files/ticket_checker.ui", self)
        self.setDate2departureStationDateEdit()
        self.readDependencies()

        self.timer = QTimer()
        self.timer.timeout.connect(self.startControl)

        self.addChromeDriverButton.clicked.connect(self.addChromeDriver)
        self.startControlButton.clicked.connect(self.startControl)
        self.clearPlainTextEdit.clicked.connect(self.clear)
        self.stopControlButton.clicked.connect(self.stop)

        self.retryCount = 0
        self.maxRetries = 3

    def stop(self):
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.timer.stop()
        self.worker.terminate()
        self.logPlainTextEdit.appendPlainText("Kontrol işlemi durduruldu.")

    def clear(self):
        self.logPlainTextEdit.clear()

    def startControl(self):
        departureStation = self.departureStationCombo.currentText()
        arrivalStation = self.arrivalStationCombo.currentText()
        travelDate = self.departureStationDateTimeEdit.date().toString("dd.MM.yyyy")
        travelTime = self.departureStationDateTimeEdit.time().toString("HH:mm")
        controlTime = self.controlTimeSpinBox.value()

        self.timer.start(controlTime * 60 * 1000)

        self.progressBar.setRange(0, 0)
        self.progressBar.show()
        
        self.worker = Controller(self.dependencies, departureStation, arrivalStation, travelDate, travelTime, controlTime)
        self.worker.controlMessage.connect(self.checkControl)
        self.worker.finished.connect(self.onControlFinished)
        self.worker.start()

    def checkControl(self, controlMessage):
        now = datetime.now()
        self.now = now.strftime("%H:%M:%S")
        log = f"Kontrol zamanı : {self.now}, "

        if controlMessage.startswith("Hata") or controlMessage.startswith("Kontrol"):
            log += controlMessage
            self.retryCount += 1
            if self.retryCount <= self.maxRetries:
                self.logPlainTextEdit.appendPlainText(f"{log}\nKontrol işlemi tekrar başlatılıyor. {self.retryCount}/{self.maxRetries}")
                self.startControl()
            else:
                log += controlMessage
                self.logPlainTextEdit.appendPlaintext(f"{log}")
                self.logPlainTextEdit.appendPlainText("Çok fazla deneme oldu, program sonlandırılıyor.")
                self.stop()
        else:
            if "Engelli" in controlMessage or "(0 )" in controlMessage:
                log += "Uygun koltuk bulunamadı!"
            elif controlMessage.startswith("Kontrol"):
                log += "Kontrol işlemi durduruldu."
            else:
                log += controlMessage
                self.progressBar.setRange(0, 100)
                self.progressBar.setValue(100)
                self.timer.stop()
                QMessageBox.information(self, "Bilgi", "Uygun koltuk tespit edildi!")
            self.retryCount = 0
            self.logPlainTextEdit.appendPlainText(log)

    def onControlFinished(self):
        print("Kontrol süreci başarıyla tamamlandı.")

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
        if os.path.exists(self.dependencies["driver_path"]):
            self.startControlButton.setEnabled(True)
        else:
            self.chromeDriverLineEdit.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    checker = TicketChecker()
    checker.show()
    sys.exit(app.exec_())