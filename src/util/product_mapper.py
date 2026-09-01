# src/utils/product_mapper.py

def get_product_code(definition):
    """
    Product Definition metnini analiz eder ve tablodaki SAP kodunu döndürür.
    Görseldeki tüm kodlar ve metinler eklenmiştir.
    """
    if not definition:
        return "99999"

    # Karşılaştırma kolaylığı için metni normalize et
    text = definition.lower().replace('i', 'i').replace('I', 'ı').strip()

    # --- 1. ÖNCELİKLİ ÖZEL KURALLAR (Metin İçinde Birden Fazla Kelime Arayanlar) ---
    
    # Gömlek Grubu
    if "gömlek" in text:
        if "uzun" in text: return "04000"
        if "kısa" in text: return "05000"
        return "04000" # Varsayılan

    # T-shirt Grubu
    if "t-shirt" in text or "tshirt" in text:
        if "uzun" in text: return "15000"
        if "kısa" in text: return "16000"
        return "16000" # Varsayılan

    # Body Grubu
    if "body" in text or "zıbın" in text:
        if "çıtçıt" in text: return "52000"
        if "uzun" in text: return "13000"
        if "kısa" in text: return "14000"
        return "13000"

    # Kostüm Grubu
    if "kostüm" in text:
        if "üst" in text: return "30000"
        if "pantolon" in text: return "31000"
        if "başlık" in text: return "32000"
        if "pelerin" in text: return "33000"
        if "maske" in text: return "34000"
        if "tulum" in text: return "35000"
        if "elbise" in text: return "80000"
        return "30000"

    # Plaj Grubu
    if "plaj" in text:
        if "elbise" in text: return "47000"
        if "şort" in text: return "48000"

    # Maske Grubu (Kostüm olmayanlar)
    if "maske" in text:
        if "telli" in text: return "82000"
        if "ticari" in text: return "83000"
        if "kumaş" in text: return "85000"
        return "81000"

    # Siperlik Grubu
    if "siperlik" in text:
        if "ticari" in text: return "87000"
        return "86000"

    # Önlük Grubu
    if "önlük" in text:
        if "mutfak" in text: return "90000"
        return "44000"

    # Pantolon Grubu (Özel)
    if "pantolon" in text and "ekose" in text:
        return "79000"

    # --- 2. GENEL EŞLEŞTİRME SÖZLÜĞÜ (Tek Kelimelik Net Eşleşmeler) ---
    mapping = {
        "atlet": "01000",
        "sweat": "02000",
        "pantolon": "03000",
        "elbise": "06000",
        "etek": "07000",
        "tunik": "08000",
        "ceket": "09000",
        "yelek": "10000",
        "hırka": "11000",
        "mont": "12000",
        "tayt": "17000",
        "bluz": "18000",
        "tulum": "19000",
        "salopet": "20000",
        "pijama": "21000",
        "kazak": "22000",
        "bermuda": "23000",
        "şort": "24000",
        "roller": "25000",
        "capri": "26000",
        "polo-shirt": "27000",
        "eşofman": "28000",
        "fanila": "29000",
        "kravat": "36000",
        "papyon": "37000",
        "şapka": "38000",
        "eldiven": "39000",
        "bolero": "40000",
        "boxer": "41000",
        "slip": "42000",
        "battaniye": "43000",
        "sırt bezi": "45000",
        "kaban": "46000",
        "iç çamaşır": "49000",
        "bustiyer": "51000",
        "gecelik": "53000",
        "mayo": "54000",
        "bandana": "55000",
        "bere": "56000",
        "boyunluk": "57000",
        "mağaza": "58000",
        "çanta": "59000",
        "cüzdan": "60000",
        "çorap": "61000",
        "havlu": "62000",
        "masa örtü": "63000",
        "nevresim": "64000",
        "oyuncak": "65000",
        "saç bandı": "66000",
        "taç": "67000",
        "supla": "68000",
        "bardak alt": "69000",
        "çarşaf": "70000",
        "yastık kılıf": "71000",
        "yastık": "72000",
        "şal": "73000",
        "atkı": "74000",
        "uyku band": "75000",
        "kapı süs": "76000",
        "kemer": "77000",
        "yakalık": "78000",
        "süveter": "89000",
        "hammadde": "91000",
        "hurda": "92000",
        "ayakkabı": "93000",
        "terlik": "94000",
        "işletme": "95000",
        "ecc teklif": "99999"
    }

    # Sözlükte döngüye gir ve metin içinde anahtar kelimeyi ara
    for key, code in mapping.items():
        if key in text:
            return code

    # Hiçbir kurala uymuyorsa
    return "99999"