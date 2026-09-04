import json
import keyring
import os

APP_NAME = "LCW_Automation_2026"
APP_VERSION = "1.0.2"

class ConfigManager:
    CONFIG_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), APP_NAME)
    CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
    
    # Log ve JSON çıktıları için de yollar tanımlayalım
    LOG_FILE = os.path.join(CONFIG_DIR, 'automation.log')
    JSON_DIR = os.path.join(CONFIG_DIR, 'json_output')
    # Kullanıcının Belgelerim klasörünü bul
    DOCUMENTS_DIR = os.path.join(os.path.expanduser("~"), "Documents")
    # Belgelerim içinde özel bir klasör adı
    OUTPUT_EXCEL_DIR = os.path.join(DOCUMENTS_DIR, "LCW_Automation_Outputs")

    DEFAULTS = {
        # --- UYGULAMA VE GÜNCELLEME AYARLARI ---
        "APP_VERSION": APP_VERSION,
        "UPDATE_CHECK_URL": "https://gist.githubusercontent.com/AlptugKizilay/f7112cf3433f3466dfb28e90cd8cf81a/raw/version.json",
        "AUTO_UPDATE_ENABLED": True,

        # --- LCW TEDARİKÇİ PORTALI AYARLARI ---
        "LCW_LOGIN_URL": "https://supplierportal.lcwaikiki.com/home",
        "LCW_TOKEN_API_ENDPOINT_PART": "/sts/issue/oidc/",
        "LCW_USERNAME_SELECTOR": "#username",
        "LCW_PASSWORD_SELECTOR": "#password",
        "LCW_LOGIN_BUTTON_SELECTOR": "#kc-login",

        # --- XIR SİSTEM AYARLARI ---
        "XIR_URL": "https://tr.xir.lcwaikiki.com/",

        # --- SAP GUI BAĞLANTI AYARLARI ---
        "SAP_LOGON_PATH": r"C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe",
        "SAP_SYSTEM_NAME": "S4P Canlı Sistem",
        #"SAP_SYSTEM_NAME": "S4Q RISE TEST",
        "SAP_CLIENT": "100",
        "SAP_LANGUAGE": "TR",

        # --- ARKA PLAN / UYGULAMA AYARLARI ---
        "APP_LANGUAGE": "TR",

        # --- FIORI AYARLARI ---
        "FIORI_URL": "https://hecfioriprd.tahagiyim.com/sap/bc/ui2/flp?sap-client=100&sap-language=TR#Action-SD001"
    }
    @staticmethod
    def ensure_dirs():
        """Gerekli klasörlerin (AppData içinde) var olduğundan emin olur."""
        if not os.path.exists(ConfigManager.CONFIG_DIR):
            os.makedirs(ConfigManager.CONFIG_DIR)
        if not os.path.exists(ConfigManager.JSON_DIR):
            os.makedirs(ConfigManager.JSON_DIR)
        if not os.path.exists(ConfigManager.OUTPUT_EXCEL_DIR):
            os.makedirs(ConfigManager.OUTPUT_EXCEL_DIR)

    @staticmethod
    def save_setting(key, value):
        """Ayarı kaydederken dosyayı güvenli bir şekilde okur ve yazar."""
        ConfigManager.ensure_dirs()
        config = {}
        file_path = "config.json"
        
        # ARTIK CONFIG_FILE KULLANIYORUZ
        if os.path.exists(ConfigManager.CONFIG_FILE):
            try:
                with open(ConfigManager.CONFIG_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        config = json.loads(content)
            except Exception:
                config = {}
        
        config[key] = value
        with open(ConfigManager.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        


    @staticmethod
    def get_setting(key):
        """Ayarı okurken dosya hatalarını tolere eder."""
        
        if os.path.exists(ConfigManager.CONFIG_FILE):
            try:
                with open(ConfigManager.CONFIG_FILE, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        config = json.loads(content)
                        return config.get(key, ConfigManager.DEFAULTS.get(key, ""))
            except Exception:
                pass
        
        return ConfigManager.DEFAULTS.get(key, "")

    @staticmethod
    def save_password(service, password):
        try:
            keyring.set_password(APP_NAME, service, password)
        except:
            pass

    @staticmethod
    def get_password(service):
        try:
            return keyring.get_password(APP_NAME, service) or ""
        except:
            return ""