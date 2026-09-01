# src/cli/generate_bom_template.py

from asyncio.log import logger
import json
import logging
import os
from src.file_management.excel_generator import create_bom_template_excel, create_set_bom_template_excel

from src.auth.auth_manager_playwright import _cached_token, get_token_sync
from src.data_sources.variant_value_api import get_variant_details

# Logging yapılandırması (main'den veya genel bir config'den gelmeli, burada örnek için)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def generate_bom_template_cli(data):
    """
    Kullanıcıdan alınan PO verilerine göre BOM şablonu Excel dosyasını oluşturur.
    Bu fonksiyon, otomasyon akışından bağımsız olarak çağrılmak üzere tasarlanmıştır.
    """
    try:
# --- BOM Şablonu Excel Oluşturma ---
       
        plm_id = data.get('plm_code') # JSON'dan PLM ID'yi al
        isPrinted = data.get('isPrinted')
        style_name = data.get('styleName')
        if not plm_id:
            raise Exception("JSON verisinde 'plm_code' bulunamadı, BOM şablonu oluşturulamadı.")

        # Renk kodlarını JSON'dan al
        available_colors = list(data['order_color_code']) if 'order_color_code' in data else []
        if not available_colors:
            logger.warning("JSON verisinde renk kodu bulunamadı, Renk dropdown'ı boş olabilir.")

        # Beden kodlarını JSON'dan al (varsayım: selected_size_sequence_numbers zaten görünen beden isimleri)
        # EĞER bu sadece sıra numaralarıysa, zmm0020_beden_secimi'nde gerçek beden isimlerini çekmeliyiz.
        available_sizes = [str(s) for s in data['sizes']] if 'sizes' in data else []
        if not available_sizes:
            logger.warning("JSON verisinde beden kodu bulunamadı")

        logger.info(f"BOM Şablonu için PLM ID: {plm_id}, Renkler: {available_colors}, Bedenler: {available_sizes}")
        
        bom_template_path = create_bom_template_excel(plm_id, style_name, available_colors, available_sizes, isPrinted)
        if not bom_template_path:
            raise Exception("BOM şablonu Excel dosyası oluşturulamadı.")
        
        logger.info(f"BOM şablonu '{bom_template_path}' başarıyla oluşturuldu. Kullanıcının doldurması bekleniyor.")
        return bom_template_path

    except json.JSONDecodeError as e:
        logger.exception(f"PO veri JSON dosyası okunurken hata oluştu: {e}")
        return None
    except Exception as e:
        logger.exception(f"BOM şablonu oluşturulurken beklenmeyen bir hata oluştu: {e}")
        return None
    
def generate_set_bom_template_cli(data):
    """
    Set siparişler için her child ürünü içeren çok sayfalı BOM şablonu oluşturur.
    """
    try:
        plm_id = data.get('plm_code')
        style_name = data.get('styleName')
        available_sizes = [str(s) for s in data.get('sizes', [])]
        childrens = data.get('childrens', [])
        po_no = data.get('po_no')
        order_color_code = data.get('order_color_code', [])
         # Token'ı al ve API sorgusunu yap
        logger.info(f"Varyant değerleri API'den çekiliyor. PO: {po_no}")
        
        token = get_token_sync()

        api_results = get_variant_details(po_no, token)

        if not childrens:
            raise Exception("Set siparişi içerisinde 'childrens' verisi bulunamadı.")

        logger.info(f"SET BOM Şablonu oluşturuluyor: {style_name} (Çocuk Sayısı: {len(childrens)})")
        
        # Set'e özel generator fonksiyonunu çağırıyoruz
        bom_template_path = create_set_bom_template_excel(plm_id, style_name, available_sizes, childrens, order_color_code, api_results)
        
        if not bom_template_path:
            raise Exception("Set BOM şablonu oluşturulamadı.")
            
        return bom_template_path

    except Exception as e:
        logger.exception(f"Set BOM şablonu oluşturulurken hata: {e}")
        return None

