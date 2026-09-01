SIZE_GROUP_MAPPING = {
    "COCUK": {
        "3m-6m": "5",
        "9m-12m": "21",
        "1y-2y": "1",
        "2y-3y": "3",
        "3y-4y": "4",
        "3y-6y": "5",
        "4y-5y": "8",
        "4y-6y": "9",
        "5y-6y": "10",
        "6y-7y": "11",
        "6y-8y": "12",
        "6y-10y": "13",
        "7y-8y": "14",
        "7y-9y": "15",
        "7y-10y": "16",
        "8+": "19",
        "8y-9y": "17",
        "8y-10y": "18",
        "9+": "22",
        "9y-10y": "20",
        "10+": "27",
        "10y-11y": "23",
        "10y-12y": "24",
        "10y-13y": "25",
        "10y-14y": "26",
        "11y-12y": "28",
        "12y-13y": "29",
        "13y": "31",
        "13y-14y": "32",
        "14y-15y": "33",
        "14y-16y": "34",
        "15y-16y": "35",
        "12y-14y": "30",
        "3y-14y": "7",
        "18m-24m": "2"
    },
    "BEBEK": {
        "0m": "1",
        "0m-1m": "2",
        "0m-2m": "3",
        "0m-3m": "4",
        "0m-6m": "5",
        "0m-12m": "6",
        "0m-18m": "7",
        "0m-24m": "8",
        "1m-3m": "9",
        "3m-6m": "11",
        "6m-9m": "12",
        "9m-12m": "13",
        "12m-18m": "14",
        "18m-24m": "15",
        "24m-36m": "16",
        "3y-4y": "17",
        "2y-3y": "18",
        "4y-5y": "19",
        "5y-6y": "20",
        "18m-3y": "21",
        "9m-18m": "22",
        "0y-3y": "23",
        "1y-2y": "24",
        "2y-3y": "25",
        "12m-24m": "26",
        "2y-4y": "27",
        "2y-5y": "28",
        "2y-6y": "29",
        "6m-18m": "30",
        "3y-6y": "31",
        "6m-12m": "32",
        "4y-6y": "33",
        "18m-36m": "34",
        "6y-7y": "35",
        "6y-7y": "36",
        "6y-8y": "37",
        "7y-8y": "38",
        "8y-9y": "39",
        "8y-10y": "40",
        "9y-10y": "41",
        "10y-11y": "42",
        "10y-12y": "43",
        "11y-12y": "44",
        "12y-13y": "45",
        "12y-14y": "46",
        "13y-14y": "47"
    },

    "BUYUK_S-M-L": {
        "XXS": "1",
        "XS": "2",
        "S": "3",
        "M": "4",
        "L": "5",
        "XL": "6",
        "XXL": "7",
        "2XL": "8",
        "3XL": "9",
        "4XL": "10",
        "5XL": "11",
        "6XL": "12",
        "7XL": "13",
        "M-L": "14",
        "XS-S": "15",
        "DMY": "16",
        "XL-XXL": "17",
    },
    "BUYUK_34-36-38": {
        "22": "1",
        "24": "2",
        "25": "3",
        "26": "4",
        "27": "5",
        "28": "6",
        "29": "7",
        "30": "8",
        "31": "9",
        "32": "10",
        "33": "11",
        "34": "12",
        "35": "13",
        "36": "14",
        "37": "15",
        "38": "16",
        "39": "17",
        "40": "18",
        "41": "19",
        "42": "20",
        "43": "21",
        "44": "22",
        "45": "23",
        "46": "24",
        "47": "25",
        "48": "26",
        "49": "27",
        "50": "28",
        "54": "29",
        "56": "30",
        "58": "31",
        "26-30": "32",
        "26-32": "33",
        "28-30": "34",
        "28-32": "35",
        "30-30": "36",
        "30-31": "37",
        "30-32": "38",
        "31-29": "39",
        "31-30": "40",
        "31-31": "41",
        "31-32": "42",
        "32-31": "43",
        "32-32": "44",
        "32-33": "45",
        "32-35": "46",
        "33-31": "47",
        "33-32": "48",
        "34-29": "49",
        "34-30": "50",
        "34-31": "51",
        "34-32": "52",
        "34-33": "53",
        "36-29": "54",
        "36-30": "55",
        "36-31": "56",
        "36-32": "57",
        "36-33": "58",
        "36-35": "59",
        "38-30": "60",
        "38-31": "61",
        "38-32": "62",
        "40-30": "63",
        "40-31": "64",
        "40-32": "65",
        "42-31": "66",
        "42-32": "67",
        "44-31": "68",
        "44-32": "69",
    },
}

def determine_size_group(magk, sizes_list):
    """
    MAGK ve Beden listesine bakarak size_group değerini belirler.
    """
    if not magk:
        return "UNKNOWN"

    magk_lower = magk.lower()
    
    # Kurallar: CU ve CK Grubu (Çocuk/Bebek)
    if magk_lower.startswith(('cu1', 'cu4', 'ck1', 'ck4')):
        return "COCUK"
    
    if magk_lower.startswith(('cub', 'ckb')):
        return "BEBEK"

    # Kurallar: BU Grubu (Büyük)
    if magk_lower.startswith(('bu', 'bg')):
        if not sizes_list:
            return "BUYUK_BELIRSIZ"
        
        # İlk bedene bakarak tipini anla (S, M, L mi yoksa 34, 36 mı?)
        # Beden listesindeki herhangi bir değer harf içeriyorsa S-M-L grubudur.
        has_letters = any(any(char.isalpha() for char in str(size)) for size in sizes_list)
        
        if has_letters:
            return "BUYUK_S-M-L"
        else:
            return "BUYUK_34-36-38"

    return "DIGER"

def get_size_sequence_numbers(size_group, sizes_from_api):
    """
    Belirli bir size_group ve API'den gelen beden listesi için
    karşılık gelen SAP sıra numaralarını döndürür.
    """
    sequence_numbers = []
    
    # İlgili beden grubuna ait eşleşme tablosunu al
    group_map = SIZE_GROUP_MAPPING.get(size_group)
    
    if not group_map:
        print(f"Uyarı: '{size_group}' için beden sıra numarası eşleşmesi bulunamadı.")
        return []

    for api_size in sizes_from_api:
        # API'den gelen bedeni temizle ve küçük harfe çevir (eğer gerekirse)
        # Bedenler zaten API'den temiz string olarak geldiği varsayılıyor.
        normalized_api_size = str(api_size).strip()
        
        # Eşleşme tablosunda bedeni ara ve sıra numarasını al
        seq_num = group_map.get(normalized_api_size)
        
        if seq_num:
            sequence_numbers.append(seq_num)
        else:
            print(f"Uyarı: '{size_group}' grubunda '{normalized_api_size}' bedeni için sıra numarası bulunamadı.")
            # Belki de burada bir hata fırlatmak veya varsayılan bir değer kullanmak daha iyi olabilir.
            # Şimdilik sadece uyarı verip atlıyoruz.
            
    return sequence_numbers