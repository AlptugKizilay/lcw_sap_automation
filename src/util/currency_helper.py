# src/utils/currency_helper.py

import requests
import logging
from src.util.localizer import _

logger = logging.getLogger(__name__)

def get_usd_to_egp_rate():
    """
    Güncel USD -> EGP kurunu çeker. 
    API hatası durumunda güvenli bir yedek (fallback) değer döner.
    """
    try:
        # Ücretsiz ve hızlı bir döviz kuru API'si
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # EGP kurunu al
        rate = data.get("rates", {}).get("EGP")
        
        if rate:
            logger.info(_("LOG_EXCHANGE_RATE", curr="USD/EGP", rate=rate))
            return float(rate)
        else:
            raise Exception("EGP kuru veride bulunamadı.")
            
    except Exception as e:
        #logger.error(f"Döviz kuru çekilirken hata oluştu: {e}. Yedek kur kullanılıyor.")
        return 48.50 # Hata durumunda kullanılacak yaklaşık sabit kur (Manuel güncellenebilir)