# src/data_sources/order_components_api.py

import requests
import json
import re # Renk kodunu çıkarmak için regex kullanacağız
from src.data_sources.product_info_api import get_common_headers 

def printed_colors_counter(order_no, option_id, token):
    try:
        printed_colors_count = {} 
        response_json = get_option_components_data(order_no, option_id, token)
        if 'OptionComponents' in response_json and isinstance(response_json['OptionComponents'], list):
            for component_item in response_json['OptionComponents']:
                component_group = component_item.get('ComponentGroup').lower()
                component_name = component_item.get('ComponentName', '').lower() # Küçük harfe çevirerek karşılaştır

                # Ekran görüntüsünde ComponentColor direkt bir değer, ancak bazen içinden ayıklamak gerekebilir.
                # Regex ile ayrıştırma işini extract_color_code_from_component_color fonksiyonuna bıraktık.
                component_color_raw = component_item.get('ComponentColor')
                #print(f"İncelenen Component - Group: {component_group}, Name: {component_name}, Raw Color: {component_color_raw}")
                # YENİ BASKI FİLTRELEME MANTIĞI:
                # ComponentGroup "PRINT" olacak
                # VE ComponentName "label" içermeyecek
                # VE ComponentName "allover" içermeyecek
                if "print" in component_name and \
                   "label" not in component_name and \
                   "allover" not in component_name: # <-- Bu kısım güncellendi!
                    extracted_color_code = None

                    if component_color_raw: # Diğer normal renk kodları
                        extracted_color_code = extract_color_code_from_component_color(component_color_raw)
                        print(f"  Normal baskı komponenti. Çıkarılan Renk Kodu: {extracted_color_code}")
                    elif "artwork" in component_color_raw.strip().lower():
                        # Özel durum: "see artwork" ise bunu baskı olarak kabul et
                        extracted_color_code = "SEE_ARTWORK_PRINT"
                        print(f"  'See Artwork' baskı olarak kabul edildi. Özel Kod: {extracted_color_code}")  
                    elif component_color_raw is None or component_color_raw.strip() == "":
                        # Boş veya None ComponentColor için özel durum
                        extracted_color_code = "SEE_ARTWORK_PRINT"
                        print(f"  Baskı komponenti ancak ComponentColor boş. Özel Kod: {extracted_color_code}")                  
                    else:
                        print(f"  Baskı komponenti ancak ComponentColor bilgisi boş veya tanımsız.")

                    if extracted_color_code:
                        # Bu renk veya özel durum kodu için bir baskı komponenti bulduk, sayacı artır
                        printed_colors_count[extracted_color_code] = printed_colors_count.get(extracted_color_code, 0) + 1
            else:
                print(f"Uyarı: GetOptionComponents yanıtı beklenen liste formatında değil.")
            return printed_colors_count
    except Exception as err:
        print(f"Beklenmedik bir hata oluştu (GetOptionComponents): {err}")
    return None

