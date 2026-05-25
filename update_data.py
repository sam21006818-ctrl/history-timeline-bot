import pandas as pd
import requests
import io
import time
from geopy.geocoders import Nominatim

def fetch_and_clean_all():
    print("🔄 步驟 1：正在巡邏全台政府開放平台下載名冊...")
    
    # 全台主要縣市與內政部 CSV 網址整合清單 (已預設加入 6 個主要指標性資料庫)
    target_urls = [
        # 內政部 (全國性團體)
        "https://data.moi.gov.tw/MoiOD/System/DownloadFile.aspx?DATA=C634AF01-D330-41CA-B303-3C53C5DDE7DC",
        # 台北市
        "https://data.taipei/api/dataset/84df12a5-b1a9-4d6d-8b6b-853406f5223e/resource/123/download",
        # 新北市
        "https://data.ntpc.gov.tw/api/datasets/6D202863-7DA9-4A7B-9BA5-776AB1B2B72E/csv/file",
        # 台中市
        "https://datacenter.taichung.gov.tw/swagger/OpenData/e75c60e3-463d-4c37-a164-90ff66041695",
        # 台南市
        "https://data.tainan.gov.tw/dataset/e63b6528-6625-46eb-8e56-11f879e6027a/resource/11/download",
        # 屏東縣
        "https://www.pthg.gov.tw/planib/OpenData_Download.aspx?n=6E78FA6BD6603FBE&sms=96489379D5BD0818"
    ]
    
    all_clan_data = pd.DataFrame()
    name_col_to_use = "名稱"
    
    for url in target_urls:
        try:
            response = requests.get(url, timeout=30)
            response.encoding = 'utf-8' # 確保中文不亂碼
            df_gov = pd.read_csv(io.StringIO(response.text))
            
            # 自動辨識該縣市的名稱欄位寫法
            name_col = 'name' if 'name' in df_gov.columns else (
                       '團體名稱' if '團體名稱' in df_gov.columns else df_gov.columns[0])
            
            # 篩選名稱中包含謝氏宗親的資料
            df_clan = df_gov[df_gov[name_col].astype(str).str.contains("謝氏|謝姓|寶樹", na=False)].copy()
            
            if not df_clan.empty:
                # 統一名稱欄位
                df_clan.rename(columns={name_col: name_col_to_use}, inplace=True)
                
                # 自動辨識該縣市的地址欄位寫法，並統一改為「地址」
                addr_col = 'address' if 'address' in df_clan.columns else (
                           '會址' if '會址' in df_clan.columns else (
                           '通訊地址' if '通訊地址' in df_clan.columns else df_clan.columns[1]))
                df_clan.rename(columns={addr_col: "地址"}, inplace=True)
                
                # 將此縣市的資料合併進總資料庫
                all_clan_data = pd.concat([all_clan_data, df_clan], ignore_index=True)
                
            print(f"✅ 成功下載並清洗一筆清單，目前累積 {len(all_clan_data)} 筆。")
            time.sleep(1) # 暫停 1 秒避免對政府伺服器造成過大負擔
        except Exception as e:
            print(f"⚠️ 某網址失效或維護中，自動跳過。")
            continue

    return all_clan_data

def add_gps_and_save(df):
    final_data = []
    if df is None or df.empty:
        print("❌ 找不到資料，寫入系統預設值。")
        final_data = [{"名稱": "世界謝氏宗親總會", "負責人": "依政府名冊登記", "電話": "暫無", "地址": "台北市", "緯度": 25.0518, "經度": 121.5332, "簡介": "預設資料"}]
    else:
        print("🔄 步驟 2：正在將全台地址轉換為地圖經緯度座標...")
        geolocator = Nominatim(user_agent="my_clan_bot")
        for _, row in df.iterrows():
            addr = str(row["地址"])
            try:
                # 請求免費地圖伺服器轉換經緯度
                location = geolocator.geocode(addr, timeout=5)
                lat, lon = (location.latitude, location.longitude) if location else (23.6, 121.0)
                time.sleep(1)
            except:
                lat, lon = (23.6, 121.0) # 若地址無法辨識，給予台灣中心點座標
                
            final_data.append({
                "名稱": str(row["名稱"]),
                "負責人": "依政府名冊登記",
                "電話": "暫無",
                "地址": addr,
                "緯度": lat,
                "經度": lon,
                "簡介": "資料來源：各縣市政府與內政部開放資料平台自動同步。"
            })
            
    # 將處理完畢的全台資料覆蓋寫入 clan_data.py
    print("🔄 步驟 3：正在覆蓋寫入資料庫...")
    with open("clan_data.py", "w", encoding="utf-8") as f:
        f.write("import pandas as pd\n\n")
        f.write("def get_clan_data():\n")
        f.write(f"    data = {final_data}\n")
        f.write("    return pd.DataFrame(data)\n")
    print("🎉 【大功告成】全台資料更新完畢！")

if __name__ == "__main__":
    df_new = fetch_and_clean_all()
    add_gps_and_save(df_new)
