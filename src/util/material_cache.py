import json
import os
from datetime import datetime

class MaterialCache:
    def __init__(self, filepath="data/material_cache.json"):
        # Verileri tutacağımız klasörü oluştur (Yoksa)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.filepath = filepath
        self.cache = self._load_cache()

    def _load_cache(self):
        """Kayıtlı JSON dosyasını okur, yoksa boş sözlük döner"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        """Verileri JSON dosyasına kaydeder"""
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=4, ensure_ascii=False)

    def add_material(self, tanim, matnr, tur, model):
        """Yeni açılan malzemeyi hafızaya ekler"""
        key = str(tanim).strip().upper()
        self.cache[key] = {
            "matnr": matnr,
            "tur": tur,
            "model": model,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save_cache()

    def get_material(self, tanim):
        """Tanımı verilen malzemenin kodunu döndürür (Varsa)"""
        key = str(tanim).strip().upper()
        return self.cache.get(key)