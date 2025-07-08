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
from regex import preprocessar_texto

# IMPORTA FUNÇÃO DE GRÁFICO DE VOLUMETRIA

from utils.plot_utils import generate_daily_volume_chart

# ← AQUI ↓, logo depois de set_page_config:
st.set_page_config(
    page_title="📊 V-Tracker: Data Cleaning & Analysis",
    page_icon="📈",
    layout="wide"
)

# Inicializa a chave macros_confirmed para evitar AttributeError
if 'macros_confirmed' not in st.session_state:
    st.session_state.macros_confirmed = False

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

# → Nuvem de palavras
cloud_size_label = st.sidebar.selectbox(
    'Tamanho da Nuvem',
    ['Quadrado', 'Retângulo', 'WashTape 1 (290×1760)', 'WashTape 2 (290×760)']
)
cloud_size_map = {
    'Quadrado':  (1600, 1600),
    'Retângulo': (1840, 1060),
    'WashTape 1 (290×1760)': (290, 1760),
    'WashTape 2 (290×760)':  (290, 760),
}
cloud_w, cloud_h = cloud_size_map[cloud_size_label]

# → Gráficos de volumetria
plot_size_label = st.sidebar.selectbox(
    'Tamanho do Gráfico',
    ['Diário (2475×1885)', 'Relatório (3780×1522)']
)
plot_size_map = {
    'Diário (2475×1885)':  (2475, 1885),
    'Relatório (3780×1522)': (3780, 1522),
}
plot_w, plot_h = plot_size_map[plot_size_label]


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

            # → Mesma lógica de temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(uploaded_pub.read())
                tmp_path = tmp.name

            # ← AQUI: chame process_publicacoes passando width e height
            # e desempacote em df e png_daily
            df, png_daily = process_publicacoes(
                tmp_path,
                output_filename=file_clean,
                width=plot_w,
                height=plot_h
            )

            # análise e renomeações
            analysis_publicacoes(df.copy(), txt_filename=file_ai)
            old_iram = file_clean.replace(".xlsx", "_iramuteq.txt")
            if os.path.exists(old_iram):
                os.rename(old_iram, file_corpus)
            os.remove(tmp_path)

            # prepara buffers para o ZIP
            excel_buf = BytesIO(); df.to_excel(excel_buf, index=False)
            ai_buf    = BytesIO(open(file_ai,     "rb").read())
            corp_buf  = BytesIO(open(file_corpus, "rb").read())

            # monta o ZIP com tudo
            zp = BytesIO()
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
                # 1) tabelas e .txt
                z.writestr(file_clean,  excel_buf.getvalue())
                z.writestr(file_ai,     ai_buf.getvalue())
                z.writestr(file_corpus, corp_buf.getvalue())

                # 2) gráfico de volumetria diária
                #    usa png_daily retornado pela função
                z.write(png_daily, arcname="daily_volume_chart.png")

                # 3) wordcloud de publicações
                cloud_pub = f"{base}_cloud.png"
                texto_pub = (
                    open(file_ai, "r", encoding="utf-8").read()
                    + "\n"
                    + open(file_corpus, "r", encoding="utf-8").read()
                )
                texto_pub_limpo = preprocessar_texto(texto_pub)
                generate_wordcloud(
                    text=texto_pub_limpo,
                    output_path=cloud_pub,
                    width=plot_w, height=plot_h
                )
                z.write(cloud_pub, arcname="daily_cloud.png")

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
                texto_news_limpo = preprocessar_texto(texto_news) # <--- REGEX

                generate_wordcloud(
                    text=texto_news_limpo,
                    output_path=cloud_news,
                    width=plot_w, height=plot_h
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

    # Apenas definir o uploader
    uploaded_bi = st.file_uploader(
        "📂 Envie o Excel para Relatório Quinzenal",
        type=["xlsx"],
        key="ubi"
    )
    if not uploaded_bi:
        st.info("⬆️ Por favor, envie um arquivo para iniciar.")
    else:
        # ─── 1) Armazena os bytes do upload ───────────────────────────
        bi_bytes = uploaded_bi.read()

        # ─── 2) Grava um temporário para tratar e outro para pipeline ──
        tmp_sel = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        tmp_sel.write(bi_bytes)
        tmp_sel.close()
        sel_path = tmp_sel.name

        raw_path = sel_path  # vamos usar o mesmo arquivo para o pipeline

        # ─── 3) Carrega e limpa o DataFrame para extrair só as tags ───
        from biweekly import (
            load_and_clean_sheet,
            clean_columns_and_values,
            process_grupos_column,
            enrich_parlamentar_and_date
        )

        df_main = load_and_clean_sheet(sel_path, sheet_name="Ocorrências", is_main=True)
        try:
            df_tags = load_and_clean_sheet(sel_path, sheet_name="Tags", is_main=False)
            # fallback de Tags
            fb = pd.DataFrame(0, index=df_main.index, columns=df_tags.columns)
            df_tags = df_tags.applymap(lambda x: 1 if str(x).strip().upper()=="SIM" else 0)
            fb.iloc[:len(df_tags), :] = df_tags
            df_combined = pd.concat([df_main, fb], axis=1)
        except Exception:
            df_combined = df_main

        df = clean_columns_and_values(df_combined)
        df = process_grupos_column(df)
        df = enrich_parlamentar_and_date(df)

        # ─── 4) Define só as colunas “tag” (microtemas) ────────────────
        from pandas.api.types import is_numeric_dtype

        # Só as colunas cujos valores são 0/1 (Tags)
        tema_cols = [
            col for col in df.columns
            if is_numeric_dtype(df[col])
            and df[col].dropna().isin([0,1]).all()]

        # ─── 5) Interface para criar macrotemas a partir dessas tags ─────
        st.markdown("### Definição de Macrotemas")
        n_macro = st.number_input(
            "Quantos macrotemas deseja?",
            min_value=1, max_value=10, value=2, step=1, key="n_macro"
        )
        macros = {}
        for i in range(1, n_macro+1):
            sel = st.multiselect(
                f"Macrotema {i} (selecione TAGS)",
                tema_cols,
                key=f"macro_select_{i}"
            )
            macros[i] = sel
        st.session_state.macros = macros

        if st.button("✅ Confirmo os macrotemas acima", key="confirm_macros"):
            st.session_state.macros_confirmed = True

        # ─── 6) Só após confirmar, executa o pipeline completo ─────────
        if st.session_state.macros_confirmed:
            # chama seu pipeline, que agora retorna também png_biweekly
            cleaned_path, macro_txts, iram_txt, png_biweekly = full_pipeline(
                raw_filepath=raw_path,
                macrotheme_definitions=st.session_state.macros,
                cleaned_output_filename=f"{Path(uploaded_bi.name).stem}_cleaned.xlsx",
                width=plot_w,
                height=plot_h
            )

            # monta e oferece o ZIP (mesma lógica de antes)
            zp = BytesIO()
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_STORED) as z:
                z.writestr(Path(cleaned_path).name, open(cleaned_path, "rb").read())
                for p in macro_txts:
                    z.writestr(Path(p).name, open(p, "rb").read())
                z.writestr(Path(iram_txt).name, open(iram_txt, "rb").read())
                z.write(png_biweekly, arcname="biweekly_volume_chart.png")
                # … nuvens de macrotema e geral …

            zp.seek(0)
            st.download_button(
                "📥 Baixar Relatório Quinzenal",
                data=zp.getvalue(),
                file_name=f"{Path(uploaded_bi.name).stem}_relatorio_quinzenal.zip",
                mime="application/zip"
            )
            st.success("🎉 Relatório Quinzenal gerado com sucesso!")

# — Cleanup temporário —
if 'raw_path' in locals() and raw_path and os.path.exists(raw_path):
    try:
        os.remove(raw_path)
    except Exception as e:
        st.warning(f"Não foi possível remover o arquivo temporário: {e}")
