import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import wikipedia
import re
import textwrap
import zhconv

# 設定自定義識別身分以防 API 封鎖
wikipedia.set_user_agent("HistoryTimelineBot/1.0 (contact@example.com)")
wikipedia.set_lang("zh")

st.set_page_config(page_title="全自動華人歷史掃描器", page_icon="📡", layout="wide")
st.title("📡 全自動華人歷史生平掃描器")
st.write("智庫級系統：已升級「華人名冊過濾盾」，全自動剔除外國人譯名雜訊。")

# ==========================================
# 記憶暫存器初始化
# ==========================================
if 'candidates' not in st.session_state:
    st.session_state['candidates'] = []
if 'current_keyword' not in st.session_state:
    st.session_state['current_keyword'] = ""
if 'direct_df' not in st.session_state:
    st.session_state['direct_df'] = None
if 'direct_person' not in st.session_state:
    st.session_state['direct_person'] = ""


# ==========================================
# 核心引擎：解析特定名人的生平資料
# ==========================================
def extract_timeline_data(exact_name):
    try:
        page = wikipedia.page(exact_name)
        raw_text = page.content
        text = zhconv.convert(raw_text, 'zh-tw')

        sentences = text.split('。')
        extracted_events = []

        for sentence in sentences:
            if "==" in sentence or "外部連結" in sentence or "參考資料" in sentence:
                continue

            match = re.search(r'(\d+)年', sentence)
            if match:
                year = int(match.group(1))
                if 1 <= year <= 2100:
                    clean_event = sentence.replace('\n', '').strip()
                    if len(clean_event) > 10:
                        extracted_events.append({"年份": year, "事件": clean_event})

        df = pd.DataFrame(extracted_events)
        if not df.empty:
            df = df.drop_duplicates(subset=['年份']).sort_values(by='年份')
            return df
        return None
    except Exception:
        return None


# ==========================================
# 視覺化渲染引擎
# ==========================================
def render_timeline(df, person_name):
    st.success(f"✅ 成功提取 【{person_name}】 {len(df)} 筆關鍵歷史紀錄！")

    # ------ 樹枝圖繪圖引擎 ------
    df['顯示年份'] = df['年份'].astype(str)

    heights = []
    for i in range(len(df)):
        if i % 4 == 0:
            heights.append(0.8)
        elif i % 4 == 1:
            heights.append(-0.8)
        elif i % 4 == 2:
            heights.append(1.6)
        else:
            heights.append(-1.6)
    df['高度'] = heights

    def wrap_hover_text(text, width=35):
        return "<br>".join(textwrap.wrap(text, width=width))

    df['智慧提示文字'] = df.apply(lambda r: f"<b>📅 {r['顯示年份']}年 重要紀事</b><br>{wrap_hover_text(r['事件'])}", axis=1)

    dynamic_width = max(1000, len(df) * 120)

    fig = go.Figure()

    # A. 主幹中心線
    fig.add_trace(go.Scatter(
        x=df['顯示年份'], y=[0] * len(df),
        mode='lines', line=dict(color='#718096', width=4),
        showlegend=False, hoverinfo='skip'
    ))

    # B. 垂直小樹枝引線
    for index, row in df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row['顯示年份'], row['顯示年份']], y=[0, row['高度']],
            mode='lines', line=dict(color='#A0AEC0', width=2),
            showlegend=False, hoverinfo='skip'
        ))

    # C. 樹枝末端節點
    fig.add_trace(go.Scatter(
        x=df['顯示年份'], y=df['高度'], mode='markers+text',
        text="<b>" + df['顯示年份'] + "</b>",
        textposition=["top center" if h > 0 else "bottom center" for h in df['高度']],
        textfont=dict(size=14, color='#2D3748'),
        marker=dict(size=13, color='#DD6B20', line=dict(color='white', width=2)),
        hovertext=df['智慧提示文字'], hoverinfo="text", showlegend=False
    ))

    # D. 圖表整體版面美化
    fig.update_layout(
        title=dict(text=f"🌿 【{person_name}】生平軌跡樹枝時間軸", font=dict(size=22)),
        xaxis=dict(showgrid=False, zeroline=False, ticks="", title="歷史事件發展順序（支援左右滑動瀏覽）"),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-2.5, 2.5]),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='#F7FAFC',
        width=dynamic_width, height=530, margin=dict(l=50, r=50, t=60, b=50)
    )

    st.plotly_chart(fig, use_container_width=False)

    # ------ 智慧字卡閱讀模式 ------
    st.markdown("### 📄 歷史事件明細 (智慧字卡閱讀模式)")
    for index, row in df.iterrows():
        st.markdown(f"""
        <div style="background-color: #FFFFFF; padding: 20px; border-radius: 8px; margin-bottom: 15px; border-left: 6px solid #DD6B20; box-shadow: 0px 2px 8px rgba(0,0,0,0.06);">
            <span style="font-weight: bold; color: #DD6B20; font-size: 17px; display: block; margin-bottom: 5px;">📅 {row['年份']} 年</span>
            <p style="margin: 0; font-size: 15px; color: #333333; line-height: 1.7; white-space: normal; overflow-wrap: break-word; word-wrap: break-word;">
                {row['事件']}
            </p>
        </div>
        """, unsafe_allow_html=True)


