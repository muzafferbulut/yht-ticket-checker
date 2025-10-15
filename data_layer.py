"Selenium ile konuşan ve ham veriyi çeken uzman sınıf."
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from abc import ABC, abstractmethod
from selenium import webdriver
import pandas as pd
import time

class ITicketSearchService(ABC):
    "Bilet alma işlemlerini soyutlayan arayüz"

    @abstractmethod
    def search_and_get_raw_results(self, search_params: dict) -> str:
        pass

    @abstractmethod
    def get_station_data(self) -> dict:
        "istasyon adlarını ve ID"
        pass

class SeleniumScraperService(ITicketSearchService):
    "selenium ile tcdd sitesinden veri kazır."

    def __init__(self, dependencies:dict):
        self.dependencies = dependencies

    def _wait_and_send_keys(self, driver, elemend_id, value, is_enter_needed=True):
        "elementi bekler, temizler ve veri gönderir."
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located(By.ID, elemend_id))
        element.clear()
        element.send_keys(value)

        if is_enter_needed:
            element.send_keys(Keys.ENTER)

    def get_station_data(self) -> dict:
        """Simülasyon: İstasyon verilerini döndürür (Gerçek projede kazınabilir)."""
        return {
            "Ankara Gar": 234516259, "Eskişehir": 234516254, "Sivas": 234517773,
            "İstanbul(Söğütlüçeşme)": 234517773, "Konya": 234516260,
            "İstanbul(Pendik)": 234517782, "İstanbul(Halkalı)": 234517785
        }

    def search_and_get_raw_result(self, search_params: dict) -> str:
        """
        Web sitesinde gezinme, veri kazıma ve Pandas ile filtreleme işlemlerini yapar.
        """
        service = Service(self.dependencies["driver_path"])
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(service=service, options=options)
        
        try:
            driver.get(self.dependencies["tcdd_link"])
            
            # --- Web Sitesinde Gezinme Mantığı ---
            self._wait_and_send_keys(driver, self.dependencies["departure_element_id"], search_params["departureStation"])
            self._wait_and_send_keys(driver, self.dependencies["arrival_element_id"], search_params["arrivalStation"])
            
            # Tarih Girişi
            date_input = driver.find_element(By.ID, self.dependencies["departure_date_element_id"])
            date_input.clear()
            date_input.send_keys(search_params["travelDate"])
            date_input.send_keys(Keys.ENTER)
            
            # Tarih sekmesini kapat
            wait = WebDriverWait(driver, 10)
            close_selector = self.dependencies["departure_date_element_close_button_css_selector"]
            close_date_tab = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, close_selector)))
            close_date_tab.click()

            # Arama butonu ve tıklama
            searchButton = driver.find_element(By.ID, self.dependencies["search_button_id"])
            searchButton.click()
            time.sleep(5) 
            
            # --- Veri Kazıma ve İşleme (Pandas) ---
            rows = driver.find_elements(By.CSS_SELECTOR, self.dependencies["ticket_control_css_selector"])
            
            data = []
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                row_data = [cell.text for cell in cells]
                data.append(row_data)

            df = pd.DataFrame(data)
            # Seçilen saate göre filtreleme
            filtered_df = df[df[0].str.contains(search_params["travelTime"])].values
            
            if filtered_df.size > 0:
                return filtered_df[0][4] 
            else:
                return "Kontrol: Uygun sefer bulunamadı."

        except Exception as e:
            return f"Hata: Tarayıcı İşlemi Başarısız. Detay: {str(e)[:100]}"
            
        finally:
            driver.quit()