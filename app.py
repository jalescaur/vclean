import streamlit as st
import os
import tempfile
import zipfile
import time
import pandas as pd
from io import BytesIO
from pathlib import Path

# === Import dos módulos existentes ===
from daily_posts import (
    process_and_export_excel as process_publicacoes,
    add_analysis_column_and_export_txt as analysis_publicacoes
)
from news import (
    process_and_export_excel as process_noticias,
    add_analysis_column_and_export_txt as analysis_noticias
)
from biweekly import full_pipeline

# === Configuração da página e estilo ===
st.set_page_config(page_title="🧼 V-Tracker: Data Cleaning", page_icon="📄", layout="centered")
st.markdown("""
    <style>
        body, .main { background-color: #ffffff; }
        .stButton>button, .stDownloadButton>button {
            background-color: #26619c; color: white; border-radius: 8px;
            padding: 0.5em 1em; font-size: 16px;
        }
        .stFileUploader>div { background-color: #f0f2f6; padding:1em;
            border:1px solid #26619c; border-radius:10px;
        }
        h1,h2,h3,h4,h5,h6, .css-1v0mbdj p, .css-1v0mbdj label { color: #26619c; }
    </style>
""", unsafe_allow_html=True)

# === Sidebar: escolha do workflow ===
workflow = st.sidebar.selectbox(
    "🔄 Escolha o tipo de processamento",
    ["Publicações", "Notícias", "Relatório Quinzenal"]
)

# === Workflow 1 & 2: Publicações ou Notícias ===
if workflow in ["Publicações", "Notícias"]:
    st.title(f"🧼 V-Tracker: Data Cleaning — {workflow}")
    uploaded_file = st.file_uploader("📤 Envie um arquivo .xlsx", type=["xlsx"])
    
    if st.button("🚀 Processar"):
        if not uploaded_file:
            st.warning("⚠️ Por favor, envie um arquivo antes de processar.")
        else:
            base = os.path.splitext(uploaded_file.name)[0]
            file_clean    = f"{base}_cleaned.xlsx"
            file_txt      = file_clean.replace(".xlsx", ".txt")
            file_iramuteq = file_clean.replace(".xlsx", "_corpus.txt")

            # grava temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            # chama o processamento certo
            if workflow == "Publicações":
                df = process_publicacoes(tmp_path, output_filename=file_clean)
                df_analysis = analysis_publicacoes(df.copy(), txt_filename=None)
            else:
                df = process_noticias(tmp_path, output_filename=file_clean)
                df_analysis = analysis_noticias(df.copy(), txt_filename=None)

            os.remove(tmp_path)

            # prepara buffers
            excel_buf = BytesIO(); df.to_excel(excel_buf, index=False)
            txt_buf   = BytesIO(); txt_buf.write(df_analysis["Análise"].str.cat(sep="\n").encode("utf-8"))
            iram_buf  = BytesIO()
            with open(file_iramuteq, "rb") as f: iram_buf.write(f.read())

            # gera ZIP
            zip_buf = BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as z:
                z.writestr(file_clean,    excel_buf.getvalue())
                z.writestr(file_txt,      txt_buf.getvalue())
                z.writestr(file_iramuteq, iram_buf.getvalue())
            zip_buf.seek(0)

            st.download_button(
                label="📦 Baixar arquivos (.zip)",
                data=zip_buf,
                file_name=f"{base}_resultados.zip",
                mime="application/zip"
            )
            st.success("✅ Tudo pronto! Baixe seu .zip.")

# === Workflow 3: Relatório Quinzenal ===
else:
    st.title("🧼 V-Tracker: Relatório Quinzenal")
    uploaded_file = st.file_uploader("📤 Envie um arquivo .xlsx", type=["xlsx"])
    
    if not uploaded_file:
        st.info("⬆️ Por favor, envie um arquivo para iniciar.")
    else:
        base_name = os.path.splitext(uploaded_file.name)[0]
        # grava temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(uploaded_file.read())
            temp_path = tmp.name

        # tenta ler tags para macrotemas
        try:
            df_tags = pd.read_excel(temp_path, sheet_name="Tags", skiprows=4)
            available_tags = df_tags.columns.tolist()
        except Exception as e:
            st.error(f"❌ Erro ao carregar aba 'Tags': {e}")
            available_tags = []

        # sidebar: seleção de macrotemas
        st.sidebar.header("🎯 Defina os Macrotemas")
        st.sidebar.caption("Selecione até 4 temas diferentes e confirme.")

        if "macrothemes" not in st.session_state:
            st.session_state.macrothemes = None
            st.session_state.confirmed   = False

        # configuração temporária
        macro_temp = {i: [] for i in range(1,5)}
        selected = set()
        for i in range(1,5):
            options = [t for t in available_tags if t not in selected]
            sel = st.sidebar.multiselect(f"Macrotema {i}", options, key=f"mtemp{i}")
            macro_temp[i] = sel
            selected.update(sel)

        st.sidebar.info(f"📚 Temas restantes: {len(available_tags) - len(selected)}")

        if st.sidebar.button("✅ Confirmar Seleções"):
            st.session_state.macrothemes = macro_temp
            st.session_state.confirmed   = True
            st.experimental_rerun()

        if st.sidebar.button("🔄 Resetar Seleções"):
            st.session_state.macrothemes = None
            st.session_state.confirmed   = False
            for i in range(1,5):
                st.session_state.pop(f"mtemp{i}", None)
            st.experimental_rerun()

        # depois de confirmar
        if st.session_state.confirmed:
            macrothemes = st.session_state.macrothemes
            st.write("### Macrotemas Confirmados:")
            for i in range(1,5):
                st.write(f"**Macrotema {i}:** {', '.join(macrothemes[i]) or 'Nenhum'}")

            if st.button("🚀 Gerar Relatório Quinzenal"):
                progress = st.progress(0, text="⏳ Processando dados...")
                # opcional simulação de progresso
                for pct in range(0, 30, 10):
                    time.sleep(0.1)
                    progress.progress(pct, text="⏳ Carregando e limpando")

                # executa pipeline
                cleaned_path, macro_txts, iram_txt = full_pipeline(
                    raw_filepath=temp_path,
                    macrotheme_definitions=macrothemes,
                    cleaned_output_filename=f"{base_name}_cleaned.xlsx"
                )

                for pct in range(30, 80, 10):
                    time.sleep(0.1)
                    progress.progress(pct, text="🔧 Gerando relatórios")

                # empacota tudo em ZIP
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
                    # Excel final
                    with open(cleaned_path, "rb") as f:
                        z.writestr(cleaned_path.name, f.read())
                    # Iramuteq
                    with open(iram_txt, "rb") as f:
                        z.writestr(iram_txt.name, f.read())
                    # Macrotema txts
                    for p in macro_txts:
                        with open(p, "rb") as f:
                            z.writestr(p.name, f.read())
                zip_buffer.seek(0)

                progress.progress(100, text="✅ Relatório pronto!")
                st.success("🎉 Arquivos gerados com sucesso!")

                st.download_button(
                    label="📥 Baixar Tudo (.zip)",
                    data=zip_buffer,
                    file_name=f"{base_name}_report.zip",
                    mime="application/zip"
                )

                # cleanup
                os.remove(temp_path)
                cleaned_path.unlink()
                iram_txt.unlink()
                for p in macro_txts:
                    p.unlink()
        else:
            st.info("⬅️ Confirme os macrotemas na barra lateral.")
