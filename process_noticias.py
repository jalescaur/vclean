import pandas as pd
import re

# === Colunas que não entram no fluxo de Notícias ===
UNNECESSARY_COLUMNS = [
    "Descrição monitoramento", "Link serviço", "Descrição Pai", "Link ocorrência Pai", "Thumbnail",
    "Thumbnail pai", "Data coleta", "Linguagem", "Foto publicador", "PageRank", "Estrelas",
    "Qualificação", "Qualificada por", "Data da qualificação", "Qualificação automática", "Para",
    "Manifestações", "Cidade/Estado", "Latitude", "Longitude", "Id ocorrência no serviço",
    "Id ocorrência pai no serviço", "Link id ocorrência pai", "Arquivada", "Desarquivada",
    "Data Resposta", "Manifestações Detalhadas", "Termos", "Links", "Perfis", "Hashtags",
    "comments", "shares", "likes", "dislikes", "love", "wow", "haha", "sad", "angry",
    "thankful", "pride", "retweets", "favorites", "rating", "vendas", "resenhas", "votes",
    "views", "quotes", "videoViews", "URL da busca", "Id publicador", "Qualificação aprovada por",
    "Analisada por", "Data analisada", "Avaliação", "Tipo/Conteúdo", "Observação", "Unnamed: 73"
]

def export_for_iramuteq(df: pd.DataFrame, txt_filename: str):
    """Gera arquivo de corpus para IRAMUTEQ a partir de Título + Descrição."""
    def clean_text(text):
        return re.sub(r'[\|:\*"\?<>\|\$\-\'%]', '', str(text))
    lines = []
    for _, row in df.iterrows():
        id_    = row.get("ID", "")
        titulo = row.get("Título", "")
        descr  = clean_text(row.get("Descrição", ""))
        lines.append(f"**** *id_{id_} *u_{titulo}\n{descr}\n")
    with open(txt_filename, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"🧾 IRAMUTEQ salvo em: {txt_filename}")

def add_analysis_column_and_export_txt(df: pd.DataFrame, txt_filename: str):
    """Cria coluna Análise no formato desejado e exporta TXT."""
    for col in ["ID", "Título", "Descrição", "Link ocorrência"]:
        if col not in df.columns:
            df[col] = ""
    df["Análise"] = (
        df["ID"].astype(str)
        + " | Título: " + df["Título"].astype(str)
        + " | Texto: "  + df["Descrição"].astype(str)
        + " | Link: "   + df["Link ocorrência"].astype(str)
    )
    df["Análise"].to_csv(txt_filename, index=False, header=False)
    print(f"📝 Análise TXT salvo em: {txt_filename}")
    return df

def process_and_export_excel(filepath: str, output_filename: str) -> pd.DataFrame:
    """
    1) Lê sheet 'Ocorrências' (skiprows=4)
    2) Insere coluna ID
    3) Remove colunas UNNECESSARY_COLUMNS
    4) Exporta .txt de Análise e _iramuteq.txt
    5) Salva Excel limpo
    """
    print(f"📂 Processando Notícias: {filepath}")
    df = pd.read_excel(filepath, sheet_name="Ocorrências", skiprows=4)
    df.columns = df.columns.str.replace('"', '').str.strip()
    df.insert(0, "ID", range(1, len(df) + 1))

    # limpeza
    df = df.drop(columns=set(UNNECESSARY_COLUMNS).intersection(df.columns), errors="ignore")
    df = df.replace("-", "NA").dropna(axis=1, how="all")

    # gera Análise e IRAMUTEQ
    txt_analysis = output_filename.replace(".xlsx", ".txt")
    df = add_analysis_column_and_export_txt(df, txt_analysis)

    txt_iram = output_filename.replace(".xlsx", "_iramuteq.txt")
    export_for_iramuteq(df, txt_iram)

    # salva Excel
    df.to_excel(output_filename, index=False)
    print(f"✅ Excel de Notícias salvo em: {output_filename}")
    return df
