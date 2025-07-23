import streamlit as st
import pandas as pd
import os
import psycopg2
import openai 

# Supabase接続
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
    st.text(str(e))
    st.stop()
    
# --- 入力UI ---
period = st.selectbox("時代", ["すべて", "江戸", "室町", "鎌倉"])
country = st.selectbox("国", ["すべて", "山城", "備前", "薩摩"])
base_length = st.slider("刃長の基準値（cm）", 30.0, 100.0, 63.5, step=0.1)

# --- セッション状態でデータを一時保存 ---
if "results" not in st.session_state:
    st.session_state.results = []

# --- 検索ボタン ---
if st.button("この条件で検索"):
    cursor = conn.cursor()

    conditions = []

    if period != "すべて":
        conditions.append(f""""時代" LIKE '%{period}%'""")

    if country != "すべて":
        conditions.append(f""""国" LIKE '%{country}%'""")

    conditions.append(f""""刃長"::float BETWEEN {base_length - 5} AND {base_length + 5}""")

    where_clause = " AND ".join(conditions)

    sql = f"""
        SELECT "No.", "銘文", "概要", "所見" FROM swords
        WHERE {where_clause}
        LIMIT 10;
    """

    cursor.execute(sql)
    st.session_state.results = cursor.fetchall()

# --- 結果表示（検索済みのときのみ） ---
if st.session_state.results:
    # No列（1列目）を整数に変換して桁区切りなしで表示
#    df.iloc[:, 0] = df.iloc[:, 0].astype(int)
    
    df = pd.DataFrame(st.session_state.results, columns=["No.", "銘文", "概要", "所見"])
    # No列の桁区切り（カンマ）を除去してから整数化（エラーを防ぐ）
    df["No"] = df["No"].astype(str).str.replace(",", "").astype(int)
    st.dataframe(df)

    # --- GPTに送るボタン ---
    if st.button("ChatGPTに所見と概要を要約してもらう"):
        prompt = "以下の刀剣について表形式で所見と概要を表示してください：\n"
        for row in st.session_state.results:
            prompt += f"No: {row[0]}\n銘文: {row[1]}\n概要: {row[2]}\n所見: {row[3]}\n\n"

        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは刀剣の専門家です"},
                {"role": "user", "content": prompt}
            ]
        )

        st.markdown(response.choices[0].message.content)
