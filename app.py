import streamlit as st
import os
import tempfile
import zipfile
import time
import pandas as pd
from io import BytesIO
from biweekly import full_pipeline
from pathlib import Path
import zipfile

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

        # inicializa session_state para macros e confirmação
        if "macros" not in st.session_state:
            st.session_state.macros = {i: [] for i in range(1, 5)}
        if "macros_confirmed" not in st.session_state:
            st.session_state.macros_confirmed = False

        # Multiselects para os 4 macrotemas (sem confirmação individual)
        cols = st.columns(2)
        for i in range(1, 5):
            with cols[(i - 1) % 2]:
                # evita repetição de tags entre os macrotemas (se multitema=False)
                used = set().union(*[
                    st.session_state.macros[j] for j in range(1, 5) if j != i
                ]) if not multitema else set()
                choices = [t for t in all_tags if t not in used or t in st.session_state.macros.get(i, [])]
                st.session_state.macros[i] = st.multiselect(
                    f"Macrotema {i}",
                    options=choices,
                    default=st.session_state.macros.get(i, []),
                    key=f"sel_{i}"
                )

        # Botão único para confirmar todos os macros de uma vez
        if st.button("💾 Confirmar Macrotemas"):
            st.session_state.macros_confirmed = True
            st.success("Macrotemas confirmados!")

        # Pré-visualização dos nomes de arquivo antes de gerar relatório
        if st.session_state.macros_confirmed:
            base = Path(raw_path).stem
            if base.endswith("_raw"):
                base = base[:-4]
            st.markdown("**Arquivos que serão gerados:**")
            preview_files = [
                f"{base}_cleaned.xlsx",
                *[
                    f"{base}_ai_macrotema-{i}_{'_'.join(st.session_state.macros[i]) or 'sem_tags'}.txt"
                    for i in range(1, 5)
                ],
                f"{base}_corpus.txt",
                f"{base}_relatorio_quinzenal.zip"
            ]
            for name in preview_files:
                st.write(f"- {name}")

            # Confirmação final para gerar relatório
            if st.checkbox("✅ Confirmo que está tudo correto", key="confirm_files"):
                gerar = True
            else:
                gerar = False
        else:
            gerar = False

        # Gera relatório apenas após confirmação
        if gerar:
            with st.spinner("Processando relatório quinzenal…"):

            # ==== novo código 2025-6-27

                if gerar:
                    # 0) Inicializa barra de progresso
                    progress_bar = st.progress(0)

                    with st.spinner("Processando relatório quinzenal…"):
                        # 1) Define nomes de saída
                        base = Path(raw_path).stem
                        if base.endswith("_raw"):
                            base = base[:-4]

                        file_clean  = f"{base}_cleaned.xlsx"
                        file_ai     = f"{base}_ai.txt"
                        file_corpus = f"{base}_corpus.txt"

                        # 2) Executa pipeline principal
                        cleaned_path, macro_txts, iram_txt = full_pipeline(
                            raw_filepath=raw_path,
                            macrotheme_definitions=st.session_state.macros,
                            cleaned_output_filename=file_clean
                        )

                        # 3) Empacota tudo em um ZIP
                        zp = BytesIO()
                        with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
                            z.writestr(file_clean,  open(cleaned_path, "rb").read())
                            z.writestr(file_ai,     open(file_ai,     "rb").read())
                            z.writestr(file_corpus, open(file_corpus, "rb").read())
                            for p in macro_txts:
                                z.writestr(Path(p).name, open(p, "rb").read())
                        zp.seek(0)

                        # 4) Atualiza progresso para 100%
                        progress_bar.progress(100)

                        # 5) Gera botão de download
                        st.download_button(
                            "📥 Baixar Relatório Quinzenal",
                            data=zp,
                            file_name=f"{base}_relatorio_quinzenal.zip"
                        )
                        st.success("🎉 Relatório Quinzenal gerado com sucesso!")
            # ==== novo código 2025-6-27

# cleanup temporário
    if os.path.exists(raw_path):
        os.remove(raw_path)
