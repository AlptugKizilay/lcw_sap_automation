# src/sap_automation/sap_connection.py

import win32com.client
import pythoncom 
import os
import time
import logging
from dotenv import load_dotenv
from src.util.config_manager import ConfigManager

# Yapılandırmayı yükle
load_dotenv()
logger = logging.getLogger(__name__)
cfg = ConfigManager()
def get_sap_session():
    """
    SAP GUI'ye bağlanır ve aktif bir session (oturum) döndürür.
    Ön Koşul: SAP Logon Pad açık olmalı ve hedef sisteme bağlantı kurulmuş olmalı.
    """
    
    # .env / config_manager dosyasından gerekli bilgileri al
    system_name = cfg.get_setting("SAP_SYSTEM_NAME") or os.getenv("SAP_SYSTEM_NAME")
    username = cfg.get_setting("SAP_USERNAME") or os.getenv("SAP_USERNAME")
    password = cfg.get_password("SAP_PASS") or os.getenv("SAP_PASSWORD")
    
    from src.util.localizer import get_language, _
    app_lang = get_language().upper() # "TR" veya "EN"
    target_sap_langu = "EN" if app_lang == "EN" else "TR"

    try:
        pythoncom.CoInitialize() # COM ortamını hazırlar
        
        try:
            sap_gui_auto = win32com.client.GetObject("SAPGUI")
        except Exception:
            sap_gui_auto = win32com.client.Dispatch("Sapgui.ScriptingCtrl.1")

        application = sap_gui_auto.GetScriptingEngine
        
        # 2. Açık olan bağlantılar arasında hedef sistemi ara
        connection = None
        for conn in application.Children:
            if conn.Description == system_name:
                connection = conn
                break
        
        if connection is None:
            logger.error(f"HATA: '{system_name}' adlı aktif bir SAP bağlantısı bulunamadı.")
            logger.info("Lütfen SAP Logon Pad'den sistemi manuel olarak açın.")
            return None
            
        # 3. Bağlantıdaki ilk oturumu (session) al
        session = connection.Children(0)
        logger.info(f"'{system_name}' sistemine başarıyla bağlanıldı. İşlem Kodu: '{session.info.transaction}'")

        # 4. Login Kontrolü: Eğer login ekranındaysak (S000) uygulama diline uygun giriş yap
        if session.info.transaction == "S000":
            logger.info(f"SAP Login ekranı algılandı. Uygulama dili '{app_lang}' uyarınca SAP dili '{target_sap_langu}' ile '{username}' girişi yapılıyor...")
            
            session.findById("wnd[0]").maximize()
            session.findById("wnd[0]/usr/txtRSYST-BNAME").text = username
            session.findById("wnd[0]/usr/pwdRSYST-BCODE").text = password
            session.findById("wnd[0]/usr/txtRSYST-LANGU").text = target_sap_langu
            session.findById("wnd[0]").sendVKey(0) # Enter
            
            time.sleep(2) # Girişin tamamlanması için bekle

        else:
            # 5. Açık Oturum Dil Kontrolü: Uygulama dili ile SAP oturum dili aynı mı?
            raw_sap_lang = str(session.info.Language).strip().upper()
            
            # SAP dili eşleştirmesi: TR/T -> TR, EN/E -> EN
            if raw_sap_lang in ["TR", "T"]:
                current_sap_lang = "TR"
            elif raw_sap_lang in ["EN", "E"]:
                current_sap_lang = "EN"
            else:
                current_sap_lang = raw_sap_lang

            logger.info(f"Aktif SAP Oturum Dili: '{raw_sap_lang}' ({current_sap_lang}), Uygulama Dili: '{app_lang}'")
            
            if current_sap_lang != app_lang:
                msg = _("SAP_LANG_MISMATCH", app_lang=app_lang, sap_lang=current_sap_lang)
                logger.error(msg)
                raise Exception(msg)

        logger.info("SAP oturumu kullanıma hazır.")
        return session

    except Exception as e:
        logger.error(f"SAP bağlantısı / dil kontrolü sırasında hata: {e}")
        return None

if __name__ == "__main__":
    # Test Bloğu
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger.info("Sıfırdan SAP bağlantı testi başlatılıyor...")
    
    test_session = get_sap_session()
    
    if test_session:
        print(f"BAŞARILI: Şu an '{test_session.info.SystemName}' sistemindesiniz.")
        # Test amaçlı küçük bir hareket: Komut alanına odaklan

        logger.info("Bağlantı doğrulandı, komut alanına odaklanıldı.")
    else:
        print("BAŞARISIZ: Bağlantı kurulamadı. Lütfen SAP Logon'un açık olduğundan emin olun.")