def extract_color_code_from_component_color(component_color_str):
    """
    "1. Varyant (LRA-ECRU PRINTED)", "LE4-AÇIK BEJ ÇİZGİLİ:-SEE ARTWORK" veya
    "2. Varyant (R9J-ECRU)" gibi string'lerden
    "LRA", "LE4" veya "R9J" gibi 2-4 haneli renk kodunu çıkarır.
    Hem parantez içi hem de string başı formatlarını destekler.
    """

    # --- 1. Adım: Önce parantez içi formatını kontrol et (mevcut mantık) ---
    start_paren = component_color_str.find('(')
    end_paren = component_color_str.find(')')

    if start_paren != -1 and end_paren != -1 and end_paren > start_paren:
        # Parantez içindeki metni al
        inner_text = component_color_str[start_paren + 1 : end_paren].strip()
        
        # " PRINTED" kısmını (varsa) kaldır
        # re.IGNORECASE ile büyük/küçük harf duyarsızlığı sağlanır
        cleaned_text_from_paren = re.sub(r'\sPRINTED$', '', inner_text, flags=re.IGNORECASE) 
        
        # İlk kelimeyi almayı deneyelim (örn. "LRA-ECRU" -> "LRA", "R9J-ECRU" -> "R9J")
        potential_code_paren_split = cleaned_text_from_paren.split('-')[0].strip()

        # Eğer potansiyel kod 2-4 karakterli bir harf-rakam kombinasyonu ise kabul et
        # re.match ile string'in başlangıcının regex ile eşleşip eşleşmediği kontrol edilir
        if re.match(r'^[A-Z0-9]{2,4}$', potential_code_paren_split, re.IGNORECASE):
            return potential_code_paren_split.upper() 
        
        # Eğer ilk kelime tire ile ayrılmamışsa veya farklı bir format ise, tüm metindeki ilk kelimeyi dene.
        first_word_from_cleaned_paren = cleaned_text_from_paren.split(' ')[0].strip()
        if re.match(r'^[A-Z0-9]{2,4}$', first_word_from_cleaned_paren, re.IGNORECASE):
            return first_word_from_cleaned_paren.upper()
    
    # --- 2. Adım: Eğer parantez içi mantığı sonuç vermediyse, string'in başından kodu ara ---
    # Bu kısım, "LE4-AÇIK BEJ ÇİZGİLİ" gibi formatlar içindir.
    
    # String'i ilk tireye göre böl. Sadece ilk tireye göre bölmek için limit=1 kullanırız.
    parts = component_color_str.split('-', 1)
    
    # Eğer string boş değilse ve ilk parça varsa
    if parts:
        potential_code_from_start = parts[0].strip()
        
        # Bu potansiyel kodun 2-4 karakterli harf/rakam kombinasyonu olup olmadığını kontrol et
        if re.match(r'^[A-Z0-9]{2,4}$', potential_code_from_start, re.IGNORECASE):
            return potential_code_from_start.upper()
            
    # Yukarıdaki koşulların hiçbiri karşılanmazsa None döndür
    return None


from src.auth.auth_manager_playwright import get_token_sync

def get_option_components_data(order_no, option_id, token):
    """
    XIR API'den GetOptionComponents bilgilerini çeker, baskı komponentlerini filtreler
    ve ComponentColor'a göre baskı bilgilerini döndürür.
    """
    base_url = "https://xir.prod.lcwaikiki.com/xir/request/service/api/Order/GetOptionComponents"
    full_url = f"{base_url}?IsNeedComponentProductProperty=true&optionId={option_id}&orderNo={order_no}"

    print(f"\nXIR API'den GetOptionComponents sorgusu yapılıyor... URL: {full_url}, OptionId: {option_id}, OrderNo: {order_no}")

    current_token = token
    for attempt in range(2):
        try:
            headers = get_common_headers(current_token)
            response = requests.get(full_url, headers=headers)
            
            if response.status_code == 401 and attempt == 0:
                print("HTTP 401 (GetOptionComponents): Token geçersiz/süresi dolmuş! Token yenilenip tekrar deneniyor...")
                current_token = get_token_sync(force_refresh=True)
                if not current_token:
                    print("Hata: Yeni token alınamadı.")
                    return None
                continue

            response.raise_for_status() 
            
            response_json = response.json()
            return response_json

        except requests.exceptions.HTTPError as err:
            if err.response is not None and err.response.status_code == 401 and attempt == 0:
                print("HTTP 401 (GetOptionComponents): Token yenilenip tekrar deneniyor...")
                current_token = get_token_sync(force_refresh=True)
                if not current_token:
                    return None
                continue
            print(f"HTTP Hatası (GetOptionComponents): {err}")
            return None
        except requests.exceptions.RequestException as err:
            print(f"İstek Hatası (GetOptionComponents): {err}")
            return None
        except json.JSONDecodeError:
            print("GetOptionComponents yanıtı JSON formatında değil.")
            return None
        except Exception as err:
            print(f"Beklenmedik bir hata oluştu (GetOptionComponents): {err}")
            return None

    return None

if __name__ == "__main__":
    print("--- XIR GetOptionComponents API Testi ---")
    
    try:
        from src.auth.auth_manager_playwright import get_token_sync
        test_token = get_token_sync()
        if test_token:
            test_order_no = 1259111 
            test_option_id = 1088690 
            
            print_info = get_option_components_data(test_order_no, test_option_id, test_token)
            if print_info:
                print(f"OrderNo {test_order_no}, OptionId {test_option_id} için baskı bilgileri: {print_info}")
            else:
                print(f"OrderNo {test_order_no}, OptionId {test_option_id} için baskı bilgisi bulunamadı.")
        else:
            print("Token alınamadı, test yapılamadı.")
    except Exception as e:
        print(f"Test sırasında beklenmedik bir hata oluştu: {e}")
