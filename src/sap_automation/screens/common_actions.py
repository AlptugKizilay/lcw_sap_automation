

import time
import logging
from src.util.handle_sap_popups import handle_sap_popups
logger = logging.getLogger(__name__)


def save_sap_screen(session, timeout_seconds=10):
    """
    SAP ekranında kaydetme işlemini yapar ve işlemin tamamlanmasını bekler.
    Durum çubuğundaki mesajı kontrol eder.
    """
    try:
        logger.info("SAP Ekranı: Kaydetme işlemi başlatılıyor (btn[11]).")
        session.findById("wnd[0]/tbar[0]/btn[11]").press()
        handle_sap_popups(session)
        
        start_time = time.time()
        last_message_text = "" # Mesajın değişip değişmediğini kontrol etmek için
        
        while time.time() - start_time < timeout_seconds:
            handle_sap_popups(session)
            status_info = read_sap_status_bar(session)
            
            # Mesaj değiştiyse veya yeni bir mesaj geldiyse kontrol et
            if status_info["text"] and status_info["text"] != last_message_text:
                last_message_text = status_info["text"]
                
                # Başarı mesajı ('S') veya kesin hata mesajı ('E') kontrolü
                if status_info["type"] == "S":
                    logger.info(f"SAP Ekranı: Kaydetme işlemi başarıyla tamamlandı. Mesaj: {status_info['text']}")
                    handle_sap_popups(session)
                    return True
                elif status_info["type"] == "E":
                    logger.error(f"SAP Ekranı: Kaydetme işlemi başarısız oldu. Hata Mesajı: {status_info['text']}")
                    return False
            
            # Eğer belirli bir süre boyunca hiçbir 'S' veya 'E' mesajı gelmezse,
            # veya mesaj değişmezse beklemeye devam et.
            time.sleep(1) # Her saniye durumu kontrol et

        logger.error(f"SAP Ekranı: Kaydetme işlemi {timeout_seconds} saniye içinde tamamlanmadı veya başarı mesajı alınamadı.")
        return True

    except Exception as e:
        logger.exception(f"SAP ekranı kaydetme fonksiyonunda kritik hata: {e}")
        return False

def read_sap_status_bar(session):
    """
    SAP ana penceresinin (wnd[0]) durum çubuğundaki mesajı okur ve döndürür.
    """
    try:
        status_bar = session.findById("wnd[0]/sbar")
        message_type = status_bar.MessageType # 'S' (Success), 'E' (Error), 'W' (Warning), 'I' (Information)
        message_text = status_bar.Text
        if message_text: # Boş mesajları loglamamak için
            logger.info(f"SAP Durum Çubuğu Mesajı: [{message_type}] {message_text}")
        return {"type": message_type, "text": message_text}
    except Exception as e:
        logger.warning(f"SAP durum çubuğu okunurken hata oluştu: {e}")
        return {"type": "E", "text": "Durum çubuğu okunamadı."} # Hata durumunda varsayılan hata mesajı
    
def get_current_sap_mode(session):
    """
    SAP ana ekranının başlığını okuyarak mevcut modu (Görüntüle/Değiştir) belirler.
    Dönüş değeri: "DISPLAY", "CHANGE", veya "UNKNOWN"
    """
    try:
        window_title = session.findById("wnd[0]").text
        window_title_lower = window_title.lower()
        if "görüntüleme" in window_title_lower or "display" in window_title_lower:
            return "DISPLAY"
        elif "güncelleme" in window_title_lower or "update" in window_title_lower or "change" in window_title_lower:
            return "CHANGE"
        else:
            logger.warning(f"SAP ekran modu belirlenemedi. Başlık: '{window_title}'")
            return "UNKNOWN"
    except Exception as e:
        logger.error(f"SAP ekran modu okunurken hata oluştu: {e}")
        return "UNKNOWN"

def ensure_change_mode(session, change_button_id="wnd[0]/tbar[1]/btn[14]", timeout_seconds=10):
    """
    SAP ekranının "Değiştir" modunda olduğundan emin olur.
    Eğer "Görüntüle" modundaysa, belirtilen "Görüntüle/Değiştir" butonuna basarak modu değiştirir.
    """
    try:
        current_mode = get_current_sap_mode(session)
        logger.info(f"SAP Ekranı: Mevcut mod '{current_mode}'.")

        if current_mode == "CHANGE":
            logger.info("SAP Ekranı zaten 'Değiştir' modunda.")
            return True
        elif current_mode == "DISPLAY":
            logger.info(f"SAP Ekranı 'Görüntüle' modunda. 'Değiştir' moduna geçiliyor.")
            session.findById(change_button_id).press()
            time.sleep(1) # Mod değişimi için kısa bir bekleme

            start_time = time.time()
            while time.time() - start_time < timeout_seconds:
                new_mode = get_current_sap_mode(session)
                if new_mode == "CHANGE":
                    logger.info("SAP Ekranı başarıyla 'Değiştir' moduna geçti.")
                    return True
                time.sleep(0.5) # Yarım saniyede bir kontrol et

            logger.error(f"SAP Ekranı {timeout_seconds} saniye içinde 'Değiştir' moduna geçemedi.")
            return False
        elif current_mode == "UNKNOWN":
            logger.warning("SAP Ekran modunu belirleyemedi, 'Değiştir' moduna geçiş denemesi atlanıyor.")
            # Bilinmeyen bir durumda, hata vermeyip devam etmek veya durmak projenin risk iştahına bağlıdır.
            # Şimdilik False döndürüp hata fırlatabiliriz.
            return False
        
        return False # Diğer durumlar için

    except Exception as e:
        logger.exception(f"SAP ekranını 'Değiştir' moduna geçirme sırasında kritik hata: {e}")
        return False
    
    
def handle_sap_popup_ok(session, timeout: int = 5) -> bool:
    """
    Checks for a generic SAP GUI pop-up (wnd[1]) and presses the 'OK' button (btn[0]).
    Returns True if pop-up was handled, False otherwise.
    """
    try:
        # Check if wnd[1] exists and is a modal window
        # The session.Children.Count check is a quick way to see if a wnd[1] might exist
        if session.Children.Count > 1 and session.Children(1).Type == "GuiModalWindow":
            popup_wnd = session.findById("wnd[1]")
            # Attempt to find the 'OK' button and press it
            # Using findById on the popup_wnd for its own elements
            popup_wnd.findById("tbar[0]/btn[0]").press() # Note: ID is relative to wnd[1]
            logger.info("Generic SAP pop-up 'OK' button pressed.")
            time.sleep(1) # Give SAP time to process the pop-up close
            return True
        return False # No modal window found at wnd[1]
    except Exception as e:
        logger.debug(f"No generic SAP pop-up (wnd[1]/tbar[0]/btn[0]) found or could not interact: {e}")
        return False
    