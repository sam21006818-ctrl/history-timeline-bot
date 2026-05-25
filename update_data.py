import pandas as pd
import requests
import io
import time
from geopy.geocoders import Nominatim

def fetch_and_clean_all():
    print("🔄 嘗試連線至內政部與各縣市政府資料庫...")
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
                    
                    clean_df = pd.DataFrame({
                        "名稱": df_clan[name_col],
                        "地址": df_clan[addr_col],
                        "負責人": df_clan[leader_col] if leader_col else "未提供",
                        "電話": df_clan[phone_col] if phone_col else "未提供"
                    })
                    all_clan_data = pd.concat([all_clan_data, clean_df], ignore_index=True)
        except:
            pass
    return all_clan_data

def add_gps_and_save(df):
    # 👑 預設的7筆全國精選資料，當作地圖的「基本盤」
    final_data = [
        {"名稱": "世界謝氏宗親總會", "負責人": "依名冊登記", "電話": "未提供", "地址": "台北市中山區吉林路286號", "緯度": 25.0645, "經度": 121.5295, "簡介": "全國性宗親總會"},
        {"名稱": "新北市謝氏宗親會", "負責人": "依名冊登記", "電話": "未提供", "地址": "新北市板橋區中正路", "緯度": 25.0160, "經度": 121.4550, "簡介": "新北地區宗親聯誼會"},
        {"名稱": "桃園市謝氏宗親會", "負責人": "依名冊登記", "電話": "未提供", "地址": "桃園市桃園區三民路", "緯度": 24.9930, "經度": 121.3140, "簡介": "桃園地區宗親聯誼會"},
        {"名稱": "台中市謝氏宗親會", "負責人": "依名冊登記", "電話": "未提供", "地址": "台中市西區民生路", "緯度": 24.1415, "經度": 120.6750, "簡介": "台中地區宗親聯誼會"},
        {"名稱": "台南市謝氏宗親會", "負責人": "依名冊登記", "電話": "未提供", "地址": "台南市中西區民族路", "緯度": 22.9970, "經度": 120.2030, "簡介": "台南地區宗親聯誼會"},
        {"名稱": "高雄市謝氏宗親會", "負責人": "依名冊登記", "電話": "未提供", "地址": "高雄市苓雅區建國一路", "緯度": 22.6320, "經度": 120.3200, "簡介": "高雄地區宗親聯誼會"},
        {"名稱": "花蓮縣謝氏宗親會", "負責人": "依名冊登記", "電話": "未提供", "地址": "花蓮縣花蓮市中山路", "緯度": 23.9880, "經度": 121.6020, "簡介": "東部地區宗親聯誼會"}
    ]

    # 記錄已經在基本盤裡的名字，避免重複顯示
    existing_names = [item["名稱"] for item in final_data]

    # 如果有抓到新資料，就把它們疊加進去
    if df is not None and not df.empty:
        print("🔄 正在轉換政府最新資料的經緯度...")
        geolocator = Nominatim(user_agent="my_xie_bot_2026")
        for _, row in df.iterrows():
            name = str(row["名稱"]).strip()
            
            # 如果名字已經在基本盤裡，或是名字是空的，就跳過
            if name in existing_names or name == 'nan': 
                continue
                
            addr = str(row["地址"]).strip()
            boss = str(row["負責人"]).strip()
            phone = str(row["電話"]).strip()
            
            # 預設經緯度 (如果地圖辨識不出地址，就先把它丟到台灣中間)
            lat, lon = 23.6, 120.9 
            
            if addr != 'nan' and addr:
                try:
                    location = geolocator.geocode(addr, timeout=3)
                    if location:
                        lat, lon = location.latitude, location.longitude
                    time.sleep(1)
                except:
                    pass # 如果地圖查不到，依然保留預設經緯度，不把資料丟掉
                    
            final_data.append({
                "名稱": name,
                "負責人": boss if boss != 'nan' else "未提供",
                "電話": phone if phone != 'nan' else "未提供",
                "地址": addr if addr != 'nan' else "未提供",
                "緯度": lat,
                "經度": lon,
                "簡介": "政府開放資料最新同步"
            })

    with open("clan_data.py", "w", encoding="utf-8") as f:
        f.write("import pandas as pd\n\n")
        f.write("def get_clan_data():\n")
        f.write(f"    data = {final_data}\n")
        f.write("    return pd.DataFrame(data)\n")
    print(f"🎉 檔案寫入完畢！共更新 {len(final_data)} 筆。")

if __name__ == "__main__":
    df_new = fetch_and_clean_all()
    add_gps_and_save(df_new)
