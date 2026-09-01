# src/data_sources/mdx_query_handler.py

from datetime import datetime
import win32com.client
import pandas as pd
import pythoncom

def excel_motoruyla_sorgula(siparis_kodu):
    conn_str = (
        "Provider=MSOLAP;"
        "Data Source=lcwtabular_s30;"
        "Initial Catalog=ASAS_30;" 
        "Integrated Security=SSPI;"
    )

    # MDX Sorgusu: Üretici ve Siparişin Geçildiği Ülke eklendi, Sipariş Kod ON ROWS'tan kaldırıldı.
    mdx_query = f"""
    SELECT 
        {{ [Measures].[FOB Fiyatı] }} ON COLUMNS,  -- 1 ölçü
        CROSSJOIN(
            {{[Model Özellikleri].[Sezon].[Sezon].MEMBERS}},      -- 1. Boyut
            CROSSJOIN(
                {{[Model Özellikleri].[Merch Alt Grup Kod].[Merch Alt Grup Kod].MEMBERS}}, -- 2. Boyut
                CROSSJOIN(
                    {{[Model Özellikleri].[Model Adı].[Model Adı].MEMBERS}},  -- 3. Boyut
                    CROSSJOIN(
                        {{[Model Özellikleri].[Renk Kod].[Renk Kod].MEMBERS}}, -- 4. Boyut
                        CROSSJOIN(
                            {{[Model Özellikleri].[Plm Kod].[Plm Kod].MEMBERS}}, -- 5. Boyut
                            CROSSJOIN(
                                {{[Model Özellikleri].[Özel Kod 1].[Özel Kod 1].MEMBERS}}, -- 6. Boyut
                                CROSSJOIN(
                                    {{[Model Özellikleri].[Üretici].[Üretici].MEMBERS}}, -- 7. Boyut
                                    CROSSJOIN(
                                        {{[Model Özellikleri].[Siparişin Geçildiği Ülke].[Siparişin Geçildiği Ülke].MEMBERS}}, -- 8. Boyut (YENİ EKLENDİ)
                                        {{[Tarihler].[Orijinal Exfactory Merch Tarih].MEMBERS}} -- 9. Boyut
                                    )
                                )                                                         
                            )
                        )
                    )
                )
            )
        ) ON ROWS  -- Toplam 9 boyut + 1 ölçü = 10 sütun bekleniyor
    FROM [Genel]  
    WHERE ( [Model Özellikleri].[Sipariş Kod].&[{siparis_kodu}] ) 
    """

    #print("Çalıştırılan MDX Sorgusu:\n", mdx_query) 

    conn = None
    try:
        pythoncom.CoInitialize() 

        conn = win32com.client.Dispatch("ADODB.Connection")
        conn.ConnectionString = conn_str
        conn.Open()
        
        recordset, affected_rows = conn.Execute(mdx_query)
        
        if recordset.EOF:
            return f"'{siparis_kodu}' için sonuç bulunamadı."
        
        data = recordset.GetRows()
        df = pd.DataFrame(data).T
        
        actual_adodb_field_names = []
        for i in range(recordset.Fields.Count):
            actual_adodb_field_names.append(recordset.Fields.Item(i).Name)

        print(f"DEBUG: ADODB Recordset'ten dönen gerçek sütun sayısı: {recordset.Fields.Count}")
        #print(f"DEBUG: ADODB Recordset'ten dönen gerçek sütun isimleri (ham): {actual_adodb_field_names}")
        
        # Beklenen DataFrame sütun isimleri, MDX sorgusundaki ON ROWS sırasına göre ayarlandı (10 elemanlı)
        expected_df_column_names = [
            "[Model Özellikleri].[Sezon].[Sezon].[MEMBER_CAPTION]",
            "[Model Özellikleri].[Merch Alt Grup Kod].[Merch Alt Grup Kod].[MEMBER_CAPTION]",
            "[Model Özellikleri].[Model Adı].[Model Adı].[MEMBER_CAPTION]",
            "[Model Özellikleri].[Renk Kod].[Renk Kod].[MEMBER_CAPTION]",
            "[Model Özellikleri].[Plm Kod].[Plm Kod].[MEMBER_CAPTION]",
            "[Model Özellikleri].[Özel Kod 1].[Özel Kod 1].[MEMBER_CAPTION]",            
            "[Model Özellikleri].[Üretici].[Üretici].[MEMBER_CAPTION]",
            "[Model Özellikleri].[Siparişin Geçildiği Ülke].[Siparişin Geçildiği Ülke].[MEMBER_CAPTION]", # YENİ EKLENDİ
            "[Tarihler].[Orijinal Exfactory Merch Tarih].[Orijinal Exfactory Merch Tarih].[MEMBER_CAPTION]",
            "[Measures].[FOB Fiyatı]" 
        ]
        
        if recordset.Fields.Count != len(expected_df_column_names):
            raise ValueError(
                f"MDX sorgusundan dönen sütun sayısı beklenenden farklı. "
                f"Beklenen: {len(expected_df_column_names)}, Gelen: {recordset.Fields.Count}. "
                f"Dönen ham isimler: {actual_adodb_field_names}" 
            )

        df.columns = expected_df_column_names
        
        # Sütun isimlerini daha okunabilir hale getirelim 
        renamed_columns = {}
        for col in df.columns:
            if col.endswith('.[MEMBER_CAPTION]'):
                parts = col.split('.')
                if len(parts) >= 3: 
                    renamed_columns[col] = parts[-3].replace('[', '').replace(']', '')
                else:
                    renamed_columns[col] = col.replace('.[MEMBER_CAPTION]', '').replace('[', '').replace(']', '')
            elif col.startswith('[Measures].['): 
                renamed_columns[col] = col.replace('[Measures].[', '').replace(']', '')
            else:
                renamed_columns[col] = col 
        
        df = df.rename(columns=renamed_columns)
        print(f"DEBUG: Yeniden adlandırılan DataFrame sütunları: {df.columns.tolist()}")

        # Sipariş Kodu'nu DataFrame'e manuel olarak ekleme satırı KALDIRILDI.
        # df['Sipariş Kod'] = int(siparis_kodu) 

        # Sütunların varlığını kontrol ederek işlem yap (yeniden adlandırma sonrası)
        if 'Plm Kod' in df.columns:
            df = df.dropna(subset=['Plm Kod'])
            df['Plm Kod'] = pd.to_numeric(df['Plm Kod'], errors='coerce').fillna(0).astype(int)
        else:
            raise KeyError("'Plm Kod' sütunu bulunamadı, DataFrame ataması/yeniden adlandırma hatalı.")
        
        if 'FOB Fiyatı' in df.columns:
            df['FOB Fiyatı'] = pd.to_numeric(df['FOB Fiyatı'], errors='coerce').fillna(0.0)
        else:
            raise KeyError("'FOB Fiyatı' sütunu bulunamadı, DataFrame ataması/yeniden adlandırma hatalı.")
        
        # Tarih formatını dönüştür (YYYYAAGG -> GG.AA.YYYY)
        if 'Orijinal Exfactory Merch Tarih' in df.columns: 
            df['Orijinal Exfactory Merch Tarih'] = df['Orijinal Exfactory Merch Tarih'].astype(str).apply(lambda x: 
                datetime.strptime(x, '%Y%m%d').strftime('%d.%m.%Y') if pd.notna(x) and x.isdigit() and len(x) == 8 else None
            )
        else:
            print("WARNING: 'Orijinal Exfactory Merch Tarih' sütunu yeniden adlandırma sonrası bulunamadı. Tarih dönüşümü atlandı.")
        
        # Sipariş Kod sütunu artık DataFrame'de yok, bu kontrol kaldırıldı.
        # if 'Sipariş Kod' in df.columns:
        #     df['Sipariş Kod'] = pd.to_numeric(df['Sipariş Kod'], errors='coerce').fillna(0).astype(int)
        # else:
        #     print("WARNING: 'Sipariş Kod' sütunu DataFrame'de bulunamadı.")


        return df
        
    except Exception as e:
        error_message = str(e)
        if "The dimension" in error_message or "The level" in error_message or "The measure" in error_message:
            return f"Hata: MDX sorgusundaki boyut, öznitelik veya ölçü adları yanlış olabilir. Lütfen küp yapınızı kontrol edin. \n\nOrijinal Hata: {e}"
        return f"Bir bağlantı veya sorgu hatası oluştu: {e}"
        
    finally:
        if conn and conn.State == 1:
            conn.Close()
        pythoncom.CoUninitialize()

if __name__ == "__main__":
    print("--- MDX Sorgu Testi ---")
    
    test_orders = ["1355273", "1288697", "1307821"]
    for code in test_orders:
        print(f"\n==================== Sipariş Kodu: {code} ====================")
        df_result = excel_motoruyla_sorgula(code)
        
        if isinstance(df_result, pd.DataFrame):
            print(f"Sipariş Kodu {code} için MDX sorgusu başarılı.")
            print("DataFrame Sütunları:", df_result.columns.tolist())
            if 'Siparişin Geçildiği Ülke' in df_result.columns:
                print("Siparişin Geçildiği Ülke Değerleri:", df_result['Siparişin Geçildiği Ülke'].unique())
            if 'Üretici' in df_result.columns:
                print("Üretici Değerleri:", df_result['Üretici'].unique())
            print("DataFrame İlk 5 Satır:")
            print(df_result[['Plm Kod', 'Özel Kod 1', 'Üretici', 'Siparişin Geçildiği Ülke', 'FOB Fiyatı']].head())
        else:
            print(f"MDX sorgusu başarısız: {df_result}")
