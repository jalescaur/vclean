import pandas as pd
from datetime import datetime
import traceback
import re

# === Constants ===
UNNECESSARY_COLUMNS = [
    "Descrição monitoramento", "Link serviço", "Descrição Pai", "Link ocorrência Pai", "Thumbnail",
    "Thumbnail pai", "Data coleta", "Linguagem", "Foto publicador", "PageRank", "Estrelas",
    "Qualificação", "Qualificada por", "Data da qualificação", "Qualificação automática", "Para",
    "Latitude", "Longitude", "Id ocorrência no serviço", "Id ocorrência pai no serviço",
    "Link id ocorrência pai", "Arquivada", "Desarquivada", "Data Resposta",
    "Manifestações Detalhadas", "Termos", "Links", "Perfis", "Hashtags",
    "comments", "shares", "likes", "dislikes", "love", "wow", "haha", "sad", "angry",
    "thankful", "pride", "retweets", "favorites", "rating", "vendas", "resenhas", "votes", "views", "quotes",
    "videoViews", "URL da busca", "Id publicador", "Qualificação aprovada por", "Analisada por",
    "Data analisada", "Avaliação", "Tipo/Conteúdo", "Observação", "Unnamed: 73"
]

ENGAGEMENT_COLS = [
    "comments", "shares", "likes", "dislikes", "love", "wow", "haha", "sad", "angry",
    "thankful", "pride", "retweets", "favorites", "rating", "vendas",
    "resenhas", "votes", "views", "quotes"
]

LIST_CASA = ["CÂMARA", "SENADO"]
LIST_PARTIDO = ["MDB", "PT", "PRD", "PP", "PSDB", "PDT", "UNIÃO", "PL", "PODEMOS", "PSB", "REPUBLICANOS",
                 "PV", "AVANTE", "PSC", "PSOL", "PCDOB", "PSD", "SOLIDARIEDADE", "NOVO", "REDE", "PMB",
                 "UP", "DC", "PCO", "PSTU", "PCB", "PRTB", "MOBILIZA", "AGIR", "CIDADANIA", "PROS", "PATRIOTA"]
LIST_ESTADO = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB",
                "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]

SPECIFIC_OVERRIDES = {
    "Nilto Tatto": {"Partido": "PT", "Estado": "SP"},
    "Socorro Neri": {"Partido": "PP", "Estado": "AC"},
    "AJ Albuquerque": {"Partido": "PP", "Estado": "CE"},
    "Duarte Junior": {"Partido": "PSB", "Estado": "MA"},
    "Julio Cesar": {"Partido": "PSD", "Estado": "PI"},
    "Júlio César": {"Partido": "PSD", "Estado": "PI"},
    "Vicentinho Júnior": {"Partido": "PP", "Estado": "TO"},
    "Yury do Paredão": {"Partido": "MDB", "Estado": "CE"}
}

# === Utility Function for IRAMUTEQ ===
def export_for_iramuteq(df, txt_filename):
    def clean_description(text):
        return re.sub(r'[\|:\*"\?<>\|\$\-\'%]', '', str(text))

    lines = []
    for _, row in df.iterrows():
        id_val = row.get("ID", "")
        nome = row.get("Nome publicador", "")
        descricao = clean_description(row.get("Descrição", ""))
        lines.append(f"**** *id_{id_val} *u_{nome}\n{descricao}\n")

    with open(txt_filename, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"🧾 Arquivo IRAMUTEQ salvo como: {txt_filename}")

# === Core functions ===
def load_and_clean_sheet(filepath, sheet_name, is_main=True):
    df = pd.read_excel(filepath, sheet_name=sheet_name, skiprows=4)
    df.columns = df.columns.str.replace('"', '').str.strip()
    if is_main:
        df.insert(0, 'ID', range(1, len(df) + 1))
    return df

def clean_columns_and_values(df):
    # Sum "Manifestações reais" before dropping engagement columns
    engagement_present = [col for col in ENGAGEMENT_COLS if col in df.columns]
    if engagement_present:
        df["Manifestações reais"] = df[engagement_present].apply(pd.to_numeric, errors='coerce').sum(axis=1)
        if "Manifestações" in df.columns:
            idx = df.columns.get_loc("Manifestações") + 1
            cols = df.columns.tolist()
            cols.insert(idx, cols.pop(cols.index("Manifestações reais")))
            df = df[cols]

    df = df.drop(columns=set(UNNECESSARY_COLUMNS).intersection(df.columns), errors="ignore")
    df = df.replace("-", "NA").dropna(axis=1, how="all")

    for col in ['Perfil/Nome da busca', 'Serviço']:
        if col in df.columns:
            df[col] = df[col].str.split(r"[-,]").str[0].str.strip()

    return df

