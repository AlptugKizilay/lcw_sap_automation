import requests
import json
import logging

logger = logging.getLogger(__name__)

from src.auth.auth_manager_playwright import get_token_sync

def get_variant_details(po_no, token):
    """
    Çalışan scriptteki mantığı dinamik hale getirdik.
    """
    url = "https://cpsapi.prod.lcwaikiki.com/cps/api/process/SpPreProductionList/"

    if not token:
        logger.error("API Hatası: Token boş geldi!")
        return None

    # PO numarasının liste içinde ve integer olduğundan emin oluyoruz
    try:
        if isinstance(po_no, list):
            po_list = [int(x) for x in po_no if x]
        else:
            po_list = [int(po_no)]
    except Exception as e:
        logger.error(f"PO Numarası dönüştürülemedi: {po_no} - Hata: {e}")
        return None

    # SQL hatası almamak için liste boşsa isteği hiç gönderme
    if not po_list:
        logger.error("API Hatası: OrderNoList boş olamaz!")
        return None

    payload = {
        "processType": "0",
        "FilterRef": 20568,
        "OrderNoList": po_list
    }

    current_token = token
    for attempt in range(2):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Authorization": f"Bearer {current_token}",
            "Origin": "https://supplierportal.lcwaikiki.com",
            "Referer": "https://supplierportal.lcwaikiki.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

        try:
            logger.info(f"API isteği gönderiliyor. PO: {po_list}")
            response = requests.post(url, headers=headers, data=json.dumps(payload))

            if response.status_code == 401 and attempt == 0:
                logger.warning("HTTP 401 (SpPreProductionList): Token geçersiz/süresi dolmuş! Token yenilenip tekrar deneniyor...")
                current_token = get_token_sync(force_refresh=True)
                if not current_token:
                    logger.error("Hata: Yeni token alınamadı.")
                    return None
                continue

            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data:
                    order_info = {
                        "order_no": item.get("orderNumber"),
                        "main_color": item.get("color", {}).get("colorCode", "N/A"),
                        "components": []
                    }
                    
                    for comp in item.get("components", []):
                        if comp.get("componentName") and comp.get("componentColorDesc"):
                            order_info["components"].append({
                                "componentName": comp.get("componentName"),
                                "componentColorDesc": comp.get("componentColorDesc"),
                                "componentCode": comp.get("componentCode"),
                                "picturePath": comp.get("picturePath")
                            })
                    results.append(order_info)
                
                return results
            else:
                logger.error(f"API Hatası! Kod: {response.status_code}, Mesaj: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Sorgu sırasında genel hata: {e}")
            return None

    return None