"UI kuran, tüm akışı birleştiren ve yöneten sınıf."

import sys
import os
import json
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QLabel, QComboBox, QDateTimeEdit, QSpinBox,
    QPushButton, QLineEdit, QGroupBox, QPlainTextEdit,
    QProgressBar, QFileDialog, QMessageBox
)
from PyQt5.QtCore import QDateTime, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon

from data_layer import SeleniumScraperService, ITicketSearchService 
from domain import TicketAvailabilityChecker, ControlStatus
from utilities import DependencyManager

class WorkerThread(QThread):
    controlMessage = pyqtSignal(dict)

    def __init__(self, checker: TicketAvailabilityChecker, search_params:dict):
        super().__init__()
        self.checker = checker
        self.search_params = search_params
        
    def run(self):
        result = self.checker.check_and_process(self.search_params)
        self.controlMessage.emit(result)

class TicketCheckerApp(QMainWindow):

    def __init__(self):
        super().__init__()
        # 1. Uzmanları Oluştur (DIP & Kompozisyon)
        self.dep_manager = DependencyManager()
        self.dependencies = self.dep_manager.dependencies
        
        # Servis ve İş Mantığı oluşturulurken Dependency Injection kullanılır
        self.ticket_service = SeleniumScraperService(self.dependencies) 
        self.checker = TicketAvailabilityChecker(self.ticket_service)
        
        # 2. UI ve Sinyal Yönetimi
        self.setup_ui_elements() 
        self.init_app_state()
        self.connect_signals()

    def setup_ui_elements(self):
        # Sizin XML'inizden yeniden oluşturulan UI tasarımı
        self.setWindowTitle("YHT Ticket Control"); self.setFixedSize(470, 600)
        centralwidget = QWidget(self); self.setCentralWidget(centralwidget)
        main_layout = QVBoxLayout(centralwidget); main_layout.setContentsMargins(5, 5, 5, 5)

        self.groupBox = QGroupBox(centralwidget); self.groupBox.setTitle(" Bilgiler ")
        self.groupBox_3 = QGroupBox(centralwidget); self.groupBox_3.setTitle(" Kontrol ")
        self.groupBox_2 = QGroupBox(centralwidget); self.groupBox_2.setTitle(" Geçmiş ")

        self.chromeDriverLineEdit = QLineEdit(); self.chromeDriverLineEdit.setEnabled(False)
        self.departureStationDate = QDateTimeEdit(); self.departureStation = QComboBox(); self.arrivalStation = QComboBox()
        self.controlTime = QSpinBox(); self.controlTime.setMinimum(5); self.controlTime.setMaximum(60); self.controlTime.setValue(5)
        
        self.addChromeDriverButton = QPushButton("Driver Seç"); self.start_control = QPushButton("Kontrolü Başlat"); 
        self.finish_control = QPushButton("Kontrolü Bitir"); self.clear_log = QPushButton("Logları Temizle")
        self.logPlainText = QPlainTextEdit(); self.logPlainText.setReadOnly(True); self.progressBar = QProgressBar()

        formLayout = QFormLayout();
        formLayout.addRow(QLabel("Chrome Driver :"), self.chromeDriverLineEdit); formLayout.addWidget(self.addChromeDriverButton)
        formLayout.addRow(QLabel("Tarih :"), self.departureStationDate); formLayout.addRow(QLabel("Kalkış İstasyonu: "), self.departureStation)
        formLayout.addRow(QLabel("Varış İstasyonu :"), self.arrivalStation); formLayout.addRow(QLabel("Kontrol Aralığı (Dk.) : "), self.controlTime)
        self.groupBox.setLayout(formLayout)

        buttonsLayout = QHBoxLayout(); buttonsLayout.addWidget(self.start_control); buttonsLayout.addWidget(self.finish_control); buttonsLayout.addWidget(self.clear_log)
        self.groupBox_3.setLayout(buttonsLayout)

        logLayout = QVBoxLayout(); logLayout.addWidget(self.logPlainText); logLayout.addWidget(self.progressBar)
        self.groupBox_2.setLayout(logLayout)

        main_layout.addWidget(self.groupBox); main_layout.addWidget(self.groupBox_3); main_layout.addWidget(self.groupBox_2)

        # İstasyon verilerini yükle
        station_names = list(self.ticket_service.get_station_data().keys())
        self.departureStation.addItems(station_names); self.arrivalStation.addItems(station_names)
        self.show()

    def init_app_state(self):
        self.finish_control.setEnabled(False)
        self.update_driver_ui()
        self.progressBar.setVisible(False)
        self.departureStationDate.setDateTime(QDateTime.currentDateTime().addDays(1))

    def connect_signals(self):
        self.addChromeDriverButton.clicked.connect(self.addChromeDriver)
        self.start_control.clicked.connect(self.startControl)
        self.clear_log.clicked.connect(self.logPlainText.clear)
        self.finish_control.clicked.connect(self.stopControl)

    def update_driver_ui(self):
        driver_path = self.dependencies.get("driver_path", "")
        self.chromeDriverLineEdit.setText(driver_path)
        if os.path.exists(driver_path) and driver_path:
            self.start_control.setEnabled(True)
        else:
            self.start_control.setEnabled(False)

    def stopControl(self):
        # Kontrolü durdurma mantığı (DRY ve Temiz Kod)
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        if hasattr(self, 'worker') and self.worker.isRunning():
            # QThread sonlandırma
            self.worker.terminate()
            
        self.checker.is_running = False 
        self.logPlainText.appendPlainText(f"\n[{datetime.now().strftime('%H:%M:%S')}] KONTROL DURDURULDU.")
        self.progressBar.setVisible(False)
        self.start_control.setEnabled(True)
        self.finish_control.setEnabled(False)
        self.checker.retry_count = 0 

    def startControl(self):
        # Kontrolü başlatma mantığı
        self.checker.is_running = True
        self.logPlainText.appendPlainText(f"\n--- YENİ KONTROL BAŞLATILIYOR ---")
        
        control_time_minutes = self.controlTime.value()
        
        if not hasattr(self, 'timer'):
            self.timer = QTimer()
            self.timer.timeout.connect(self._run_worker)
        self.timer.start(control_time_minutes * 60 * 1000)
        
        self.start_control.setEnabled(False)
        self.finish_control.setEnabled(True)
        self._run_worker() # İlk çalıştırmayı hemen yap

    def _run_worker(self):
        # Thread'i başlatma mantığı (SRP: Thread Yönetimi)
        search_params = {
            "departureStation": self.departureStation.currentText(),
            "arrivalStation": self.arrivalStation.currentText(),
            "travelDate": self.departureStationDate.date().toString("dd.MM.yyyy"),
            "travelTime": self.departureStationDate.time().toString("HH:mm"),
        }
        
        self.progressBar.setRange(0, 0)
        self.progressBar.setVisible(True)

        self.worker = WorkerThread(self.checker, search_params)
        self.worker.controlMessage.connect(self.processControlResult)
        self.worker.start()

    def processControlResult(self, result: dict):
        # Sonuç işleme mantığı (Temiz Kod: Durum Kodları ile Kontrol)
        now_time = datetime.now().strftime("%H:%M:%S")
        self.progressBar.setVisible(False)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        
        log_message = f"[{now_time}] "

        if result["status"] == ControlStatus.SUCCESS:
            log_message += f"BAŞARILI: {result['message']}"
            self.logPlainText.appendPlainText(log_message)
            QMessageBox.information(self, "Bilgi", "UYGUN KOLTUK TESPİT EDİLDİ!")
            self.stopControl()
        
        elif result["status"] == ControlStatus.RETRY:
            log_message += f"TEKRAR DENEME: {result['message']}"
            self.logPlainText.appendPlainText(log_message)
            
        elif result["status"] == ControlStatus.FATAL_ERROR:
            log_message += f"KRİTİK HATA: {result['message']}"
            self.logPlainText.appendPlainText(log_message)
            self.stopControl()

        else: # NOT_FOUND veya STOPPED
            log_message += f"KONTROL TAMAMLANDI: {result['message']}"
            self.logPlainText.appendPlainText(log_message)

    def addChromeDriver(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Exe Dosyası Seç", "", "Exe Files (*.exe)")
        if file_path:
            self.dep_manager.save_driver_path(file_path)
            self.dependencies = self.dep_manager.dependencies 
            self.update_driver_ui()
        else:
            QMessageBox.warning(self, "Uyarı", "Driver seçimi zorunludur!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # DependencyManager'ın başlatılması (Dosya yapısını hazırlar)
    DependencyManager().save_driver_path(DependencyManager().dependencies.get("driver_path", ""))
    
    checker = TicketCheckerApp()
    sys.exit(app.exec_())