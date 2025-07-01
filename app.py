import streamlit as st
import os
import tempfile
import zipfile
import time
import pandas as pd
from io import BytesIO
from pathlib import Path
import re

# === Seus módulos ===
from daily_posts import (
    process_and_export_excel    as process_publicacoes,
    add_analysis_column_and_export_txt as analysis_publicacoes
)
from news import (
    process_and_export_excel    as process_noticias,
    add_analysis_column_and_export_txt as analysis_noticias
)
from biweekly import full_pipeline  # biweekly.py

# ← ADICIONADO: import da função de nuvem
from utils.wordcloud_utils import generate_wordcloud

# Importa a função de limpeza de texto
from regex import clean_text
from regex import remove_palavras_curtas

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

# ← ADICIONADO: controle de tamanho da nuvem
st.sidebar.header('Tamanho da Nuvem')
size_label = st.sidebar.selectbox(
    'Escolha um tamanho:',
    [
        'Quadrado (800×800)',
        'Retângulo (920×530)',
        'WashTape 1 (290×1760)',
        'WashTape 2 (290×760)'
    ]
)
size_map = {
    'Quadrado (800×800)':  (800, 800),
    'Retângulo (920×530)': (920, 530),
    'WashTape 1 (290×1760)': (290, 1760),
    'WashTape 2 (290×760)':  (290, 760),
}
width, height = size_map[size_label]

# ==== Abas ====
tab1, tab2, tab3 = st.tabs([
    "📱 Publicações", 
    "🗞️ Notícias", 
    "🗓️ Relatório Quinzenal"
])

