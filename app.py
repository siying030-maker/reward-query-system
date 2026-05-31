import streamlit as st
import pandas as pd

from datetime import datetime

from core.google_api import open_sheet

# ==============================
# 頁面設定
# ==============================

st.markdown("""
<div class="custom-title">
📋 獎懲查詢系統
</div>
""", unsafe_allow_html=True)

# ==============================
# 手機版優化
# ==============================

st.markdown("""
<style>

/* 頁面邊距 */
.block-container{
    padding-top:4rem;
    padding-bottom:1rem;
    padding-left:1rem;
    padding-right:1rem;
}

/* 自訂標題 */
.custom-title{
    font-size:2.3rem;
    font-weight:700;
    margin-bottom:1rem;
}

/* 查詢按鈕 */
.stButton > button,
.stFormSubmitButton > button{
    height:50px;
    font-size:18px;
    font-weight:bold;
    border-radius:12px;
}

/* Metric卡片 */
[data-testid="metric-container"]{
    text-align:center;
    border-radius:12px;
    padding:15px;
    background-color:#f8f9fa;
}

/* DataFrame字體 */
[data-testid="stDataFrame"]{
    font-size:14px;
}

/* 手機版 */
@media (max-width:768px){

    .block-container{
        padding-top:4rem !important;
        padding-left:0.5rem;
        padding-right:0.5rem;
    }

    .custom-title{
        font-size:1.8rem;
    }

    [data-testid="metric-container"]{
        padding:10px;
    }

    .stFormSubmitButton > button{
        width:100%;
        height:55px;
        font-size:20px;
    }
}

</style>
""", unsafe_allow_html=True)

# ==============================
# 學期判斷表
# ==============================

SEMESTER_CONFIG_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "18tZv6d8Ja19ZZy5rPuIWMrB5c4NnMqbnwh9SegW-9-Y/edit"
)

SEMESTER_CONFIG_SHEET = "工作表1"

# ==============================
# 獎懲資料表
# ==============================

SEMESTER_SHEETS = {
    "上學期": {
        "url": "https://docs.google.com/spreadsheets/d/18FrgMjyb6bo0apiAKpOfTkr7fQQSQlbW6al8G6y_AYk/edit"
    },
    "下學期": {
        "url": "https://docs.google.com/spreadsheets/d/1kymMcZ7M69he0ZkE7pCQnbDsWJ4qawQdO730nUuHn3M/edit"
    }
}

TARGET_SHEET_NAME = "輸入_懲處_男女"

DISPLAY_COLUMNS = [
    "學號",
    "日期",
    "獎懲詳細原因",
    "獎懲",
    "數量"
]

# ==============================
# 欄位處理
# ==============================

def make_unique_columns(columns):

    result = []
    used = {}

    for i, col in enumerate(columns):

        col = str(col).strip()

        if col == "":
            col = f"空白欄位_{i}"

        if col in used:
            used[col] += 1
            col = f"{col}_{used[col]}"
        else:
            used[col] = 0

        result.append(col)

    return result

# ==============================
# 自動判斷學期
# ==============================

@st.cache_data(ttl=3600)
def get_current_semester():

    ss = open_sheet(SEMESTER_CONFIG_URL)

    ws = ss.worksheet(SEMESTER_CONFIG_SHEET)

    values = ws.get_all_records()

    today = datetime.now().date()

    for row in values:

        start_date = pd.to_datetime(
            row["開始日期"]
        ).date()

        end_date = pd.to_datetime(
            row["結束日期"]
        ).date()

        if start_date <= today <= end_date:
            return row["學期"]

    return None

# ==============================
# 讀取獎懲資料
# ==============================

@st.cache_data(ttl=1800)
def load_reward_data(url):

    ss = open_sheet(url)

    ws = ss.worksheet(TARGET_SHEET_NAME)

    values = ws.get_all_values()

    if len(values) <= 1:
        return pd.DataFrame()

    headers = make_unique_columns(values[0])

    df = pd.DataFrame(
        values[1:],
        columns=headers
    )

    df.columns = df.columns.astype(str).str.strip()

    df = df.dropna(how="all")

    if "學號" in df.columns:
        df["學號"] = df["學號"].astype(str).str.strip()
        df = df[df["學號"] != ""]

    return df

# ==============================
# 標題
# ==============================



semester = get_current_semester()

if semester is None:

    st.error(
        "目前日期不在任何學期區間內，請聯絡管理員。"
    )

    st.stop()

st.info(
    f"目前學期：{semester}"
)

# ==============================
# 查詢區
# ==============================

with st.form("query_form"):

    student_id = st.text_input(
        "請輸入學號",
        placeholder="例如：D1114241034"
    )

    search_btn = st.form_submit_button(
        "🔍 查詢",
        use_container_width=True
    )

if not search_btn:
    st.stop()

if student_id.strip() == "":
    st.warning("請輸入學號")
    st.stop()

# ==============================
# 讀取資料
# ==============================

url = SEMESTER_SHEETS[semester]["url"]

try:

    df = load_reward_data(url)

except Exception as e:

    st.error("Google 試算表讀取失敗")

    st.exception(e)

    st.stop()

if df.empty:

    st.warning("目前沒有資料")

    st.stop()

missing_columns = [
    col
    for col in DISPLAY_COLUMNS
    if col not in df.columns
]

if missing_columns:

    st.error(
        f"缺少欄位：{', '.join(missing_columns)}"
    )

    st.write("目前欄位：")

    st.write(list(df.columns))

    st.stop()

# ==============================
# 查詢
# ==============================

student_id = student_id.strip().upper()

df["學號"] = (
    df["學號"]
    .astype(str)
    .str.strip()
    .str.upper()
)

result = df[
    df["學號"] == student_id
]

if result.empty:

    st.warning("查無獎懲資料")

    st.stop()

result = result[DISPLAY_COLUMNS].copy()

total_records = len(result)

# ==============================
# 結果
# ==============================

st.success(
    f"查詢成功，共找到 {total_records} 筆紀錄。"
)

st.subheader("📊 查詢統計")

st.metric(
    "紀錄筆數",
    total_records
)

st.subheader("📄 查詢結果")

st.dataframe(
    result,
    use_container_width=True,
    hide_index=True
)

