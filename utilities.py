"Uygulamanın konfigürasyonunu ve dosya işlemlerini yöneten sınıf."
import os
import json

class DependencyManager:
    """HELP:
        Dosya okur, yazar, uygulama bağımlılıklarını yönetir.
    """

    def __init__(self, file_path="files/dependencies.json"):
        self.file_path = file_path
        self.dependencies = self._load()

    def _load(self) -> dict:
        "konfigürasyon dosyasını yükler veya varsayılan değerleri döndürür."
        default_deps = {
            "driver_path": "", 
            "tcdd_link": "https://yebsp.tcddtasimacilik.gov.tr", 
            "departure_element_id": "DepartureStation", 
            "arrival_element_id": "ArrivalStation",
            "departure_date_element_id": "DepartureDate", 
            "search_button_id": "SearchButton",
            "departure_date_element_close_button_css_selector": "button.close",
            "ticket_control_css_selector": ".table-responsive table tbody tr"
        }

        try:
            with open(self.file_path, "r",encoding="utf-8") as file:
                loaded = json.load(file)
                return {**default_deps, **loaded}
        except (FileNotFoundError, json.JSONDecodeError):
            return default_deps
        
    def save_driver_path(self, driver_path:str):
        self.dependencies["driver_path"] = driver_path
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(self.dependencies, file, ensure_ascii=False, indent=4)