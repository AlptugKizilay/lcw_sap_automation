# src/data_processing/json_transformer.py

import pandas as pd
import json
import re # Renk kodunu çıkarmak için regex kullanacağız
from typing import List, Dict, Any, Optional, Union
from src.data_sources.product_info_api import get_product_list_from_order_code, get_product_information_and_beden
from src.data_sources.technical_sheets_api import get_technical_sheets 
from src.util.product_mapper import get_product_code
from src.util.currency_helper import get_usd_to_egp_rate
from src.util.sizegroup_mapper import determine_size_group, get_size_sequence_numbers 


# transform_df_to_json fonksiyonuna 'auth_token' ve 'print_info_by_color' parametrelerini ekledik
def transform_df_to_json(df, siparis_kodu, published_label_id, country_id, product_search_type, auth_token, all_print_info_by_color): # <-- Yeni parametre eklendi
    if isinstance(df, str): 
        return {"error": df}
    
    if df.empty:
        return {"error": f"Sipariş kodu '{siparis_kodu}' için dönüştürülecek veri bulunamadı."}

    # --- Beden bilgilerini API'den çekme ---
    sizes_list = []
    try:
        product_list_for_payload = get_product_list_from_order_code(siparis_kodu, published_label_id, country_id, product_search_type, auth_token)
        if product_list_for_payload:
            #print(f"product_list_for_payload: {product_list_for_payload}")
            beden_bilgileri = get_product_information_and_beden(product_list_for_payload, siparis_kodu, country_id, published_label_id, auth_token)
            if beden_bilgileri:
                #print(f"beden_bilgileri: {beden_bilgileri}")
                sizes_list = sorted(list(set([item['value'] for item in beden_bilgileri])))
            else:
                print(f"Uyarı: Sipariş kodu {siparis_kodu} için beden bilgisi bulunamadı.")
        else:
            print(f"Uyarı: Sipariş kodu {siparis_kodu} için ProductList API'den boş geldi veya hata oluştu.")
    except Exception as e:
        print(f"Beden bilgisi çekerken hata oluştu: {e}")
        sizes_list = []
    # ----------------------------------------
   
    
    # DataFrame'deki benzersiz Plm Kod'ları bul
    unique_plm_codes = df['Plm Kod'].unique().tolist()
    # Güncel kuru al
    egp_rate = get_usd_to_egp_rate()
    
    # Siparişin takımlı olup olmadığını kontrol et
    if len(unique_plm_codes) == 1:
        # --- Tekli Sipariş Yapısı ---
        main_plm_code = unique_plm_codes[0]
        main_data = df[df['Plm Kod'] == main_plm_code].iloc[0] 
        
        style_name = main_data['Model Adı'].replace('-A', '').replace('-B', '').strip()
        magk = main_data['Merch Alt Grup Kod']
        season = main_data['Sezon']
        special_code = main_data['Özel Kod 1']
        fob_price_usd = float(main_data['FOB Fiyatı'])
        exfactory_date = main_data['Orijinal Exfactory Merch Tarih'] 

        order_color_codes = df[df['Plm Kod'] == main_plm_code]['Renk Kod'].unique().tolist()
        # EGP fiyatını hesapla (Yuvarlayarak)
        fob_price_egp = round(fob_price_usd * egp_rate, 2)
        

        # --- Teknik sayfa bilgilerini API'den çekme (tekli sipariş için) ---
        product_definition = ""
        technical_sheets_data = get_technical_sheets(special_code, auth_token) 
        if technical_sheets_data and isinstance(technical_sheets_data, list):
            for item in technical_sheets_data:
                if item.get('PlmKodu') == main_plm_code:
                    product_definition = item.get('K_UrunAnaTanim', '').strip() or item.get('UrunAnaTanim', '').strip()
                    break
            if not product_definition and technical_sheets_data: 
                product_definition = technical_sheets_data[0].get('K_UrunAnaTanim', '').strip()
        if not product_definition:
            print(f"Uyarı: Tekli sipariş için '{special_code}' Özel Kod 1'ine ait teknik sayfa tanımı bulunamadı.")

        # ------------------------------------------------------------------
        sap_product_code = get_product_code(product_definition)
        size_group = determine_size_group(magk, sizes_list)
        selected_size_sequence_numbers = get_size_sequence_numbers(size_group, sizes_list)
        # ------------------------------------------------------------------

        # Tekli sipariş için baskı kontrolü (Ana modelin renk kodu ile eşleştir)
        is_printed_main = False
        if order_color_codes and all_print_info_by_color:
            main_color_code = order_color_codes[0] # Tekli siparişin ana renk kodunu al
            if all_print_info_by_color.get(main_color_code, 0) > 0:
                is_printed_main = True
            if all_print_info_by_color.get("SEE_ARTWORK_PRINT", 0) > 0:
                is_printed_main = True
        
        single_order_json = {
            "orderType": "single",
            "styleName": style_name,
            "po_no": str(siparis_kodu),
            "MAGK": magk,
            "season": season,
            "plm_code": main_plm_code,
            "special_code": special_code,
            "fob_price_usd": fob_price_usd,
            "fob_price_egp": fob_price_egp,
            "order_color_code": order_color_codes,
            "sizes": sizes_list,
            "selected_size_sequence_numbers": selected_size_sequence_numbers,
            "productDefiniton": product_definition,
            "sapProductCode": sap_product_code, 
            "isPrinted": is_printed_main, # <-- Tekli sipariş için isPrinted eklendi
            "size_group": size_group,
            "sale_group": "#magk göre belirlenecek#",
             "exfactoryDate": exfactory_date
        }
        return [single_order_json]

    else:
        # --- Takımlı Sipariş Yapısı (Mevcut Mantık) ---
        plm_codes_with_fob = df[df['FOB Fiyatı'] > 0]['Plm Kod'].unique().tolist()

        if not plm_codes_with_fob:
            return {"error": f"Sipariş kodu '{siparis_kodu}' için pozitif FOB Fiyatı olan ana Plm Kod bulunamadı."}
        
        if len(plm_codes_with_fob) > 1:
            print(f"Uyarı: Sipariş kodu '{siparis_kodu}' için birden fazla pozitif FOB Fiyatı olan Plm Kod bulundu: {plm_codes_with_fob}. Model Adı'nda ek içermeyeni ana model olarak seçme denemesi yapılıyor.")
            main_candidates = df[df['Plm Kod'].isin(plm_codes_with_fob)]
            non_suffix_models = main_candidates[~main_candidates['Model Adı'].str.contains(r'-A|-B', na=False)]
            if not non_suffix_models.empty:
                main_plm_code = non_suffix_models['Plm Kod'].iloc[0]
            else:
                main_plm_code = plm_codes_with_fob[0]
        else:
            main_plm_code = plm_codes_with_fob[0]
        
        df_main = df[df['Plm Kod'] == main_plm_code]
        df_children = df[df['Plm Kod'] != main_plm_code]
        
        if df_main.empty:
            return {"error": f"Belirlenen ana Plm Kod ({main_plm_code}) için veri bulunamadı (iç hata)."}

        style_name = df_main['Model Adı'].iloc[0].replace('-A', '').replace('-B', '').strip()
        magk = df_main['Merch Alt Grup Kod'].iloc[0]
        season = df_main['Sezon'].iloc[0]
        special_code = df_main['Özel Kod 1'].iloc[0]
        fob_price_usd = float(df_main['FOB Fiyatı'].iloc[0])
        exfactory_date = df_main['Orijinal Exfactory Merch Tarih'].iloc[0]

        main_order_color_codes = df_main['Renk Kod'].unique().tolist()
        fob_price_egp = round(fob_price_usd * egp_rate, 2)

        # --- Teknik sayfa bilgilerini API'den çekme (takımlı sipariş için) ---
        technical_sheets_data_all = get_technical_sheets(special_code, auth_token)
        
        technical_sheets_map = {}
        if technical_sheets_data_all and isinstance(technical_sheets_data_all, list):
            for item in technical_sheets_data_all:
                plm_kodu = item.get('PlmKodu')
                urun_tanim = item.get('K_UrunAnaTanim', '').strip() or item.get('UrunAnaTanim', '').strip()
                if plm_kodu is not None:
                    technical_sheets_map[plm_kodu] = urun_tanim
        
        main_product_definition = technical_sheets_map.get(main_plm_code, "")
        if not main_product_definition and technical_sheets_data_all: 
             main_product_definition = technical_sheets_data_all[0].get('K_UrunAnaTanim', '').strip()
        if not main_product_definition:
            print(f"Uyarı: Takımlı sipariş ana modeli için '{special_code}' Özel Kod 1'ine ait teknik sayfa tanımı bulunamadı.")
       
        # ------------------------------------------------------------------
        sap_product_code_main = get_product_code(main_product_definition)
        size_group = determine_size_group(magk, sizes_list)
        selected_size_sequence_numbers = get_size_sequence_numbers(size_group, sizes_list)
        # ------------------------------------------------------------------

        # Ana model için baskı kontrolü (Ana modelin renk kodu ile eşleştir)
        is_printed_main = False
        if main_order_color_codes and all_print_info_by_color:
            main_color_code = main_order_color_codes[0] # Ana modelin ilk renk kodunu al
            if all_print_info_by_color.get(main_color_code, 0) > 0:
                is_printed_main = True

        main_json_entry = {
            "orderType": "set",
            "styleName": style_name,
            "po_no": str(siparis_kodu),
            "MAGK": magk,
            "season": season,
            "plm_code": main_plm_code,
            "special_code": special_code,
            "fob_price_usd": fob_price_usd,
            "fob_price_egp": fob_price_egp,
            "order_color_code": main_order_color_codes,
            "sizes": sizes_list,
            "selected_size_sequence_numbers": selected_size_sequence_numbers,
            "productDefiniton": main_product_definition, 
            "sap_product_code_main": sap_product_code_main,
            "isPrinted": is_printed_main, # <-- Ana model için isPrinted eklendi
            "size_group": size_group,
            "sale_group": "#magk göre belirlenecek#",
            "exfactoryDate": exfactory_date,
            "main_material_code": "",
            "childrens": []
        }

        child_plm_codes = df_children['Plm Kod'].unique().tolist()
        print(f"Çocuk Plm Kod sayısı: {len(child_plm_codes)}")
        fob_price_egp_eachChild = round(fob_price_egp / len(child_plm_codes), 2) 
        fob_price_usd_eachChild = round(fob_price_usd / len(child_plm_codes), 2)
        # Karmaşık "aynı renk, farklı baskı" mantığı için sayaç
        # Hangi renkten kaç çocuğa baskı atandığını takip edecek
        assigned_prints_count_by_color = {color: 0 for color in all_print_info_by_color.keys()}


        for child_plm in child_plm_codes:
            child_data = df_children[df_children['Plm Kod'] == child_plm]
            
            if child_data.empty:
                continue
            component_colors_for_child = child_data['Renk Kod'].unique().tolist()
            sonuc_unique = child_data.groupby('Orijinal Exfactory Merch Tarih')['Renk Kod']
            print(sonuc_unique)
            
            child_product_definition = technical_sheets_map.get(child_plm, "")
            sap_product_code = get_product_code(child_product_definition)
            if not child_product_definition:
                print(f"Uyarı: Çocuk Plm Kodu '{child_plm}' için teknik sayfa tanımı bulunamadı.")

            is_printed_for_child = False
            if component_colors_for_child and all_print_info_by_color:
                child_main_color_code = component_colors_for_child[0] # Çocuğun ana renk kodunu al

                # Eğer bu renk kodu için API'den baskı bilgisi geldiyse
                # VE bu renge ait atanabilecek baskı sayısı henüz tükenmediyse
                if all_print_info_by_color.get(child_main_color_code, 0) > 0 and \
                   assigned_prints_count_by_color.get(child_main_color_code, 0) < all_print_info_by_color.get(child_main_color_code, 0):
                    
                    is_printed_for_child = True
                    assigned_prints_count_by_color[child_main_color_code] += 1 # Atanan baskı sayacını artır

            child_entry = {
                "plm_code": child_plm,
                "componentColor": component_colors_for_child,
                "productDefiniton": child_product_definition, 
                "sapProductCode": sap_product_code,
                "isPrinted": is_printed_for_child, # <-- Children için isPrinted eklendi
                "price_egp": fob_price_egp_eachChild,
                "price_usd": fob_price_usd_eachChild,
                "sap_material_code": ""
            }
            main_json_entry["childrens"].append(child_entry)

        return [main_json_entry]
