import streamlit as st
import pandas as pd

from core.google_api import open_sheet

# ======================
# 頁面設定
# ======================

st.set_page_config(
    page_title="獎懲查詢系統",
    page_icon="📋",
    layout="wide"
)

# ======================
# Google Sheet
# ======================

SEMESTER_SHEETS = {
    "上學期": {
        "url": "https://docs.google.com/spreadsheets/d/18FrgMjyb6bo0apiAKpOfTkr7fQQSQlbW6al8G6y_AYk/edit"
    },
    "下學期": {
        "url": "https://docs.google.com/spreadsheets/d/1kymMcZ7M69he0ZkE7pCQnbDsWJ4qawQdO730nUuHn3M/edit"
    }
}

DISPLAY_COLUMNS = [
    "學號",
    "日期",
    "獎懲詳細原因",
    "獎懲",
    "數量"
]

# ======================
# 欄位去重
# ======================

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

# ======================
# 讀取資料
# ======================

@st.cache_data(ttl=1800)
def load_reward_data(url):

    ss = open_sheet(url)

    ws = ss.sheet1

    values = ws.get_all_values()

    if len(values) <= 1:
        return pd.DataFrame()

    headers = make_unique_columns(values[0])

    df = pd.DataFrame(
        values[1:],
        columns=headers
    )

    df.columns = df.columns.str.strip()

    df = df.dropna(how="all")

    return df

# ======================
# 畫面
# ======================

st.title("📋 獎懲查詢系統")

st.write("請選擇學期並輸入學號查詢獎懲紀錄")

semester = st.selectbox(
    "選擇學期",
    ["上學期", "下學期"]
)

student_id = st.text_input(
    "請輸入學號",
    placeholder="例如 D1114241034"
)

# 一開始不顯示資料

if not student_id:
    st.info("請輸入學號後查詢")
    st.stop()

# ======================
# 讀資料
# ======================

url = SEMESTER_SHEETS[semester]["url"]

df = load_reward_data(url)

if df.empty:
    st.warning("查無資料")
    st.stop()

# ======================
# 檢查欄位
# ======================

missing = [
    col
    for col in DISPLAY_COLUMNS
    if col not in df.columns
]

if missing:
    st.error(
        f"缺少欄位：{', '.join(missing)}"
    )
    st.stop()

# ======================
# 查詢學號
# ======================

student_id = student_id.strip().upper()

result = df[
    df["學號"]
    .astype(str)
    .str.strip()
    .str.upper()
    == student_id
]

if result.empty:
    st.warning("查無此學號資料")
    st.stop()

# ======================
# 統計
# ======================

result = result[DISPLAY_COLUMNS].copy()

total_records = len(result)

quantity_series = pd.to_numeric(
    result["數量"],
    errors="coerce"
).fillna(0)

total_quantity = int(quantity_series.sum())

# ======================
# 顯示統計
# ======================

st.subheader("📊 獎懲統計")

col1, col2 = st.columns(2)

col1.metric(
    "獎懲紀錄筆數",
    total_records
)

col2.metric(
    "獎懲總次數",
    total_quantity
)

# ======================
# 顯示資料
# ======================

st.subheader("📄 查詢結果")

st.dataframe(
    result,
    use_container_width=True,
    hide_index=True
)