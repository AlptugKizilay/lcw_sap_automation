# src/data_sources/order_options_api.py

import requests
import json
from src.data_sources.product_info_api import get_common_headers 
from src.auth.auth_manager_playwright import get_token_sync

def get_order_options_data(order_no, token):
    """
    XIR API'den OrderOptions bilgilerini çeker ve OptionId'leri döndürür.
    """
    full_url = f"https://xir.prod.lcwaikiki.com/xir/request/service/api/Order/GetOrderOptions?OrderNo={order_no}"
    
    print(f"\nXIR API'den OrderOptions sorgusu yapılıyor... URL: {full_url}, OrderNo: {order_no}")

    current_token = token
    for attempt in range(2):
        try:
            headers = get_common_headers(current_token)
            response = requests.get(full_url, headers=headers)
            
            if response.status_code == 401 and attempt == 0:
                print("HTTP 401 (getOrderOptions): Token geçersiz/süresi dolmuş! Token yenilenip tekrar deneniyor...")
                current_token = get_token_sync(force_refresh=True)
                if not current_token:
                    print("Hata: Yeni token alınamadı.")
                    return None
                continue

            response.raise_for_status()
            
            response_json = response.json()
            
            option_ids = []
            if 'Options' in response_json and isinstance(response_json['Options'], list):
                for option_item in response_json['Options']:
                    if 'OptionId' in option_item:
                        option_ids.append(option_item['OptionId'])
            
            return option_ids

        except requests.exceptions.HTTPError as err:
            if err.response is not None and err.response.status_code == 401 and attempt == 0:
                print("HTTP 401 (getOrderOptions): Token yenilenip tekrar deneniyor...")
                current_token = get_token_sync(force_refresh=True)
                if not current_token:
                    return None
                continue
            print(f"HTTP Hatası (getOrderOptions): {err}")
            return None
        except requests.exceptions.RequestException as err:
            print(f"İstek Hatası (getOrderOptions): {err}")
            return None
        except json.JSONDecodeError:
            print("getOrderOptions yanıtı JSON formatında değil.")
            return None
        except Exception as err:
            print(f"Beklenmedik bir hata oluştu (getOrderOptions): {err}")
            return None

    return None

if __name__ == "__main__":
    print("--- XIR OrderOptions API Testi ---")
    
    try:
        # Ana projenin yapısına uygun importlar
        from src.auth.auth_manager_playwright import get_token_sync
        test_token = get_token_sync()
        if test_token:
            test_order_no = 1259111 # Ekran görüntüsündeki örnek OrderNo
            
            options = get_order_options_data(test_order_no, test_token)
            if options:
                print(f"OrderNo {test_order_no} için bulunan OptionId'ler: {options}")
            else:
                print(f"OrderNo {test_order_no} için OptionId bulunamadı.")
        else:
            print("Token alınamadı, test yapılamadı.")
    except ModuleNotFoundError as e:
        print(f"Hata: Test için gerekli modüller bulunamadı: {e}")
        print("Lütfen dosyayı projenin ana dizininden 'python -m src.data_sources.order_options_api' komutuyla çalıştırın veya")
        print("test bloğundaki import'ları ve token alma mantığını kontrol edin.")
    except Exception as e:
        print(f"Test sırasında beklenmedik bir hata oluştu: {e}")
