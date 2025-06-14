import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
from io import BytesIO
import tempfile
from cleaning import process_and_export_excel, add_analysis_column_and_export_txt

# Page configuration
st.set_page_config(page_title="V-Tracker: Data Cleaning", page_icon="📄", layout="centered")
st.title("🧼 V-Tracker: Data Cleaning")

# File upload section
st.markdown("### Envie um arquivo:")

uploaded_file = st.file_uploader("📤 Envie um arquivo .xlsx", type=["xlsx"])

file_name = None
if uploaded_file is not None:
    base_name = os.path.splitext(uploaded_file.name)[0]
    file_name_clean = f"{base_name}_cleaned.xlsx"
    file_name_gpt = f"{base_name}_gpt.txt"
    file_name_iramuteq = f"{base_name}_corpus.txt"
    st.success(f"💾 Arquivos gerados:\n- {file_name_clean}\n- {file_name_gpt}\n- {file_name_iramuteq}")

if st.button("🚀 Processar"):
    try:
        if uploaded_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp:
                temp.write(uploaded_file.read())
                temp_path = temp.name

            # Process the file (avoid saving to disk)
            df = process_and_export_excel(temp_path, output_filename="do_not_save.xlsx")

            # Remove temp files
            os.remove(temp_path)
            if os.path.exists("do_not_save.xlsx"):
                os.remove("do_not_save.xlsx")

            # Prepare cleaned Excel download
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False)
            st.download_button("📥 Baixar planilha limpa", data=excel_buffer.getvalue(), file_name=file_name_clean)

            # Prepare GPT .txt
            gpt_buffer = BytesIO()
            df_with_analysis = add_analysis_column_and_export_txt(df.copy(), txt_filename=None)
            gpt_lines = df_with_analysis["Análise"].str.cat(sep="\n")
            gpt_buffer.write(gpt_lines.encode("utf-8"))
            st.download_button("📥 Baixar texto para GPT", data=gpt_buffer.getvalue(), file_name=file_name_gpt)

            # Prepare IRAMUTEQ .txt
            iramuteq_buffer = BytesIO()
            def clean_description(text):
                return re.sub(r'[\|:\*"\?<>\|\$\-\'%]', '', str(text))
            iramuteq_lines = []
            for _, row in df.iterrows():
                id_val = row.get("ID", "")
                nome = row.get("Nome publicador", "")
                descricao = clean_description(row.get("Descrição", ""))
                iramuteq_lines.append(f"**** *id_&{id_val} *u_&{nome}\n{descricao}\n")
            iramuteq_buffer.write("".join(iramuteq_lines).encode("utf-8"))
            st.download_button("📥 Baixar texto para IRAMUTEQ", data=iramuteq_buffer.getvalue(), file_name=file_name_iramuteq)

            st.success("✅ Todos os arquivos foram gerados com sucesso!")
        else:
            st.warning("⚠️ Por favor, envie um arquivo antes de processar.")
    except Exception as e:
        st.error(f"❌ Ocorreu um erro ao processar o arquivo: {e}")
