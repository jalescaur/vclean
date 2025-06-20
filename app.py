import streamlit as st
import os
import tempfile
import zipfile
import time
import pandas as pd
from io import BytesIO
from pathlib import Path

# ==== seus módulos ====
from daily_posts import (
    process_and_export_excel    as process_publicacoes,
    add_analysis_column_and_export_txt as analysis_publicacoes
)
from news import (
    process_and_export_excel    as process_noticias,
    add_analysis_column_and_export_txt as analysis_noticias
)
from biweekly import full_pipeline     # biweekly.py

# ==== Configuração da página ====
st.set_page_config(
    page_title="📊 V-Tracker: Data Cleaning & Analysis",
    page_icon="📈",
    layout="wide"
)

# ==== CSS ====
st.markdown("""
<style>
    :root { --primary: #26619c; --secondary: #C5C6D0; }
    .stButton>button, .stDownloadButton>button {
        background-color: var(--primary) !important;
        color: white !important;
        border-radius: 8px; padding: 0.5em 1em; font-size: 16px;
    }
    .stFileUploader>div {
        background-color: var(--secondary) !important;
        padding: 1em !important;
        border: 1px solid var(--primary) !important;
        border-radius: 10px !important;
    }
    h1,h2,h3,h4,h5,h6 { color: var(--primary) !important; }
</style>
""", unsafe_allow_html=True)

# ==== Título geral ====
st.title("📊 V-Tracker: Data Cleaning & Analysis")

# ==== Abas ====
tab1, tab2, tab3 = st.tabs([
    "📱 Publicações", 
    "🗞️ Notícias", 
    "🗓️ Relatório Quinzenal"
])

with tab1:
    st.header("📱 Processamento de Publicações")
    uploaded_pub = st.file_uploader(
        "📂 Envie o Excel de Publicações",
        type=["xlsx"],
        key="upub"
    )
    if not uploaded_pub:
        st.info("⬆️ Por favor, envie um arquivo para iniciar.")
    else:
        if st.button("📊 Processar Publicações"):
            base = os.path.splitext(uploaded_pub.name)[0]
            file_clean    = f"{base}_cleaned.xlsx"
            file_ai       = f"{base}_ai.txt"
            file_corpus   = f"{base}_corpus.txt"

            # 1) Grava upload em temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(uploaded_pub.read())
                tmp_path = tmp.name

            # 2) Gera cleaned.xlsx
            df = process_publicacoes(tmp_path, output_filename=file_clean)

            # 3) Gera base_ai.txt
            analysis_publicacoes(df.copy(), txt_filename=file_ai)

            # 4) Renomeia o corpus default para base_corpus.txt
            old_iram = file_clean.replace(".xlsx", "_iramuteq.txt")
            if os.path.exists(old_iram):
                os.rename(old_iram, file_corpus)

            # 5) Limpa temporário
            os.remove(tmp_path)

            # 6) Empacota no ZIP
            excel_buf = BytesIO()
            df.to_excel(excel_buf, index=False)

            ai_buf    = BytesIO(open(file_ai,     "rb").read())
            corp_buf  = BytesIO(open(file_corpus, "rb").read())

            zp = BytesIO()
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
                z.writestr(file_clean,  excel_buf.getvalue())
                z.writestr(file_ai,     ai_buf.getvalue())
                z.writestr(file_corpus, corp_buf.getvalue())
            zp.seek(0)

            st.download_button(
                "📥 Baixar Resultados (Publicações)",
                data=zp.getvalue(),
                file_name=f"{base}_publicacoes.zip"
            )
            st.success("✅ Publicações processadas com sucesso!")

