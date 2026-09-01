
from venv import logger

import time
def handle_sap_popups(session):
    """
    Sadece ana ekranı kilitleyen modal pop-up'ları (wnd[1]) kapatır.
    Gerçek pencerelere veya F4 arama ekranlarına dokunmaz.
    """
    try:
        # session.Children.Count > 1 demek, ana pencere (wnd[0]) dışında bir pencere (wnd[1]) var demektir.
        logger.info("Pop-up kontrolü yapılıyor...")
        time.sleep(1) # Pop-up'ın gelmesi için kısa bir bekleme
        if session.Children.Count > 1:
            popup_window = session.findById("wnd[1]")
            # Pop-up'ın başlığını veya ID'sini kontrol ederek spesifik bir pop-up olduğunu doğrulayabiliriz
            # Örneğin: if "Uyarı" in popup_window.Text:
            
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
            logger.info("ZMM0020: Pop-up bulunamadı, normal akışa devam ediliyor.")
    except Exception as e_popup:
        logger.debug(f"ZMM0020: Pop-up kontrolü sırasında hata oluştu veya pop-up gelmedi (normal olabilir): {e_popup}")
        pass # Pop-up yoksa veya beklenenden farklıysa hata vermeden devam et