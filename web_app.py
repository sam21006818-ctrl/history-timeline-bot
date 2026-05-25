import streamlit as st
import pandas as pd
import pydeck as pdk

# 網頁基本設定
st.set_page_config(page_title="全台謝氏宗親會互動地圖", page_icon="⛩️", layout="wide")
st.title("⛩️ 全台謝氏宗親會互動地圖")
st.markdown("請將滑鼠游標移至地圖上的 **橘色圓點**，即可自動查看該地區的宗親會詳細資訊！")
st.markdown("---")

# 嘗試讀取抓下來的資料，如果沒有就用預設資料
try:
    from clan_data import get_clan_data
    df = get_clan_data()
except:
    data = [
        {"名稱": "世界謝氏宗親總會", "負責人": "謝宗翰", "地址": "台北市中山區吉林路286號", "緯度": 25.0645, "經度": 121.5295, "簡介": "全國性宗親總會"}
    ]
    df = pd.DataFrame(data)

# 🚀 建立滑鼠可互動的地圖圖層
layer = pdk.Layer(
    "ScatterplotLayer",
    df,
    pickable=True,
    opacity=0.8,
    stroked=True,
    filled=True,
    radius_scale=6,
    radius_min_pixels=12,
    radius_max_pixels=30,
    get_position="[經度, 緯度]",
    get_fill_color="[255, 140, 0]",
    get_line_color=[255, 255, 255],
)

# 設定地圖一開始看的位子 (鎖定台灣中心點)
view_state = pdk.ViewState(
    latitude=23.7,
    longitude=121.0,
    zoom=6.5,
    pitch=0
)

# 🚀 畫出地圖，並設定滑鼠移過去彈出的資訊卡 (Tooltip)
st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={
        "html": """
            <div style="font-family: sans-serif; padding: 5px;">
                <b style="font-size: 16px; color: #FF8C00;">⛩️ {名稱}</b><br/>
                <b>👨‍💼 負責人：</b> {負責人}<br/>
                <b>🏠 地址：</b> {地址}<br/>
                <hr style="margin: 5px 0; border: 0.5px solid #ccc;"/>
                <span style="font-size: 12px; color: #ddd;">{簡介}</span>
            </div>
        """,
        "style": {
            "backgroundColor": "#222222", 
            "color": "white",
            "borderRadius": "8px"
        }
    }
))
