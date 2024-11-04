from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver_path = "chromedriver.exe"
kalkis = "Ankara Gar"
varis = "İstanbul(Söğütlüçeşme)"
tarih = "15.11.2024"

service = Service(driver_path)

options = webdriver.ChromeOptions()

driver = webdriver.Chrome(service=service, options=options)

driver.get("https://ebilet.tcddtasimacilik.gov.tr/view/eybis/tnmGenel/tcddWebContent.jsf")
time.sleep(2)
wait = WebDriverWait(driver, 10)

kalkis_input = wait.until(EC.presence_of_element_located((By.ID, "nereden")))
kalkis_input.clear()
kalkis_input.send_keys(kalkis)
time.sleep(1)
kalkis_input.send_keys(Keys.ENTER)

# Varış yeri
varis_input = driver.find_element(By.ID, "nereye")
varis_input.clear()
varis_input.send_keys(varis)
time.sleep(1)
varis_input.send_keys(Keys.ENTER)

time.sleep(3)
tarih_input = driver.find_element(By.ID, "trCalGid_input")
tarih_input.clear()
tarih_input.send_keys(tarih)
tarih_input.send_keys(Keys.ENTER)

time.sleep(3)

kapanma_butonu = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.CSS_SELECTOR, "#ui-datepicker-div > div.ui-datepicker-buttonpane.ui-widget-content > button.ui-datepicker-close.ui-state-default.ui-priority-primary.ui-corner-all"))
)    
kapanma_butonu.click()

ara_buton = driver.find_element(By.ID, "btnSeferSorgula")
ara_buton.click()
time.sleep(10)
bilet_durumu = driver.find_elements(By.CSS_SELECTOR, ".seferRow")

etiketler = WebDriverWait(driver, 10).until(
    EC.presence_of_all_elements_located((By.CLASS_NAME, "ui-selectonemenu-label"))
)

bilet_list = []
for etiket in etiketler:
    bilet_list.append(etiket.text)
    print(etiket.text)

print(bilet_list[-7])
print(bilet_list[-8])