# === Aba 1: Publicações ===
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
            file_clean  = f"{base}_cleaned.xlsx"
            file_ai     = f"{base}_ai.txt"
            file_corpus = f"{base}_corpus.txt"

            # → Mesma lógica de temp file e processamento existente
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(uploaded_pub.read())
                tmp_path = tmp.name
            df = process_publicacoes(tmp_path, output_filename=file_clean)
            analysis_publicacoes(df.copy(), txt_filename=file_ai)
            old_iram = file_clean.replace(".xlsx", "_iramuteq.txt")
            if os.path.exists(old_iram):
                os.rename(old_iram, file_corpus)
            os.remove(tmp_path)

            # → Prepara buffers dos três arquivos originais
            excel_buf = BytesIO(); df.to_excel(excel_buf, index=False)
            ai_buf    = BytesIO(open(file_ai,     "rb").read())
            corp_buf  = BytesIO(open(file_corpus, "rb").read())

            # ← ADICIONADO: Geração de ZIP incluindo wordcloud
            zp = BytesIO()
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
                # arquivos originais
                z.writestr(file_clean,  excel_buf.getvalue())
                z.writestr(file_ai,     ai_buf.getvalue())
                z.writestr(file_corpus, corp_buf.getvalue())

                # ← ADICIONADO: Gera e adiciona a nuvem de Publicações
                cloud_pub = f"{base}_cloud.png"
                texto_pub = open(file_ai, "r", encoding="utf-8").read() + "\n" + \
                            open(file_corpus, "r", encoding="utf-8").read()

                # Aplicar a limpeza de texto usando a função importada
                texto_pub_limpo = clean_text(texto_pub)
                texto_pub_limpo = remove_palavras_curtas(texto_pub_limpo, tamanho_minimo=4)

                generate_wordcloud(
                    text=texto_pub_limpo,
                    output_path=cloud_pub,
                    width=width, height=height
                )
                z.write(cloud_pub, arcname=cloud_pub)

            zp.seek(0)
            st.download_button(
                "📥 Baixar Resultados (Publicações)",
                data=zp.getvalue(),
                file_name=f"{base}_publicacoes.zip",
                mime="application/zip"
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
            file_clean  = f"{base}_cleaned.xlsx"
            file_ai     = f"{base}_ai.txt"
            file_corpus = f"{base}_corpus.txt"

            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(uploaded_news.read())
                tmp_path = tmp.name
            df = process_noticias(tmp_path, output_filename=file_clean)
            analysis_noticias(df.copy(), txt_filename=file_ai)
            old_iram = file_clean.replace(".xlsx", "_iramuteq.txt")
            if os.path.exists(old_iram):
                os.rename(old_iram, file_corpus)
            os.remove(tmp_path)

            excel_buf = BytesIO(); df.to_excel(excel_buf, index=False)
            ai_buf    = BytesIO(open(file_ai,     "rb").read())
            corp_buf  = BytesIO(open(file_corpus, "rb").read())

            # ← ADICIONADO: ZIP com nuvem
            zp = BytesIO()
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
                z.writestr(file_clean,  excel_buf.getvalue())
                z.writestr(file_ai,     ai_buf.getvalue())
                z.writestr(file_corpus, corp_buf.getvalue())

                # nuvem de Notícias
                cloud_news = f"{base}_noticias_cloud.png"
                texto_news = open(file_ai, "r", encoding="utf-8").read() + "\n" + \
                             open(file_corpus, "r", encoding="utf-8").read()
                
                # Aplicar a limpeza de texto usando a função importada
                texto_news_limpo = clean_text(texto_news)
                texto_news_limpo = remove_palavras_curtas(texto_news_limpo, tamanho_minimo=4)

                generate_wordcloud(
                    text=texto_news_limpo,
                    output_path=cloud_news,
                    width=width, height=height
                )
                z.write(cloud_news, arcname=cloud_news)

            zp.seek(0)
            st.download_button(
                "📥 Baixar Resultados (Notícias)",
                data=zp.getvalue(),
                file_name=f"{base}_noticias.zip",
                mime="application/zip"
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
        # … (inicialização de session_state e multiselects mantidos igual :contentReference[oaicite:0]{index=0})
        if st.session_state.macros_confirmed:
            gerar = st.checkbox("✅ Confirmo que está tudo correto", key="confirm_files")
        else:
            gerar = False

            if gerar:
                progress_bar = st.progress(0)
                with st.spinner("Processando relatório quinzenal…"):
                    # ← ADICIONADO: aqui criamos raw_path
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                        tmp.write(uploaded_bi.read())
                        raw_path = tmp.name

                    input_base = os.path.splitext(uploaded_bi.name)[0]
                    # agora raw_path está definido
                    cleaned_path, macro_txts, iram_txt = full_pipeline(
                        raw_filepath=raw_path,
                        macrotheme_definitions=st.session_state.macros,
                        cleaned_output_filename=f"{input_base}_cleaned.xlsx"
                    )

                # ← ADICIONADO: prepara ZIP com todos os itens + nuvens
                zp = BytesIO()
                with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
                    # planilha limpa
                    z.writestr(Path(cleaned_path).name,
                               open(cleaned_path, "rb").read())
                    # cada macrotema .txt
                    for p in macro_txts:
                        z.writestr(Path(p).name, open(p, "rb").read())
                    # corpus geral
                    z.writestr(Path(iram_txt).name,
                               open(iram_txt, "rb").read())

                    # nuvens de macrotema
                    for p in macro_txts:
                        txt = open(p, "r", encoding="utf-8").read()
                        txt_limpo = clean_text(txt)  # Aplicar REGEX para limpar o texto
                        txt_limpo = remove_palavras_curtas(txt_limpo, tamanho_minimo=4)  # << ADICIONADO MAIS REGEX
                        cloud_mt = f"{Path(p).stem}.png"
                        
                        generate_wordcloud(
                            text=txt_limpo,
                            output_path=cloud_mt,
                            width=width, height=height
                        )
                        z.write(cloud_mt, arcname=cloud_mt)

                    # nuvem geral (corpus)
                    geral_txt = open(iram_txt, "r", encoding="utf-8").read()
                    geral_txt_limpo = clean_text(geral_txt)  # Aplicar REGEX para limpar o texto
                    geral_txt_limpo = remove_palavras_curtas(geral_txt_limpo, tamanho_minimo=4)  # << ADICIONADO MAIS REGEX
                    cloud_geral = f"{input_base}_geral.png"

                    generate_wordcloud(
                        text=geral_txt_limpo,
                        output_path=cloud_geral,
                        width=width, height=height
                    )
                    z.write(cloud_geral, arcname=cloud_geral)

                zp.seek(0)
                progress_bar.progress(100)
                st.download_button(
                    "📥 Baixar Relatório Quinzenal",
                    data=zp,
                    file_name=f"{input_base}_relatorio_quinzenal.zip",
                    mime="application/zip"
                )
                st.success("🎉 Relatório Quinzenal gerado com sucesso!")

# — Cleanup temporário —
if 'raw_path' in locals() and raw_path and os.path.exists(raw_path):
    try:
        os.remove(raw_path)
    except Exception as e:
        st.warning(f"Não foi possível remover o arquivo temporário: {e}")
