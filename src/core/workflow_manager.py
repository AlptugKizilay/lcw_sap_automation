# src/core/workflow_manager.py

import json
import pandas as pd 
import logging

# Diğer modüllerden gerekli fonksiyonları import ediyoruz
from src.auth.auth_manager_playwright import get_token_sync, get_xir_sync
from src.data_sources.mdx_query_handler import excel_motoruyla_sorgula
from src.data_processing.json_transformer import transform_df_to_json
from src.data_sources.order_options_api import get_order_options_data 
from src.data_sources.order_components_api import printed_colors_counter # <-- Yeni import

logger = logging.getLogger(__name__)

COUNTRY_MAPPING = {
    "MISIR": 56,
    "EGYPT": 56,
    "FAS": 57,
    "MOROCCO": 57,
    "TURKIYE": 48,
    "TÜRKIYE": 48,
    "TURKEY": 48,
}

def get_country_id_from_name(country_name: str, default_country_id: int = 56) -> int:
    """
    Siparişin geçildiği ülke adına göre PRODUCT_INFO_COUNTRY_ID değerini döner:
    - {id: 56, name: "EGYPT"} (MISIR)
    - {id: 57, name: "MOROCCO"} (FAS)
    - {id: 48, name: "TURKEY"} (TURKIYE)
    """
    if not country_name or not isinstance(country_name, str):
        return default_country_id
    
    clean_name = country_name.strip().upper()
    if clean_name in COUNTRY_MAPPING:
        return COUNTRY_MAPPING[clean_name]
    
    if "MISIR" in clean_name or "EGYPT" in clean_name:
        return 56
    elif "FAS" in clean_name or "MOROCCO" in clean_name:
        return 57
    elif "TURK" in clean_name or "TURKEY" in clean_name:
        return 48
        
    return default_country_id

def run_full_sap_automation(siparis_kodu, published_label_id=61, country_id=None, product_search_type=0):
    """
    SAP otomasyon projesinin veri çekme ve JSON dönüştürme aşamalarını yönetir.
    country_id verilmezse (None) veya dinamik belirlenmek istenirse MDX'ten dönen
    'Siparişin Geçildiği Ülke' bilgisine göre otomatik ayarlanır.
    """
    print(f"Otomasyon iş akışı başlatıldı. Sipariş Kodu: {siparis_kodu}")

    # --- 1. Adım: Kimlik Doğrulama Token'ını Al ---
    auth_token = get_token_sync()
    
    if not auth_token:
        raise Exception("Kimlik doğrulama token'ı alınamadı, işlem durduruluyor.")
    print("Kimlik doğrulama token'ı başarıyla alındı/yenilendi.")

    # --- 2. Adım: MDX Verisini Çek ---
    print(f"\nMDX sorgusu çalıştırılıyor. Sipariş Kodu: {siparis_kodu}")
    df_raw_data = excel_motoruyla_sorgula(siparis_kodu)
    
    if isinstance(df_raw_data, str): 
        raise Exception(f"MDX sorgusu başarısız: {df_raw_data}")
    
    if df_raw_data.empty:
        print(f"Uyarı: MDX sorgusu sipariş kodu {siparis_kodu} için boş DataFrame döndürdü.")
        return None 

    # --- 2.1. Dinamik Ülke ID Belirleme ---
    if 'Siparişin Geçildiği Ülke' in df_raw_data.columns and not df_raw_data['Siparişin Geçildiği Ülke'].dropna().empty:
        siparis_ulkesi = str(df_raw_data['Siparişin Geçildiği Ülke'].dropna().iloc[0])
        detected_country_id = get_country_id_from_name(siparis_ulkesi, default_country_id=country_id or 56)
        logger.info(f"MDX'ten tespit edilen ülke: '{siparis_ulkesi}' -> Dinamik PRODUCT_INFO_COUNTRY_ID: {detected_country_id}")
        country_id = detected_country_id
    else:
        if country_id is None:
            country_id = 56 # Varsayılan Mısır (56)
        logger.info(f"MDX verisinde ülke bilgisi bulunamadı. Kullanılan COUNTRY_ID: {country_id}")

    # --- 3. Adım: XIR API'den OrderOptions bilgilerini çek ---
    print(f"\nOrderOptions API'den OptionId'ler çekiliyor. Sipariş Kodu: {siparis_kodu}")
    option_ids = get_order_options_data(siparis_kodu, auth_token) 
    
    all_print_info_by_color = {} # Tüm optionId'ler için toplanan baskı bilgileri

    if option_ids:
        print(f"Sipariş Kodu {siparis_kodu} için bulunan OptionId'ler: {option_ids}")
        # Her bir optionId için GetOptionComponents API'sini çağır
        for opt_id in option_ids:
            print_info_for_option = printed_colors_counter(siparis_kodu, opt_id, auth_token) # <-- Yeni API çağrısı
            if print_info_for_option:
                # Toplanan baskı bilgilerini birleştir (aynı renk için sayacı topla)
                for color_code, count in print_info_for_option.items():
                    all_print_info_by_color[color_code] = all_print_info_by_color.get(color_code, 0) + count
        
        if all_print_info_by_color:
            print(f"Tüm OptionId'ler için toplanan baskı bilgileri: {all_print_info_by_color}")
        else:
            print(f"Uyarı: Sipariş Kodu {siparis_kodu} için hiçbir baskı komponenti bulunamadı.")
    else:
        print(f"Uyarı: Sipariş Kodu {siparis_kodu} için OrderOptions API'den OptionId bulunamadı.")

    # --- 4. Adım: Çekilen Veriyi JSON Yapısına Dönüştür (ve Diğer API'leri Çağır) ---
    logger.info("\nVeri JSON formatına dönüştürülüyor")
    json_output = transform_df_to_json(
        df_raw_data,
        siparis_kodu,
        published_label_id,
        country_id,
        product_search_type,
        auth_token,
        all_print_info_by_color # <-- Baskı bilgilerini json_transformer'a ilettik
    )

    if "error" in json_output: 
        raise Exception(f"JSON dönüşümü başarısız: {json_output['error']}")
    
    print("Veri JSON formatına başarıyla dönüştürüldü.")

    return json_output 