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

# ----------------------------------------
# ABA 1: Publicações
# ----------------------------------------
with tab1:
    st.header("📱 Processamento de Publicações")
    uploaded_pub = st.file_uploader(
        "📂 Envie o Excel de Publicações", type=["xlsx"], key="upub"
    )
    if not uploaded_pub:
        st.info("⬆️ Por favor, envie um arquivo para iniciar.")
    else:
        if st.button("📊 Processar Publicações"):
            base = os.path.splitext(uploaded_pub.name)[0]
            file_clean    = f"{base}_cleaned.xlsx"
            file_gpt      = f"{base}_gpt.txt"
            file_iramuteq = f"{base}_corpus.txt"

            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(uploaded_pub.read())
                tmp_path = tmp.name

            df = process_publicacoes(tmp_path, output_filename=file_clean)
            df_analysis = analysis_publicacoes(df.copy(), txt_filename=None)
            os.remove(tmp_path)

            excel_buf = BytesIO(); df.to_excel(excel_buf, index=False)
            txt_buf   = BytesIO(); txt_buf.write(
                df_analysis["Análise"].str.cat(sep="\n").encode("utf-8")
            )
            iram_buf  = BytesIO()
            with open(file_iramuteq, "rb") as f: iram_buf.write(f.read())

            zp = BytesIO()
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
                z.writestr(file_clean,    excel_buf.getvalue())
                z.writestr(file_gpt,      txt_buf.getvalue())
                z.writestr(file_iramuteq, iram_buf.getvalue())
            zp.seek(0)

            st.download_button(
                "📥 Baixar Resultados (Publicações)",
                data=zp,
                file_name=f"{base}_publicacoes.zip"
            )
            st.success("✅ Publicações processadas com sucesso!")

# ----------------------------------------
# ABA 2: Notícias
# ----------------------------------------
with tab2:
    st.header("🗞️ Processamento de Notícias")
    uploaded_news = st.file_uploader(
        "📂 Envie o Excel de Notícias", type=["xlsx"], key="unews"
    )
    if not uploaded_news:
        st.info("⬆️ Por favor, envie um arquivo para iniciar.")
    else:
        if st.button("📊 Processar Notícias"):
            base = os.path.splitext(uploaded_news.name)[0]
            file_clean    = f"{base}_cleaned.xlsx"
            file_gpt      = f"{base}_gpt.txt"
            file_iramuteq = f"{base}_corpus.txt"

            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(uploaded_news.read())
                tmp_path = tmp.name

            df = process_noticias(tmp_path, output_filename=file_clean)
            df_analysis = analysis_noticias(df.copy(), txt_filename=None)
            os.remove(tmp_path)

            excel_buf = BytesIO(); df.to_excel(excel_buf, index=False)
            txt_buf   = BytesIO(); txt_buf.write(
                df_analysis["Análise"].str.cat(sep="\n").encode("utf-8")
            )
            iram_buf  = BytesIO()
            with open(file_iramuteq, "rb") as f: iram_buf.write(f.read())

            zp = BytesIO()
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
                z.writestr(file_clean,    excel_buf.getvalue())
                z.writestr(file_gpt,      txt_buf.getvalue())
                z.writestr(file_iramuteq, iram_buf.getvalue())
            zp.seek(0)

            st.download_button(
                "📥 Baixar Resultados (Notícias)",
                data=zp,
                file_name=f"{base}_noticias.zip"
            )
            st.success("✅ Notícias processadas com sucesso!")

# ----------------------------------------
# ABA 3: Relatório Quinzenal
# ----------------------------------------
with tab3:
    st.header("🗓️ Relatório Quinzenal")
    multitema = st.checkbox("🔄 Análise multitemática?", help="Permitir repetir a mesma tag em vários macrotemas")

    uploaded_bi = st.file_uploader(
        "📂 Envie o Excel para Relatório Quinzenal",
        type=["xlsx"],
        key="ubi"
    )
    if not uploaded_bi:
        st.info("⬆️ Por favor, envie um arquivo para iniciar.")
    else:
        base = os.path.splitext(uploaded_bi.name)[0]
        # grava o upload
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(uploaded_bi.read())
            raw_path = tmp.name

        # lê as colunas de Tags
        try:
            df_tags = pd.read_excel(raw_path, sheet_name="Tags", skiprows=4)
            tag_options = df_tags.columns.tolist()
        except Exception:
            tag_options = []

        # inicia estado de seleção
        if "current_macro" not in st.session_state:
            st.session_state.current_macro = 1
            st.session_state.macros = {}

        # se ainda faltam macrotemas:
        idx = st.session_state.current_macro
        if idx <= 4:
            st.subheader(f"Selecione Macrotema {idx}")
            # filtra opções já usadas, se multitema == False
            if multitema:
                choices = tag_options
            else:
                used = set().union(*st.session_state.macros.values())
                choices = [t for t in tag_options if t not in used]

            sel = st.multiselect(f"Macrotema {idx}", choices, key=f"mt{idx}")

            if st.button(f"✅ Confirmar Macrotema {idx}"):
                st.session_state.macros[idx] = sel
                st.session_state.current_macro += 1
                st.experimental_rerun()  # safe here to advance the UI

        else:
            # todos selecionados
            st.subheader("Macrotemas Confirmados:")
            for i, tags in st.session_state.macros.items():
                st.write(f"- Macrotema {i}: {', '.join(tags) or 'Nenhum'}")

            if st.button("📊 Gerar Relatório Quinzenal"):
                progress = st.progress(0, text="⏳ Processando dados...")
                for pct in (20,50,80):
                    time.sleep(0.1)
                    progress.progress(pct)

                cleaned_path, macro_txts, iram_txt = full_pipeline(
                    raw_filepath           = raw_path,
                    macrotheme_definitions = st.session_state.macros,
                    cleaned_output_filename= f"{base}_cleaned.xlsx"
                )

                # ZIP final
                zp = BytesIO()
                with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
                    z.writestr(Path(cleaned_path).name, open(cleaned_path, "rb").read())
                    z.writestr(Path(iram_txt).name,       open(iram_txt,    "rb").read())
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

        # ao final da execução, limpe o temp
        # (pode querer mover isso para depois do download)
        if os.path.exists(raw_path):
            os.remove(raw_path)