# ==========================================
# 第一階段介面：關鍵字輸入 Form
# ==========================================
st.markdown("### 🔍 輸入名人姓名")
with st.form("keyword_form"):
    keyword_input = st.text_input("請輸入華人姓名或關鍵字：", value="謝")
    search_submit = st.form_submit_button("🚀 開始全自動掃描")

if search_submit:
    if keyword_input.strip():
        # 初始化清空舊狀態
        st.session_state['candidates'] = []
        st.session_state['direct_df'] = None
        st.session_state['direct_person'] = ""

        with st.spinner("🔮 智慧大腦正在進行華人血統特徵分析..."):
            is_direct_success = False
            clean_keyword = keyword_input.strip()

            # 軌道一：【直達車檢驗】
            if len(clean_keyword) > 1:
                try:
                    direct_page = wikipedia.page(clean_keyword)
                    direct_title = zhconv.convert(direct_page.title, 'zh-tw')

                    if (clean_keyword in direct_title) or (direct_title in clean_keyword):
                        # 直達車防線：標題含有間隔號的外國譯名直接拒絕直達
                        if not any(b in direct_title for b in ["姓", "列表", "消歧義", "空間", "定理", "·", "•"]):
                            df_direct = extract_timeline_data(direct_page.title)
                            if df_direct is not None and not df_direct.empty:
                                st.session_state['direct_df'] = df_direct
                                st.session_state['direct_person'] = direct_title
                                is_direct_success = True
                except Exception:
                    pass

            # 軌道二：【智慧候選選單】
            if not is_direct_success:
                try:
                    raw_results = wikipedia.search(clean_keyword, results=25)
                    if raw_results:
                        filtered_results = []
                        for r in raw_results:
                            tr_title = zhconv.convert(r, 'zh-tw')

                            # 🚀【新增過濾盾】黑名單中直接加入中譯間隔號「·」與「•」
                            blacklist = [
                                "姓", "案", "列表", "模組", "消歧義", "將軍",
                                "空間", "定理", "公式", "效應", "函數", "主義",
                                "假說", "係數", "常數", "條約", "法案", "制度",
                                "車站", "公司", "組織", "大學", "學派", "學科",
                                "·", "•"
                            ]
                            if any(b in tr_title for b in blacklist):
                                continue

                            if any(char in tr_title for char in clean_keyword if char.isalpha()):
                                filtered_results.append(tr_title)

                        if filtered_results:
                            st.session_state['candidates'] = filtered_results
                            st.session_state['current_keyword'] = clean_keyword
                        else:
                            st.error(f"❌ 找不到與「{clean_keyword}」相關的華人歷史名人，請檢查是否輸入錯誤。")
                    else:
                        st.error(f"❌ 網路數據庫找不到與「{clean_keyword}」相符的結果。")
                except Exception as e:
                    st.error(f"連線中斷：{e}")

# ==========================================
# 畫面呈現邏輯 (雙軌分流呈現)
# ==========================================

# 軌道一呈現
if st.session_state['direct_df'] is not None:
    st.markdown("---")
    render_timeline(st.session_state['direct_df'], st.session_state['direct_person'])

# 軌道二呈現
elif st.session_state['candidates']:
    st.markdown("---")
    st.markdown("### 🎯 智慧提示：名稱不夠精確，請選擇目標對象")

    with st.form("person_select_form"):
        chosen_person = st.selectbox(
            f"系統已自動剔除外國譯名與學術概念，以下為與「{st.session_state['current_keyword']}」相關的有效華人名單：",
            st.session_state['candidates']
        )
        draw_submit = st.form_submit_button("🌿 確定對象，生成歷史畫卷")

    if draw_submit:
        with st.spinner(f"系統正在全自動建構【{chosen_person}】的智慧樹枝圖表與字卡..."):
            df = extract_timeline_data(chosen_person)
            if df is not None and not df.empty:
                render_timeline(df, chosen_person)
            else:
                st.warning(f"【{chosen_person}】的條目中缺乏明確帶有數字年份的生平事件紀錄。")