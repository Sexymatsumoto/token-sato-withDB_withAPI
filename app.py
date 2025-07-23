import streamlit as st
import openai
import pandas as pd
import psycopg2  # Supabaseへの接続用
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=st.secrets["SUPABASE_HOST"],
        port=st.secrets["SUPABASE_PORT"],
        dbname=st.secrets["SUPABASE_DB"],
        user=st.secrets["SUPABASE_USER"],
        password=st.secrets["SUPABASE_PASSWORD"]
    )
except Exception as e:
    st.error(f"接続エラー: {e}")
    st.stop()

# 1. UI（Streamlit）
period = st.selectbox("時代", ["すべて", "江戸", "室町", "鎌倉"])
country = st.selectbox("国", ["すべて", "山城", "備前", "薩摩"])
length = st.slider("刃長（±cm）", 0.0, 10.0, 2.0)

# 2. SQL生成 → Supabaseに問い合わせ
cursor = conn.cursor()
sql = f"""SELECT * FROM swords WHERE
    (時代 = '{period}' OR '{period}' = 'すべて') AND
    (国 = '{country}' OR '{country}' = 'すべて') AND
    ABS(刃長 - 63.5) <= {length}
    LIMIT 10;
"""
cursor.execute(sql)
results = cursor.fetchall()

# 3. ChatGPT APIへ投げる用プロンプト整形
prompt = "以下の刀剣について表形式で所見と概要を表示してください：\n"
for row in results:
    prompt += f"No: {row[0]}\n銘文: {row[1]}\n概要: {row[2]}\n所見: {row[3]}\n\n"

# 4. GPT呼び出し
openai.api_key = st.secrets["OPENAI_API_KEY"]
response = openai.ChatCompletion.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "あなたは刀剣の専門家です"},
        {"role": "user", "content": prompt}
    ]
)

# 5. 出力表示
st.markdown(response['choices'][0]['message']['content'])
