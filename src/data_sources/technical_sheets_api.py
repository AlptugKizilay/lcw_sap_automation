# src/data_sources/technical_sheets_api.py

import requests
import json
from src.auth.auth_manager_playwright import get_token_sync

def get_common_headers(token):
    if not token:
        raise Exception("Kimlik doğrulama token'ı sağlanmadı.")

    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
        "Authorization": f"Bearer {token}",
    }

def get_technical_sheets(model_id, token):
    technical_sheets_base_url = "https://shipmentrequestapi.prod.lcwaikiki.com/shipmentrequest/api/OrderProject/getTechnicalSheets/"
    full_url = f"{technical_sheets_base_url}{model_id}"

    print(f"\nTeknik Sayfa Bilgileri için sorgu yapılıyor... URL: {full_url}")

    current_token = token
    for attempt in range(2):
        try:
            headers = get_common_headers(current_token)
            response = requests.get(full_url, headers=headers)
            
            if response.status_code == 401 and attempt == 0:
                print("HTTP 401 (getTechnicalSheets): Token geçersiz/süresi dolmuş! Token yenilenip tekrar deneniyor...")
                current_token = get_token_sync(force_refresh=True)
                if not current_token:
                    print("Hata: Yeni token alınamadı.")
                    return None
                continue

            response.raise_for_status() 
            
            technical_sheets_data = response.json()
            return technical_sheets_data

        except requests.exceptions.HTTPError as err:
            if err.response is not None and err.response.status_code == 401 and attempt == 0:
                print("HTTP 401 (getTechnicalSheets): Token yenilenip tekrar deneniyor...")
                current_token = get_token_sync(force_refresh=True)
                if not current_token:
                    return None
                continue
            print(f"HTTP Hatası (getTechnicalSheets): {err}")
            return None
        except requests.exceptions.RequestException as err:
            print(f"İstek Hatası (getTechnicalSheets): {err}")
            return None
        except json.JSONDecodeError:
            print("getTechnicalSheets yanıtı JSON formatında değil.")
            return None
        except Exception as err:
            print(f"Beklenmedik bir hata oluştu (getTechnicalSheets): {err}")
            return None

    return None

if __name__ == "__main__":
    print("Bu dosya doğrudan çalıştırıldığında token parametresi eksik olacaktır.")
    print("Test etmek için get_common_headers() içindeki get_token_sync() çağrısını geçici olarak geri almalısınız.")
    # Veya test için burada manuel bir token değeri sağlayabilirsiniz
    # TEST_TOKEN = "YOUR_MANUAL_TOKEN_HERE"
    # technical_sheets_result = get_technical_sheets(MODEL_ID, TEST_TOKEN)
    # ...