# === Aba 2: Notícias ===
with tab2:
    st.header("🗞️ Processamento de Notícias")
    uploaded_news = st.file_uploader(
        "📂 Envie o Excel de Notícias",
        type=["xlsx"],
        key="unews"
    )
    if not uploaded_news:
        st.info("⬆️ Por favor, envie um arquivo para iniciar.")
    else:
        if st.button("📊 Processar Notícias"):
            base = os.path.splitext(uploaded_news.name)[0]
            file_clean    = f"{base}_cleaned.xlsx"
            file_ai       = f"{base}_ai.txt"
            file_corpus   = f"{base}_corpus.txt"

            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(uploaded_news.read())
                tmp_path = tmp.name

            df = process_noticias(tmp_path, output_filename=file_clean)
            analysis_noticias(df.copy(), txt_filename=file_ai)

            old_iram = file_clean.replace(".xlsx", "_iramuteq.txt")
            if os.path.exists(old_iram):
                os.rename(old_iram, file_corpus)

            os.remove(tmp_path)

            excel_buf = BytesIO()
            df.to_excel(excel_buf, index=False)

            ai_buf    = BytesIO(open(file_ai,     "rb").read())
            corp_buf  = BytesIO(open(file_corpus, "rb").read())

            zp = BytesIO()
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
                z.writestr(file_clean,  excel_buf.getvalue())
                z.writestr(file_ai,     ai_buf.getvalue())
                z.writestr(file_corpus, corp_buf.getvalue())
            zp.seek(0)

            st.download_button(
                "📥 Baixar Resultados (Notícias)",
                data=zp.getvalue(),
                file_name=f"{base}_noticias.zip"
            )
            st.success("✅ Notícias processadas com sucesso!")

# === Aba 3: Relatório Quinzenal ===
with tab3:
    st.header("🗓️ Relatório Quinzenal")
    multitema = st.checkbox(
        "🔄 Análise multitemática?",
        help="Permitir repetir a mesma tag em vários macrotemas"
    )

    uploaded_bi = st.file_uploader(
        "📂 Envie o Excel para Relatório Quinzenal",
        type=["xlsx"],
        key="ubi"
    )
    if not uploaded_bi:
        st.info("⬆️ Por favor, envie um arquivo para iniciar.")
    else:
        base = os.path.splitext(uploaded_bi.name)[0]
        # armazena upload em arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(uploaded_bi.read())
            raw_path = tmp.name

        # tenta ler sheet Tags
        try:
            df_tags = pd.read_excel(raw_path, sheet_name="Tags", skiprows=4)
            all_tags = df_tags.columns.tolist()
        except:
            all_tags = []

        # inicializa session_state
        if "macros" not in st.session_state:
            st.session_state.macros = {i: [] for i in range(1, 5)}

        # para cada macrotema: 3/4 select + 1/4 botão confirm
        used = set()  # todas as tags confirmadas até o momento
        for i in range(1, 5):
            used = set().union(*[tags for idx, tags in st.session_state.macros.items() if idx < i]) \
                   if not multitema else set()
            choices = [t for t in all_tags if t not in used or t in st.session_state.macros[i]]

            col1, col2 = st.columns([3, 1])
            with col1:
                sel = st.multiselect(
                    f"Macrotema {i}", 
                    options=choices, 
                    default=st.session_state.macros[i],
                    key=f"sel_{i}"
                )
            with col2:
                if st.button(f"✅", key=f"confirm_{i}", help=f"Confirmar Macrotema {i}"):
                    st.session_state.macros[i] = sel
                    st.success(f"Macrotema {i} salvo: {', '.join(sel) or 'Nenhum'}")

        # botão final
        if st.button("📊 Gerar Relatório Quinzenal"):
            progress = st.progress(0, text="⏳ Processando dados…")
            for pct in (20, 50, 80):
                time.sleep(0.1)
                progress.progress(pct)

            file_clean    = f"{base}_cleaned.xlsx"
            file_ai       = f"{base}_ai.txt"
            file_iramuteq = f"{base}_corpus.txt"

            cleaned_path, macro_txts, iram_txt = full_pipeline(
                raw_filepath           = raw_path,
                macrotheme_definitions = st.session_state.macros,
                cleaned_output_filename= file_clean
            )

            # empacota tudo
            zp = BytesIO()
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
                z.writestr(file_clean, open(cleaned_path,    "rb").read())
                z.writestr(file_ai,    open(file_ai,       "rb").read())
                z.writestr(file_iramuteq, open(file_iramuteq, "rb").read())
                for p in macro_txts:
                    z.writestr(Path(p).name, open(p, "rb").read())
            zp.seek(0)
            progress.progress(100)

            st.download_button(
                "📥 Baixar Relatório Quinzenal",
                data=zp,
                file_name=f"{base}_relatorio_quinzenal.zip"
            )
            st.success("🎉 Relatório Quinzenal gerado com sucesso!")

        # cleanup temporário
        if os.path.exists(raw_path):
            os.remove(raw_path)
