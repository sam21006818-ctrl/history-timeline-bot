import pandas as pd
import requests
import io
import time
from geopy.geocoders import Nominatim

# 🔗 【重要設定】請在下方雙引號內，貼上您在 Google 表單發布的 CSV 長網址
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR0Ib-gcIDvdoiTJovsjUAflUoA_-NRtg6ZfSdoonmhRSbkc_4bdzzI0w5FbD-DEBI53Vpg3PeALzid/pubhtml"

def fetch_and_clean_all():
    print("🔄 嘗試連線至內政部與開放 API 縣市資料庫...")
    target_urls = [
        "https://data.moi.gov.tw/MoiOD/System/DownloadFile.aspx?DATA=C634AF01-D330-41CA-B303-3C53C5DDE7DC",
        "https://data.ntpc.gov.tw/api/datasets/6D202863-7DA9-4A7B-9BA5-776AB1B2B72E/csv/file"
    ]
    all_clan_data = pd.DataFrame()
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for url in target_urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                response.encoding = 'utf-8'
                df = pd.read_csv(io.StringIO(response.text), dtype=str)
                mask = df.apply(lambda row: row.astype(str).str.contains("謝氏|謝姓|寶樹").any(), axis=1)
                df_clan = df[mask].copy()
                
                if not df_clan.empty:
                    name_col = next((col for col in df_clan.columns if '名' in col or 'name' in col.lower()), df_clan.columns[0])
                    addr_col = next((col for col in df_clan.columns if '址' in col or 'address' in col.lower()), df_clan.columns[1] if len(df_clan.columns)>1 else df_clan.columns[0])
                    leader_col = next((col for col in df_clan.columns if any(k in str(col) for k in ['負責', '代表', '理事長', '姓名'])), None)
                    phone_col = next((col for col in df_clan.columns if '電話' in str(col)), None)
                    fax_col = next((col for col in df_clan.columns if '傳真' in str(col)), None)
                    
                    clean_df = pd.DataFrame({
                        "名稱": df_clan[name_col],
                        "地址": df_clan[addr_col],
                        "負責人": df_clan[leader_col] if leader_col else "政府未公開",
                        "電話": df_clan[phone_col] if phone_col else "政府未公開",
                        "傳真": df_clan[fax_col] if fax_col else "政府未公開"
                    })
                    all_clan_data = pd.concat([all_clan_data, clean_df], ignore_index=True)
        except: pass
    return all_clan_data

def get_default_coords(text):
    county_coords = {
        "台北": (25.0645, 121.5295), "新北": (25.0160, 121.4550), "桃園": (24.9930, 121.3140),
        "新竹": (24.8280, 121.0120), "苗栗": (24.5640, 120.8210), "台中": (24.1415, 120.6750),
        "彰化": (24.0810, 120.5380), "嘉義": (23.4580, 120.3230), "台南": (22.9970, 120.2030),
        "高雄": (22.6320, 120.3200), "屏東": (22.6680, 120.4850), "花蓮": (23.9880, 121.6020),
        "台灣": (25.0320, 121.5190), "金門": (24.449, 118.388)
    }
    for county, coords in county_coords.items():
        if county in text: return coords
    return (23.6, 120.9)

def add_gps_and_save(df_gov):
    final_data = []
    existing_names = []
    geolocator = Nominatim(user_agent="my_xie_cloud_sync_2026")

    # 🥇 優先載入政府最新開放資料
    if df_gov is not None and not df_gov.empty:
        for _, row in df_gov.iterrows():
            name = str(row["名稱"]).strip()
            if name == 'nan' or not name: continue
                
            addr, boss = str(row["地址"]).strip(), str(row["負責人"]).strip()
            phone = str(row.get("電話", "政府未公開")).strip()
            fax = str(row.get("傳真", "政府未公開")).strip()
            lat, lon = get_default_coords(name + addr) 
            
            if addr != 'nan' and addr:
                try:
                    location = geolocator.geocode(addr, timeout=3)
                    if location: lat, lon = location.latitude, location.longitude
                except: pass 
                    
            final_data.append({
                "名稱": name, "負責人": boss if boss != 'nan' else "政府未公開",
                "電話": phone if phone != 'nan' else "政府未公開", "傳真": fax if fax != 'nan' else "政府未公開",
                "地址": addr if addr != 'nan' else "未提供", "緯度": lat, "經度": lon,
                "簡介": "政府開放資料最新同步 (官方優先)"
            })
            existing_names.append(name)

    # 🥈 從 Google 試算表補齊缺漏的資料
    try:
        res = requests.get(GOOGLE_SHEET_CSV_URL)
        res.encoding = 'utf-8'
        sheet_df = pd.read_csv(io.StringIO(res.text), dtype=str)
        
        for _, row in sheet_df.iterrows():
            name = str(row["名稱"]).strip()
            if name == 'nan' or not name or name in existing_names: continue
            
            addr, boss, intro = str(row["地址"]).strip(), str(row["負責人"]).strip(), str(row["簡介"]).strip()
            phone = str(row.get("電話", "無")).strip()
            fax = str(row.get("傳真", "無")).strip()
            
            lat, lon = get_default_coords(name + addr)
            if addr != 'nan' and addr:
                try:
                    location = geolocator.geocode(addr, timeout=3)
                    if location: lat, lon = location.latitude, location.longitude
                except: pass
            
            final_data.append({
                "名稱": name, "負責人": boss if boss != 'nan' else "未提供",
                "電話": phone if phone != 'nan' else "無", "傳真": fax if fax != 'nan' else "無",
                "地址": addr if addr != 'nan' else "未提供", "緯度": lat, "經度": lon,
                "簡介": intro if intro != 'nan' else "試算表補充據點"
            })
    except Exception as e: print(f"⚠️ 雲端試算表讀取失敗: {e}")

    with open("clan_data.py", "w", encoding="utf-8") as f:
        f.write("import pandas as pd\n\ndef get_clan_data():\n")
        f.write(f"    data = {final_data}\n    return pd.DataFrame(data)\n")

if __name__ == "__main__":
    df_new = fetch_and_clean_all()
    add_gps_and_save(df_new)
