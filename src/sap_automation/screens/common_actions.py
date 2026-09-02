

import time
import logging
from src.util.handle_sap_popups import handle_sap_popups
from src.util.localizer import _
logger = logging.getLogger(__name__)


def save_sap_screen(session, timeout_seconds=10):
    """
    SAP ekranında kaydetme işlemini yapar ve işlemin tamamlanmasını bekler.
    Durum çubuğundaki mesajı kontrol eder.
    """
    try:
        logger.info(_("LOG_SAP_SAVE_START"))
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
                    logger.info(_("LOG_SAP_SAVE_SUCCESS", msg=status_info['text']))
                    handle_sap_popups(session)
                    return True
                elif status_info["type"] == "E":
                    logger.error(_("LOG_SAP_SAVE_FAILED", msg=status_info['text']))
                    return False
            
            # Eğer belirli bir süre boyunca hiçbir 'S' veya 'E' mesajı gelmezse,
            # veya mesaj değişmezse beklemeye devam et.
            time.sleep(1) # Her saniye durumu kontrol et

        logger.error(_("LOG_SAP_SAVE_TIMEOUT", timeout=timeout_seconds))
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
            logger.info(_("LOG_SAP_STATUS_BAR", msg_type=message_type, text=message_text))
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
        logger.info(_("LOG_SAP_MODE", mode=current_mode))

        if current_mode == "CHANGE":
            logger.info(_("LOG_SAP_MODE_ALREADY_CHANGE"))
            return True
        elif current_mode == "DISPLAY":
            logger.info(_("LOG_SAP_SWITCHING_CHANGE"))
            session.findById(change_button_id).press()
            time.sleep(1) # Mod değişimi için kısa bir bekleme

            start_time = time.time()
            while time.time() - start_time < timeout_seconds:
                new_mode = get_current_sap_mode(session)
                if new_mode == "CHANGE":
                    logger.info(_("LOG_SAP_SWITCHED_CHANGE"))
                    return True
                time.sleep(0.5) # Yarım saniyede bir kontrol et

            logger.error(f"SAP Ekranı {timeout_seconds} saniye içinde 'Değiştir' moduna geçemedi.")
            return False
        elif current_mode == "UNKNOWN":
            logger.warning("SAP Ekran modunu belirleyemedi, 'Değiştir' moduna geçiş denemesi atlanıyor.")
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
        if session.Children.Count > 1 and session.Children(1).Type == "GuiModalWindow":
            popup_wnd = session.findById("wnd[1]")
            popup_wnd.findById("tbar[0]/btn[0]").press() # Note: ID is relative to wnd[1]
            logger.info(_("LOG_SAP_POPUP_OK"))
            time.sleep(1)
            return True
        return False
    except Exception as e:
        logger.debug(f"No generic SAP pop-up (wnd[1]/tbar[0]/btn[0]) found or could not interact: {e}")
        return False
    