def process_grupos_column(df):
    if "Grupos" in df.columns:
        df['Grupos'] = df['Grupos'].str.upper()

        def split_grupos(row):
            items = row.split(" | ") if isinstance(row, str) else []
            casa = partido = estado = extras = None
            items = ["CÂMARA" if i == "CAMARA" else i for i in items]
            items = ["PODEMOS" if i == "PODE" else i for i in items]
            for item in items:
                if item in LIST_CASA and not casa:
                    casa = item
                elif item in LIST_PARTIDO and not partido:
                    partido = item
                elif item in LIST_ESTADO and not estado:
                    estado = item
                else:
                    extras = extras + " | " + item if extras else item
            return casa, partido, estado, extras

        df[['Casa', 'Partido', 'Estado', 'Extras']] = df['Grupos'].apply(split_grupos).apply(pd.Series)
        df = df.drop(columns=['Grupos'])

    if 'Perfil/Nome da busca' in df.columns:
        for name, overrides in SPECIFIC_OVERRIDES.items():
            mask = df['Perfil/Nome da busca'].str.contains(name, na=False, case=False)
            for key, value in overrides.items():
                df.loc[mask, key] = value

    # Drop columns if all values are null
    for col in ['Casa', 'Partido', 'Estado']:
        if col in df.columns and df[col].isnull().all():
            df = df.drop(columns=[col])

    return df

def enrich_parlamentar_and_date(df):
    def get_title(casa):
        return "Deputado(a)" if casa == "CÂMARA" else "Senador(a)" if casa == "SENADO" else ""

    if {'Casa', 'Perfil/Nome da busca', 'Partido', 'Estado'}.issubset(df.columns):
        df['Parlamentar'] = df.apply(
            lambda row: f"{get_title(row['Casa'])} {row['Perfil/Nome da busca']} ({row['Partido']}/{row['Estado']})",
            axis=1
        )

    if "Data publicação" in df.columns:
        df["Data publicação - Date"] = df["Data publicação"].str[:8].str.strip()
        df["Data publicação - Hour"] = df["Data publicação"].str[9:].str.strip()
        df = df.drop(columns=["Data publicação"])

    if "Data publicação - Date" in df.columns:
        df["Data publicação - Date"] = pd.to_datetime(df["Data publicação - Date"], format="%d/%m/%y", errors='coerce')
        df["Data publicação - Date"] = df["Data publicação - Date"].dt.strftime("%d/%m/%Y")
        df["Dia"] = pd.to_datetime(df["Data publicação - Date"], format="%d/%m/%Y", errors='coerce').dt.day
        df["Mês"] = pd.to_datetime(df["Data publicação - Date"], format="%d/%m/%Y", errors='coerce').dt.month
        df["Ano"] = pd.to_datetime(df["Data publicação - Date"], format="%d/%m/%Y", errors='coerce').dt.year

    if "Data publicação - Hour" in df.columns:
        df["Hora"] = df["Data publicação - Hour"].str[:2]

    return df

def add_analysis_column_and_export_txt(df, txt_filename):
    for col in ['ID', 'Descrição', 'Manifestações', 'Link ocorrência']:
        if col not in df.columns:
            df[col] = ""

    df["Análise"] = (
        "ID: " + df["ID"].astype(str) +
        " | Texto: " + df["Descrição"].astype(str) +
        " | Engajamento: " + df["Manifestações"].astype(str) +
        " | Link: " + df["Link ocorrência"].astype(str)
    )

    df["Análise"].to_csv(txt_filename, index=False, header=False)
    print(f"📝 Arquivo .txt salvo como: {txt_filename}")
    return df

def process_and_export_excel(filepath, output_filename):
    print(f"📂 Processando arquivo: {filepath}")

    df_main = load_and_clean_sheet(filepath, sheet_name="Ocorrências", is_main=True)
    df_main = df_main.reset_index(drop=True)
    df_combined = df_main.copy()

    try:
        df_tags = load_and_clean_sheet(filepath, sheet_name="Tags", is_main=False)
        df_tags = df_tags.reset_index(drop=True)
        tag_fallback = pd.DataFrame(0, index=range(len(df_main)), columns=df_tags.columns)
        df_tags = df_tags.applymap(lambda x: 1 if str(x).strip().upper() == "SIM" else 0)
        rows_to_fill = min(len(df_tags), len(tag_fallback))
        tag_fallback.iloc[:rows_to_fill] = df_tags.iloc[:rows_to_fill]
        df_combined = pd.concat([df_main, tag_fallback], axis=1)
        print("✅ Tags processadas linha a linha com fallback zero.")
    except Exception as e:
        print("⚠️ Aba 'Tags' não encontrada ou erro ao carregar:", str(e))
        traceback.print_exc()

    df = clean_columns_and_values(df_combined)
    df = process_grupos_column(df)
    df = enrich_parlamentar_and_date(df)
    df = add_analysis_column_and_export_txt(df, txt_filename=output_filename.replace(".xlsx", ".txt"))
    export_for_iramuteq(df, txt_filename=output_filename.replace(".xlsx", "_iramuteq.txt"))

    db = df.copy()
    db.to_excel(output_filename, index=False)
    print(f"✅ Banco de dados limpo salvo como: {output_filename}")
    return db