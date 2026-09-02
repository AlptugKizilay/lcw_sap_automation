
import time
import logging
from src.util.localizer import _

logger = logging.getLogger(__name__)

def handle_sap_popups(session):
    """
    Sadece ana ekranı kilitleyen modal pop-up'ları (wnd[1]) kapatır.
    Gerçek pencerelere veya F4 arama ekranlarına dokunmaz.
    """
    try:
        logger.info(_("LOG_POPUP_CHECKING"))
        time.sleep(1) # Pop-up'ın gelmesi için kısa bir bekleme
        if session.Children.Count > 1:
            popup_window = session.findById("wnd[1]")
            
            logger.info(f"ZMM0020: Pop-up uyarısı algılandı: '{popup_window.Text}'. Kapatılıyor.")
            popup_window.findById("tbar[0]/btn[0]").press() # İlk butona bas (Genellikle "Devam" veya "OK")
            time.sleep(0.5)
            
            # İkinci bir pop-up gelme ihtimaline karşı tekrar kontrol
            if session.Children.Count > 1:
                popup_window_2 = session.findById("wnd[1]")
                logger.warning(f"ZMM0020: İkinci pop-up uyarısı algılandı: '{popup_window_2.Text}'. Kapatılıyor.")
                popup_window_2.findById("tbar[0]/btn[0]").press() # İkinci butona bas
                time.sleep(1)
        else:
            logger.info(_("LOG_POPUP_NOT_FOUND"))
    except Exception as e_popup:
        logger.debug(f"ZMM0020: Pop-up kontrolü sırasında hata oluştu veya pop-up gelmedi (normal olabilir): {e_popup}")
        pass # Pop-up yoksa veya beklenenden farklıysa hata vermeden devam et