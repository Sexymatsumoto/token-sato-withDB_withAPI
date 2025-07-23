import streamlit as st
import pandas as pd
import os
import psycopg2
import openai

try:
    conn = psycopg2.connect(
        host=st.secrets["SUPABASE_HOST"],
        port=int(st.secrets["SUPABASE_PORT"]),
        dbname=st.secrets["SUPABASE_DB"],
        user=st.secrets["SUPABASE_USER"],
        password=st.secrets["SUPABASE_PASSWORD"]
    )
except Exception as e:
    st.error("接続エラーです。st.secretsの値をご確認ください。")
    st.text(str(e))  # ←伏せられてないローカルで実行すれば表示される
    st.stop()

# 1. UI（Streamlit）
period = st.selectbox("時代", ["すべて", "江戸", "室町", "鎌倉"])
country = st.selectbox("国", ["すべて", "山城", "備前", "薩摩"])
base_length = st.slider("刃長の基準値（cm）", 30.0, 100.0, 63.5, step=0.1)

# 2. SQL生成 → Supabaseに問い合わせ
cursor = conn.cursor()

conditions = []

if period != "すべて":
    conditions.append(f""""時代" LIKE '%{period}%'""")

if country != "すべて":
    conditions.append(f""""国" LIKE '%{country}%'""")
    
conditions.append(f""""刃長"::float BETWEEN {base_length - 5} AND {base_length + 5}""")
where_clause = " AND ".join(conditions)

sql = f"""
    SELECT * FROM swords
    WHERE {where_clause}
    LIMIT 10;
"""
cursor.execute(sql)


#sql = f"""SELECT * FROM swords WHERE 
#    "時代" LIKE '%{period}%' AND
#    "国" LIKE '%{country}%' AND
#    "刃長"::float BETWEEN {base_length - 10} AND {base_length + 10}
#    LIMIT 10;
#"""
#cursor.execute(sql)
results = cursor.fetchall()

# 3. ChatGPT APIへ投げる用プロンプト整形
prompt = "以下の刀剣について表形式で所見と概要を表示してください：\n"
for row in results:
    prompt += f"No: {row[0]}\n銘文: {row[1]}\n概要: {row[2]}\n所見: {row[3]}\n\n"

# 4. GPT呼び出し
openai.api_key = st.secrets["OPENAI_API_KEY"]

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "あなたは刀剣の専門家です"},
        {"role": "user", "content": prompt}
    ]
)

# client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

#response = client.chat.completions.create(
#    model="gpt-4o",
#    messages=[
#        {"role": "system", "content": "あなたは刀剣の専門家です"},
#        {"role": "user", "content": prompt}
#    ]
#)

st.markdown(response.choices[0].message.content)
