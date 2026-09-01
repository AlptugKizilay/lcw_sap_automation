# src/data_sources/product_info_api.py

import requests
import json
from src.auth.auth_manager_playwright import get_token_sync

# get_common_headers fonksiyonuna 'token' parametresini ekledik
def get_common_headers(token):
    if not token:
        raise Exception("Kimlik doğrulama token'ı sağlanmadı.")

    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
        "Authorization": f"Bearer {token}",
    }

def get_product_list_from_order_code(order_code, published_label_id, country_id, product_search_type, token):
    base_url = "https://mym-api.lcwaikiki.com/lcw/live/globallabel/service/api/"
    get_code_order_list_url = f"{base_url}ProductLabelPrint/GetCodeOrderList"
    
    params = {
        "code": order_code,
        "PublishedLabelID": published_label_id,
        "CountryID": country_id,
        "ProductSearchType": product_search_type
    }

    print(f"1. Adım: GetCodeOrderList sorgusu yapılıyor... URL: {get_code_order_list_url}, Parametreler: {params}")
    
    current_token = token
    for attempt in range(2):
        try:
            headers = get_common_headers(current_token)
            response = requests.get(get_code_order_list_url, headers=headers, params=params)
            
            if response.status_code == 401 and attempt == 0:
                print("HTTP 401 (GetCodeOrderList): Token geçersiz/süresi dolmuş! Token yenilenip tekrar deneniyor...")
                current_token = get_token_sync(force_refresh=True)
                if not current_token:
                    print("Hata: Yeni token alınamadı.")
                    return None
                continue

            response.raise_for_status() 
            response_json = response.json()
            
            if isinstance(response_json, list):
                return response_json
            elif isinstance(response_json, dict) and 'data' in response_json and isinstance(response_json['data'], list):
                return response_json['data']
            else:
                print("Uyarı: GetCodeOrderList yanıt yapısı beklenenden farklı. Yanıt:", json.dumps(response_json, indent=2, ensure_ascii=False))
                return []

        except requests.exceptions.HTTPError as err:
            if err.response is not None and err.response.status_code == 401 and attempt == 0:
                print("HTTP 401 (GetCodeOrderList): Token yenilenip tekrar deneniyor...")
                current_token = get_token_sync(force_refresh=True)
                if not current_token:
                    return None
                continue
            print(f"HTTP Hatası (GetCodeOrderList): {err}")
            return None
        except requests.exceptions.RequestException as err:
            print(f"İstek Hatası (GetCodeOrderList): {err}")
            return None
        except json.JSONDecodeError:
            print("GetCodeOrderList yanıtı JSON formatında değil.")
            return None
        except Exception as err:
            print(f"Beklenmedik bir hata oluştu (GetCodeOrderList): {err}")
            return None

    return None

def get_product_information_and_beden(dynamic_product_list, order_code, country_id, published_label_id, token):
    base_url = "https://mym-api.lcwaikiki.com/lcw/live/globallabel/service/api/"
    get_product_info_url = f"{base_url}WebDataServices/GetProductInformation"
    
    payload = {
        "CountryID": country_id,
        "PublishedLabelID": published_label_id,
        "Code": str(order_code),
        "ProductList": dynamic_product_list, 
        "IsMixed": False,
        "CurrentCountryID": "48",
        "CompanyID": None,
        "ProductSearchType": 0
    }

    print(f"\n2. Adım: GetProductInformation sorgusu yapılıyor... URL: {get_product_info_url}")

    current_token = token
    for attempt in range(2):
        try:
            headers_for_post = get_common_headers(current_token)
            headers_for_post["Content-Type"] = "application/json; charset=utf-8"

            response = requests.post(get_product_info_url, headers=headers_for_post, json=payload)
            
            if response.status_code == 401 and attempt == 0:
                print("HTTP 401 (GetProductInformation): Token geçersiz/süresi dolmuş! Token yenilenip tekrar deneniyor...")
                current_token = get_token_sync(force_refresh=True)
                if not current_token:
                    print("Hata: Yeni token alınamadı.")
                    return None
                continue

            response.raise_for_status() 
            response_json = response.json()

            all_beden_info = []
            if 'data' in response_json and isinstance(response_json['data'], list):
                for product_data_item in response_json['data']:
                    current_identifier = product_data_item.get('orderCode') or product_data_item.get('barcode') or product_data_item.get('Code') or 'N/A'
                    
                    if 'productInformationList' in product_data_item and isinstance(product_data_item['productInformationList'], list):
                        for info_item in product_data_item['productInformationList']:
                            if info_item.get('fieldName') == 'Beden':
                                all_beden_info.append({
                                    "type": info_item.get('fieldName'),
                                    "value": info_item.get('value'),
                                    "identifier": current_identifier
                                })
            return all_beden_info

        except requests.exceptions.HTTPError as err:
            if err.response is not None and err.response.status_code == 401 and attempt == 0:
                print("HTTP 401 (GetProductInformation): Token yenilenip tekrar deneniyor...")
                current_token = get_token_sync(force_refresh=True)
                if not current_token:
                    return None
                continue
            print(f"HTTP Hatası (GetProductInformation): {err}")
            return None
        except requests.exceptions.RequestException as err:
            print(f"İstek Hatası (GetProductInformation): {err}")
            return None
        except json.JSONDecodeError:
            print("GetProductInformation yanıtı JSON formatında değil.")
            return None
        except Exception as err:
            print(f"Beklenmedik bir hata oluştu (GetProductInformation): {err}")
            return None

    return None

if __name__ == "__main__":
    print("Bu dosya doğrudan çalıştırıldığında token parametresi eksik olacaktır.")
    print("Test etmek için get_common_headers() içindeki get_token_sync() çağrısını geçici olarak geri almalısınız.")
    # Veya test için burada manuel bir token değeri sağlayabilirsiniz
    # TEST_TOKEN = "YOUR_MANUAL_TOKEN_HERE"
    # product_list_for_payload = get_product_list_from_order_code(ORDER_CODE, PUBLISHED_LABEL_ID, COUNTRY_ID, PRODUCT_SEARCH_TYPE, TEST_TOKEN)
    # ...