# === Full clean.py with Fix for 'Análise' Column and Macrotheme Processing ===

import pandas as pd
import re
from pathlib import Path
import traceback

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

# === Helper Functions ===

def clean_description(text):
    return re.sub(r'[\|:\*"<>\$\-\'%]', '', str(text))

def export_iramuteq(df, output_path):
    lines = []
    for _, row in df.iterrows():
        id_val = row.get("ID", "")
        nome = row.get("Nome publicador", "")
        descricao = clean_description(row.get("Descrição", ""))
        lines.append(f"**** *id_{id_val} *u_{nome}\n{descricao}\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def load_and_clean_sheet(filepath, sheet_name, is_main=True):
    df = pd.read_excel(filepath, sheet_name=sheet_name, skiprows=4)
    df.columns = df.columns.str.replace('"', '').str.strip()
    if is_main:
        df.insert(0, 'ID', range(1, len(df) + 1))
    return df

def clean_columns_and_values(df):
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

def add_analysis_column(df):
    for col in ['ID', 'Descrição', 'Manifestações', 'Link ocorrência']:
        if col not in df.columns:
            df[col] = ""
    df["Análise"] = (
        "ID: " + df["ID"].astype(str) +
        " | Texto: " + df["Descrição"].astype(str) +
        " | Engajamento: " + df["Manifestações"].astype(str) +
        " | Link: " + df["Link ocorrência"].astype(str)
    )
    return df

# === Full Pipeline to Process, Export, and Save ===

def get_macrotheme_names(macrotheme_definitions):
    macrotheme_names = {}
    for macro, tags in macrotheme_definitions.items():
        name = " + ".join(tags)
        macrotheme_names[macro] = name
    return macrotheme_names

def assign_macrothemes(df, macrotheme_definitions):
    tag_columns = [col for col in df.columns if col not in df.columns[:df.columns.get_loc('Serviço')+1]]
    assignments = pd.DataFrame(0, index=df.index, columns=['Macrotema'])
    for macro, tags in macrotheme_definitions.items():
        mask = df[tags].sum(axis=1) > 0
        assignments.loc[mask, 'Macrotema'] = macro
    return assignments

def export_macrotheme_txts(df, assignments, macrotheme_definitions, base_name, output_dir):
    output_files = []
    for macro, tags in macrotheme_definitions.items():
        subset = df[assignments['Macrotema'] == macro]
        if not subset.empty:
            name_part = "_".join([t.lower().replace(" ", "_") for t in tags])

            # === Novo código: sufixo "_macrotema-{n}" === 2025-6-27
            full_path = output_dir / f"{base_name}_macrotema-{macro}_{name_part}.txt"
            with open(full_path, "w", encoding="utf-8") as f:
                subset = df[df["macrotema"] == macro]
            for text in subset["text"]:
                f.write(text + "\n")
            # === Fim do novo código: sufixo "_macrotema-{n}" === 2025-6-27
            
            subset['Análise'].to_csv(full_path, index=False, header=False, encoding='utf-8')
            output_files.append(full_path)
    return output_files

def create_pivot_summary(df, assignments, macrotheme_definitions):
    df['Macrotema'] = assignments['Macrotema']

    # Total number of posts in the database
    total_posts = df.shape[0]

    # Get names for macrothemes
    macrotheme_names = get_macrotheme_names(macrotheme_definitions)

    # Map numbers to names
    df['Macrotema Nome'] = df['Macrotema'].map(macrotheme_names)
    df['Macrotema Nome'] = df['Macrotema Nome'].fillna('Sem Macrotema')

    # Create pivot
    summary = df.groupby(['Ano', 'Mês', 'Dia', 'Macrotema Nome']).agg(
        Total_Publicações=('ID', 'count'),
        Total_Engajamento=('Manifestações reais', 'sum')
    ).reset_index()

    # Sort
    summary = summary.sort_values(['Mês', 'Dia'])

    return summary, total_posts

def create_microtheme_percentage(df, assignments):
    df['Macrotema'] = assignments['Macrotema']
    themes_cols = [col for col in df.columns if col not in df.columns[:df.columns.get_loc('Serviço')+1]]

    numeric_df = df[themes_cols].apply(pd.to_numeric, errors='coerce')

    percentages = numeric_df.groupby(df['Macrotema']).mean() * 100
    percentages = percentages.round(2)
    return percentages

def create_relative_frequency_summary(df, assignments, macrotheme_definitions, total_posts):
    df['Macrotema'] = assignments['Macrotema']

    macrotheme_names = get_macrotheme_names(macrotheme_definitions)

    df['Macrotema Nome'] = df['Macrotema'].map(macrotheme_names)
    df['Macrotema Nome'] = df['Macrotema Nome'].fillna('Sem Macrotema')

    # Macrotheme Relative Frequency
    macro_counts = df['Macrotema Nome'].value_counts(normalize=True) * 100
    macro_freq = macro_counts.round(2).reset_index()
    macro_freq.columns = ['Macrotema', 'Frequência Relativa (%)']

    # Microtheme Relative Frequency
    themes_cols = df.columns[df.columns.get_loc('Serviço') + 1:]
    valid_theme_cols = [col for col in themes_cols if set(df[col].dropna().unique()).issubset({0, 1})]
    numeric_df = df[valid_theme_cols].apply(pd.to_numeric, errors='coerce')
    microtheme_freq = numeric_df.sum() / total_posts
    microtheme_freq = microtheme_freq.round(4).reset_index()
    microtheme_freq.columns = ['Microtema', 'Frequência Relativa']

    return macro_freq, microtheme_freq

def full_pipeline(raw_filepath, macrotheme_definitions, cleaned_output_filename):
    raw_path = Path(raw_filepath)
    cleaned_path = raw_path.parent / cleaned_output_filename

    df_main = load_and_clean_sheet(raw_path, sheet_name="Ocorrências", is_main=True)

    try:
        df_tags = load_and_clean_sheet(raw_path, sheet_name="Tags", is_main=False)
        tag_fallback = pd.DataFrame(0, index=range(len(df_main)), columns=df_tags.columns)
        df_tags = df_tags.applymap(lambda x: 1 if str(x).strip().upper() == "SIM" else 0)
        rows_to_fill = min(len(df_tags), len(tag_fallback))
        tag_fallback.iloc[:rows_to_fill] = df_tags.iloc[:rows_to_fill]
        df_combined = pd.concat([df_main, tag_fallback], axis=1)
    except Exception:
        traceback.print_exc()
        df_combined = df_main.copy()

    df = clean_columns_and_values(df_combined)
    df = process_grupos_column(df)
    df = enrich_parlamentar_and_date(df)
    df = add_analysis_column(df)

    assignments = assign_macrothemes(df, macrotheme_definitions)

    # Export final Excel with pivots
    with pd.ExcelWriter(cleaned_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name='Cleaned Data')
        pivot_summary, total_posts = create_pivot_summary(df, assignments, macrotheme_definitions)
        pivot_summary.to_excel(writer, index=False, sheet_name='pvt_summary')
        macro_freq, microtheme_freq = create_relative_frequency_summary(
            df, assignments, macrotheme_definitions, total_posts
        )
        macro_freq.to_excel(writer, index=False, sheet_name='macro_freq')
        microtheme_freq.to_excel(writer, index=False, sheet_name='microtheme_freq')

    # --- Novo código para definir o prefixo base sem "_cleaned" ---
    stem = cleaned_path.stem
    if stem.endswith("_cleaned"):
        clean_base = stem[:-len("_cleaned")]
    else:
        clean_base = stem

    # Prefixo para arquivos de macrotema com sufixo "_ai"
    ai_macro_base = f"{clean_base}_ai"
    # --- Fim do novo código ---

    # Export macrotheme .txt usando o novo base_name (inclui "_ai")
    output_txts = export_macrotheme_txts(
        df,
        assignments,
        macrotheme_definitions,
        base_name=ai_macro_base,           # <— aqui usamos {base}_ai
        output_dir=cleaned_path.parent
    )

    # Export Iramuteq .txt com sufixo "_corpus.txt"
    iramuteq_txt_path = cleaned_path.parent / f"{clean_base}_corpus.txt"
    export_iramuteq(df, iramuteq_txt_path)

    return cleaned_path, output_txts, iramuteq_txt_path