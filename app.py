import streamlit as st
import os, tempfile, zipfile
from io import BytesIO

# seu módulo atual de publicações (cleaning.py)
from cleaning import process_and_export_excel as process_publicacoes, \
                     add_analysis_column_and_export_txt as analysis_publicacoes

# novo módulo de notícias
from process_noticias import process_and_export_excel as process_noticias, \
                             add_analysis_column_and_export_txt as analysis_noticias

st.set_page_config(page_title="V-Tracker: Data Cleaning", page_icon="📄", layout="centered")
st.title("🧼 V-Tracker: Data Cleaning")

# escolha de workflow
option = st.selectbox("Selecione o tipo de dado:", ["Publicações", "Notícias"])
uploaded_file = st.file_uploader("📤 Envie um arquivo .xlsx", type=["xlsx"])

if st.button("🚀 Processar"):
    if not uploaded_file:
        st.warning("⚠️ Por favor, envie um arquivo antes de processar.")
    else:
        base = os.path.splitext(uploaded_file.name)[0]
        file_clean    = f"{base}_cleaned.xlsx"
        file_txt      = f"{base}.txt"
        file_iramuteq = f"{base}_iramuteq.txt"

        # salva temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        # chama a função certa
        if option == "Publicações":
            df = process_publicacoes(tmp_path, output_filename=file_clean)
            df_analysis = analysis_publicacoes(df.copy(), txt_filename=None)
        else:
            df = process_noticias(tmp_path, output_filename=file_clean)
            df_analysis = analysis_noticias(df.copy(), txt_filename=None)

        os.remove(tmp_path)

        # buffers para zip
        excel_buf = BytesIO(); df.to_excel(excel_buf, index=False)
        txt_buf   = BytesIO(); txt_buf.write(df_analysis["Análise"].str.cat(sep="\n").encode("utf-8"))
        iram_buf  = BytesIO(open(file_iramuteq, "rb").read())

        zip_buf = BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as z:
            z.writestr(file_clean,    excel_buf.getvalue())
            z.writestr(file_txt,      txt_buf.getvalue())
            z.writestr(file_iramuteq, iram_buf.getvalue())
        zip_buf.seek(0)

        st.download_button(
            label="📦 Baixar arquivos (.zip)",
            data=zip_buf.getvalue(),
            file_name=f"{base}_resultados.zip",
            mime="application/zip"
        )
        st.success("✅ Tudo pronto! Baixe seu ZIP.")
