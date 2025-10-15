"Veriyi işleyen ve sonuçları analiz eden ana kontrol sınıfı."

from data_layer import ITicketSearchService
from datetime import datetime

class ControlStatus:
    SUCCESS = "SUCCESS"
    NOT_FOUND = "NOT_FOUND"
    RETRY = "RETRY"
    FATAL_ERROR = "FATAL_ERROR"
    STOPPED = "STOPPED"

class TicketAvailabilityChecker:
    "Bilet kontrol etme iş mantığını yönetir ve sonuçlar analiz eder."

    def __init__(self, search_service: ITicketSearchService, max_retries=3):
        self.search_service = search_service
        self.max_retries = max_retries
        self.retry_count = 0
        self.is_running = True

    def check_and_process(self, search_params: dict) -> dict:
        """
        Bilet arama ve sonuçları analiz etme işlemlerini yapar.
        """

        if not self.is_running:
            return {"status": ControlStatus.STOPPED, "message": "Kontrol işlemi durduruldu."}
        
        try:
            raw_message = self.search_service.search_and_get_raw_results(search_params)

            if raw_message.startswith("Hata"):
                # tarayıcı veya selenium hatası
                return self._handle_error(raw_message)
            
            if "Engelli" in raw_message or "(0 )" in raw_message or "Uygun sefer bulunamadı." in raw_message:
                self.retry_count = 0 # Başarılı bir kontrol, hata değil
                return {"status": ControlStatus.NOT_FOUND, "message": "Uygun koltuk bulunamadı."}
            
        except Exception as e:
            return self._handle_error(f"Hata: {str(e)}")  

    def _handle_error(self, error_message: str) -> dict:
        """Hata durumunda tekrar deneme mantığını yönetir (SRP: Hata Yönetimi)."""
        self.retry_count += 1
        if self.retry_count <= self.max_retries:
            return {
                "status": ControlStatus.RETRY, 
                "message": f"Tekrar denenecek: {self.retry_count}/{self.max_retries}. Detay: {error_message}"
            }
        else:
            return {
                "status": ControlStatus.FATAL_ERROR, 
                "message": f"Tekrar deneme limiti aşıldı. Detay: {error_message}"
            }