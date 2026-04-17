import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import qrcode
from io import BytesIO

# --- CONFIG ---
st.set_page_config(page_title="DecubiTech Pro", layout="wide")

# --- BANCO SQLITE ---
conn = sqlite3.connect("pacientes.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS pacientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    leito TEXT,
    risco TEXT,
    ultima TEXT,
    proxima TEXT,
    status TEXT,
    atraso_min INTEGER
)
""")
conn.commit()

# --- FUNÇÃO QR ---
def gerar_qrcode(data):
    qr = qrcode.make(data)
    buf = BytesIO()
    qr.save(buf)
    return buf.getvalue()

# --- ADICIONAR PACIENTE ---
def adicionar_paciente(nome, leito, risco):
    agora = datetime.now()
    proxima = agora + timedelta(hours=2)

    c.execute("""
    INSERT INTO pacientes (nome, leito, risco, ultima, proxima, status, atraso_min)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        nome,
        leito,
        risco,
        agora.strftime("%H:%M"),
        proxima.strftime("%H:%M"),
        "🟢 EM DIA",
        0
    ))
    conn.commit()

# --- BUSCAR PACIENTES ---
def get_pacientes():
    return pd.read_sql("SELECT * FROM pacientes", conn)

# --- BUSCAR POR ID ---
def get_paciente_id(pid):
    df = pd.read_sql(f"SELECT * FROM pacientes WHERE id={pid}", conn)
    return df.iloc[0] if not df.empty else None

# --- SIDEBAR ---
st.sidebar.title("➕ Adicionar Paciente")

nome = st.sidebar.text_input("Nome")
leito = st.sidebar.text_input("Leito")
risco = st.sidebar.selectbox("Risco", ["Baixo", "Médio", "Alto"])

if st.sidebar.button("Salvar"):
    if nome and leito:
        adicionar_paciente(nome, leito, risco)
        st.sidebar.success("Salvo!")
    else:
        st.sidebar.error("Preencha tudo")

# --- VER SE VEIO PELO QR ---
query = st.query_params

if "paciente_id" in query:
    pid = query["paciente_id"]
    p = get_paciente_id(pid)

    if p is not None:
        st.title(f"📱 Acesso via QR - {p['nome']}")

        st.write(f"Leito: {p['leito']}")
        st.write(f"Risco: {p['risco']}")
        st.write(f"Última: {p['ultima']}")
        st.write(f"Próxima: {p['proxima']}")

        tipo = st.radio("Novo decúbito:", ["Dorsal", "Lateral Direito", "Lateral Esquerdo"])

        if st.button("Confirmar pelo celular"):
            c.execute(f"""
            UPDATE pacientes 
            SET ultima='{datetime.now().strftime("%H:%M")}'
            WHERE id={pid}
            """)
            conn.commit()

            st.success("Atualizado via QR!")
            st.balloons()

    else:
        st.error("Paciente não encontrado")

    st.stop()

# --- DASHBOARD NORMAL ---
st.title("🛏️ DecubiTech PRO")

df = get_pacientes()

cols = st.columns(3)

for i, row in df.iterrows():
    with cols[i % 3]:
        st.markdown(f"""
        <div style="padding:20px;border-radius:10px;background:white">
            <h3>Leito {row['leito']} - {row['nome']}</h3>
            <p>Risco: {row['risco']}</p>
            <p>Status: {row['status']}</p>
        </div>
        """, unsafe_allow_html=True)

        # LINK DO QR
        link = f"http://localhost:8501/?paciente_id={row['id']}"

        qr_img = gerar_qrcode(link)
        st.image(qr_img, caption="Escanear")

        st.code(link)

        if st.button("Ver", key=row["id"]):
            st.session_state.sel = row

# --- DETALHES ---
if "sel" in st.session_state:
    p = st.session_state.sel

    st.header(f"📋 {p['nome']}")

    st.write(f"Leito: {p['leito']}")
    st.write(f"Risco: {p['risco']}")

    tipo = st.radio("Decúbito:", ["Dorsal", "Lateral Direito", "Lateral Esquerdo"])

    if st.button("Confirmar"):
        c.execute(f"""
        UPDATE pacientes 
        SET ultima='{datetime.now().strftime("%H:%M")}'
        WHERE id={p['id']}
        """)
        conn.commit()

        st.success("Atualizado!")
        st.rerun()