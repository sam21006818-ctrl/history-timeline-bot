import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="全台謝氏宗親會互動地圖", page_icon="⛩️", layout="wide")
st.title("⛩️ 全台謝氏宗親會互動地圖")
st.markdown("請將滑鼠游標移至地圖上的 **橘色圓點**，即可自動查看該地區的宗親會詳細資訊！")
st.markdown("---")

try:
    from clan_data import get_clan_data
    df = get_clan_data()
except:
    df = pd.DataFrame([{"名稱": "系統更新中", "負責人": "稍後", "電話": "稍後", "傳真": "稍後", "地址": "讀取中...", "緯度": 23.6, "經度": 120.9, "簡介": "請稍候"}])

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

view_state = pdk.ViewState(latitude=23.7, longitude=121.0, zoom=6.5, pitch=0)

st.pydeck_chart(pdk.Deck(
    map_style="road",  # 💡 就是加了這一行！讓黑夜變成明亮的白晝街道圖
    layers=[layer],
    initial_view_state=view_state,
    tooltip={
        "html": """
            <div style="font-family: sans-serif; padding: 5px; line-height: 1.5;">
                <b style="font-size: 16px; color: #FF8C00;">⛩️ {名稱}</b><br/>
                <b>👨‍💼 負責人：</b> {負責人}<br/>
                <b>📞 電 話：</b> {電話}<br/>
                <b>📠 傳 真：</b> {傳真}<br/>
                <b>🏠 地 址：</b> {地址}<br/>
                <hr style="margin: 5px 0; border: 0.5px solid #ccc;"/>
                <span style="font-size: 12px; color: #ddd;">{簡介}</span>
            </div>
        """,
        "style": {"backgroundColor": "#222222", "color": "white", "borderRadius": "8px"}
    }
))
