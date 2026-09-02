import os
import json
import logging
import sys
import threading
import time
from src.sap_automation.screens.zmm0170_handler import ZMM0170Handler
from src.sap_automation.sap_connection import get_sap_session
from src.util.localizer import _

# Proje kök dizinini Python yoluna ekleme
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

try:
    from main import start_automation_process
except ImportError as e:
    logging.error(f"main.py bulunamadı veya import edilemedi: {e}")

from src.util.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class AutomationBridge:
    def __init__(self, dashboard_page=None):
        # Dashboard referansını saklıyoruz (GUI güncellemeleri için)
        self.dashboard = dashboard_page


   
    def execute_workflow(self, po_no, is_template_mode):
        try:
            # 1. UI TEMİZLİĞİ
            self.dashboard.after(0, lambda: self.dashboard.wf_title.configure(text=_("FETCHING_DATA")))
            self.dashboard.after(0, lambda: [w.destroy() for w in self.dashboard.steps_container.winfo_children()])

            # 2. PARALEL İZLEYİCİYİ BAŞLAT (Kritik Nokta!)
            # Bu thread, start_automation_process'in bitmesini beklemez. 
            # Dosya diske düştüğü an GUI'yi günceller.
            watcher_thread = threading.Thread(
                target=self._wait_for_json_and_draw, 
                args=(po_no,), 
                daemon=True
            )
            watcher_thread.start()

            # 3. ANA İŞLEMİ BAŞLAT
            logger.info(_("STARTING_AUTOMATION", po_no=po_no))
            start_automation_process(po_no, is_template_mode)
            
            # Fonksiyon burada takılsa bile, yukarıdaki watcher_thread işini çoktan bitirmiş olacak.
            return True

        except Exception as e:
            logger.error(_("BRIDGE_ERROR", error=str(e)))
            return False

    def _wait_for_json_and_draw(self, po_no):
        """Arka planda JSON dosyasını bekler ve gelince GUI'yi tetikler."""
        json_path = os.path.join(ConfigManager.JSON_DIR, f"order_data_cache_{po_no}.json")
        
        timeout = 60  # Maksimum 60 saniye bekle
        start_time = time.time()
        
        logger.info(_("JSON_WATCHER_WAIT", path=json_path))
        
        while time.time() - start_time < timeout:
            if os.path.exists(json_path):
                # Dosya bulundu! Türü tespit et.
                time.sleep(1) # Dosya yazımının tamamlanması için kısa bir es
                order_type = self.detect_order_type(po_no)
                order_name = self.check_cache_and_get_orderName(po_no)
                
                logger.info(_("JSON_WATCHER_FOUND", order_type=order_type))
                
                # GUI'yi tetikle
                self.dashboard.after(0, lambda: self.dashboard.draw_workflow_steps(order_type, po_no, order_name))
                return # İşimiz bitti, thread'den çık.
            
            time.sleep(2) # 2 saniyede bir kontrol et
            
        logger.warning(_("JSON_WATCHER_TIMEOUT", po_no=po_no))

    def detect_order_type(self, po_no):
        """
        json_output klasöründeki liste yapısındaki dosyayı okuyup 
        SET mi SINGLE mı olduğunu belirler.
        """
        try:
            # Dosya adını senin formatına göre güncelledim
            json_path = os.path.join(ConfigManager.JSON_DIR, f"order_data_cache_{po_no}.json")
            
            if not os.path.exists(json_path):
                logger.warning(_("JSON_NOT_FOUND_DEFAULT", path=json_path))
                return "SINGLE"

            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Paylaştığın JSON bir liste olduğu için: [ {...} ]
                # Listenin boş olmadığını ve bir liste olduğunu kontrol ediyoruz
                if isinstance(data, list) and len(data) > 0:
                    first_item = data[0] # Listenin ilk elemanını al
                    
                    # orderType değerini al ve küçük harfe çevirerek kontrol et
                    order_type_val = str(first_item.get('orderType', '')).lower()
                    
                    if order_type_val == "set":
                        logger.info(_("PO_SET_DETECTED", po_no=po_no))
                        return "SET"
                    
                    # Alternatif kontrol: childrens listesi dolu mu?
                    if first_item.get('childrens') and len(first_item['childrens']) > 0:
                        logger.info(_("PO_CHILD_COMPONENTS_FOUND", po_no=po_no))
                        return "SET"

            return "SINGLE"
        except Exception as e:
            logger.error(_("PO_DETECT_ERROR", error=str(e)))
            return "SINGLE"

    def execute_modular_workflow(self, po_no, selected_steps):
        """
        GUI'den gelen seçili adımları (selected_steps) alır ve 
        main.py üzerinden modüler robot sürecini yönetir.
        """
        from src.util.automation_state import AutomationState
        try:
            logger.info(_("MODULAR_FLOW_START"))
            logger.info(_("TARGET_PO_LOG", po_no=po_no))
            logger.info(_("LOG_SELECTED_STEPS", steps=selected_steps))

            # 1. Circular Import'u önlemek için yerel import yapıyoruz
            from main import start_modular_process
            
            # 2. Modüler Motoru Çalıştır (Sıralama kontrolü main ve workflow katmanında yapılır)
            success = start_modular_process(po_no, selected_steps, self)

            # 3. Sonuca göre loglama yap
            if success:
                logger.info(_("MODULAR_FLOW_SUCCESS", po_no=po_no))
            else:
                logger.error(_("MODULAR_FLOW_FAILED", po_no=po_no))

            return success

        except Exception as e:
            logger.error(_("MODULAR_BRIDGE_ERROR", error=str(e)), exc_info=True)
            return False

        finally:
            # İşlem bittiğinde (DURDURULMADIYSA) ID'yi temizle
            AutomationState.current_thread_id = None
            # 4. İŞLEM BİTTİĞİNDE BUTONLARI TEKRAR AKTİF ET (Kritik!)
            # Robot başarılı olsa da hata alsa da kullanıcıya kontrolü geri vermeliyiz.
            # DashboardPage üzerindeki butonları ana thread'de (after) güncelliyoruz.
            self.dashboard.after(0, lambda: self.dashboard.btn_run_selected.configure(
                state="normal", 
                text=_("START_SELECTED_STEPS")
            ))
            self.dashboard.after(0, lambda: self.dashboard.btn_template.configure(state="normal"))
            
            # Sistem durum göstergesini de güncelleyebiliriz
            self.dashboard.after(0, lambda: self.dashboard.status_indicator.configure(
                text=_("SYSTEM_READY"), 
                text_color="#14a44d"
            ))
    def check_cache_and_get_type(self, po_no):
        """
        Belirtilen PO için yerel JSON olup olmadığını kontrol eder.
        Varsa türünü döner, yoksa None döner.
        """
        json_path = os.path.join(ConfigManager.JSON_DIR, f"order_data_cache_{po_no}.json")

        if os.path.exists(json_path):
            # Dosya varsa türünü tespit et ve dön
            return self.detect_order_type(po_no)

        return None
    
    
    def check_cache_and_get_orderName(self, po_no):
        """
        Belirtilen PO için yerel JSON olup olmadığını kontrol eder.
        Varsa sipariş adını döner, yoksa None döner.
        """
        json_path = os.path.join(ConfigManager.JSON_DIR, f"order_data_cache_{po_no}.json")

        if os.path.exists(json_path):
            # Dosya varsa sipariş adını döner
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    first_item = data[0] # Listenin ilk elemanını al
                    
                    # orderType değerini al ve küçük harfe çevirerek kontrol et
                    order_type_val = str(first_item.get('styleName', '')).lower()
                return order_type_val

        return None

    def get_full_order_data(self, po_no):
        """JSON içeriğini tamamen döner."""
        json_path = os.path.join(ConfigManager.JSON_DIR, f"order_data_cache_{po_no}.json")
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data[0] if isinstance(data, list) else data
        return None
    

    def update_step_status(self, step_id, status, progress=None):
        """Robotun durumunu GUI'ye iletir."""
        self.dashboard.after(0, lambda: self.dashboard.update_ui_status(step_id, status, progress))
        
    def create_accessory_in_sap(self, data):
        """Kendi sap_connection.py dosyamızı kullanarak SAP otomasyonunu tetikler"""
        # Senin harika fonksiyonunu çağırıyoruz:
        session = get_sap_session() 
        
        if not session:
            return {"status": "error", "message": _("SAP_LOGIN_ERROR_BRIDGE")}
        
        # Ekran yöneticisini (handler) çağır ve işlemi başlat
        handler = ZMM0170Handler()
        return handler.create_accessory(session, data)