from asyncio.log import logger
import json
import os
def update_json_cache(file_path, key, value):
    if not os.path.exists(file_path):
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            full_content = json.load(f)
            # update_json_cache içine ekle:
        print(f"DEBUG: JSON'a yazılan anahtar: {key}, Değer: {value}")

        # EĞER DOSYA BİR LİSTEYSE 
        if isinstance(full_content, list) and len(full_content) > 0:
            # Listenin ilk elemanı olan ana sözlüğe (Master Dict) veriyi ekle
            full_content[0][key] = value
            print(f"DEBUG: JSON içeriği güncellendi {full_content[0][key]}.")
        
        # EĞER DOSYA DOĞRUDAN BİR SÖZLÜKSE
        elif isinstance(full_content, dict):
            full_content[key] = value

        # Kaydet
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(full_content, f, indent=4, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"Cache güncelleme hatası: {e}")