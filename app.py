import streamlit as st
import pandas as pd

from core.google_api import open_sheet

# ==============================
# 頁面設定
# ==============================

st.set_page_config(
    page_title="獎懲查詢系統",
    page_icon="📋",
    layout="wide"
)

# ==============================
# Google 試算表設定
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
# 欄位名稱處理
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


def clean_text(value):
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if text.lower() in ["nan", "none"]:
        return ""

    return text


# ==============================
# 讀取 Google Sheet
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

    # 清除每個儲存格前後空白
    for col in df.columns:
        df[col] = df[col].apply(clean_text)

    # 移除完全空白列
    df = df[
        df.astype(str)
        .apply(lambda row: "".join(row).strip(), axis=1) != ""
    ]

    # 移除沒有學號的列
    if "學號" in df.columns:
        df["學號"] = df["學號"].astype(str).str.strip()
        df = df[df["學號"] != ""]

    return df


# ==============================
# 統計數量
# ==============================

def calculate_total_quantity(result):
    if "數量" not in result.columns:
        return 0

    quantity = pd.to_numeric(
        result["數量"],
        errors="coerce"
    ).fillna(0)

    return int(quantity.sum())


def calculate_reward_punish_count(result):
    reward_count = 0
    punish_count = 0

    if "獎懲" not in result.columns:
        return reward_count, punish_count

    reward_keywords = ["獎", "嘉獎", "記功", "表揚"]
    punish_keywords = ["懲", "申誡", "警告", "記過", "扣點"]

    for value in result["獎懲"].astype(str):
        text = value.strip()

        if any(keyword in text for keyword in reward_keywords):
            reward_count += 1

        if any(keyword in text for keyword in punish_keywords):
            punish_count += 1

    return reward_count, punish_count


# ==============================
# 頁面內容
# ==============================

st.title("📋 獎懲查詢系統")

st.write("請選擇學期，並輸入學號查詢個人獎懲紀錄。")

semester = st.selectbox(
    "請選擇學期",
    ["上學期", "下學期"]
)

student_id = st.text_input(
    "請輸入學號",
    placeholder="例如：D1114241034"
)

if student_id.strip() == "":
    st.info("請先輸入學號後查詢。")
    st.stop()


# ==============================
# 載入資料
# ==============================

url = SEMESTER_SHEETS[semester]["url"]

try:
    df = load_reward_data(url)

except Exception as e:
    st.error("讀取 Google 試算表失敗，請確認工作表名稱、分享權限或 Secrets 設定。")
    st.exception(e)
    st.stop()


if df.empty:
    st.warning("目前試算表沒有資料。")
    st.stop()


# ==============================
# 檢查欄位
# ==============================

missing_columns = [
    col for col in DISPLAY_COLUMNS
    if col not in df.columns
]

if missing_columns:
    st.error(f"Google 試算表缺少欄位：{', '.join(missing_columns)}")
    st.write("目前讀到的欄位有：")
    st.write(list(df.columns))
    st.stop()


# ==============================
# 查詢學號
# ==============================

student_id = student_id.strip().upper()

df["學號"] = df["學號"].astype(str).str.strip().str.upper()

result = df[df["學號"] == student_id]

if result.empty:
    st.warning("查無此學號的獎懲資料。")
    st.stop()


# ==============================
# 整理查詢結果
# ==============================

result = result[DISPLAY_COLUMNS].copy()

# 日期格式整理
if "日期" in result.columns:
    result["日期"] = result["日期"].astype(str).str.strip()

# 數量轉數字
result["數量_數字"] = pd.to_numeric(
    result["數量"],
    errors="coerce"
).fillna(0)

total_records = len(result)
total_quantity = int(result["數量_數字"].sum())
reward_count, punish_count = calculate_reward_punish_count(result)

display_result = result[DISPLAY_COLUMNS].copy()


# ==============================
# 顯示結果
# ==============================

st.success(f"查詢成功，共找到 {total_records} 筆紀錄。")

st.subheader("📊 獎懲統計")

col1, col2, col3, col4 = st.columns(4)

col1.metric("紀錄筆數", total_records)
col2.metric("獎懲總次數", total_quantity)
col3.metric("獎勵筆數", reward_count)
col4.metric("懲處筆數", punish_count)

st.subheader("📄 查詢結果")

st.dataframe(
    display_result,
    use_container_width=True,
    hide_index=True
)