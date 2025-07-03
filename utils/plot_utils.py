import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.dates import DateFormatter

# Carregamento das fontes Aptos
FONT_REGULAR = fm.FontProperties(fname='assets/fonts/aptos.ttf')
FONT_BOLD = fm.FontProperties(fname='assets/fonts/aptos-bold.ttf')


def generate_daily_volume_chart(
    df: pd.DataFrame,
    output_path: str,
    width: int,
    height: int
) -> str:
    """
    Gera um gráfico de linha (smoothed) da contagem de publicações diárias.

    - df deve ter colunas ['Hora', 'Dia', 'Mês', 'Serviços']
    - output_path: caminho do PNG a salvar
    - width, height: dimensões em pixels
    """
    # 1) Constrói datetime e agrupa
    df['datetime'] = pd.to_datetime(
        df['Dia'].astype(str) + '/' + df['Mês'].astype(str) + ' ' + df['Hora'],
        format='%d/%m %H:%M', errors='coerce'
    )
    counts = df.groupby('datetime').size().reset_index(name='count')

    # 2) Define labels e formato do eixo X
    unique_days = counts['datetime'].dt.day.nunique()
    if unique_days > 2:
        x_label = 'Data'
        fmt = DateFormatter('%d/%m')
    else:
        x_label = 'Data/Hora'
        fmt = DateFormatter('%Hh\n%d/%m')

    # 3) Cria figura transparente
    fig, ax = plt.subplots(figsize=(width/100, height/100))
    fig.patch.set_alpha(0)

    # 4) Plot suavizado (linha 2pt)
    ax.plot(
        counts['datetime'], counts['count'],
        linewidth=2, color='#26619C'
    )

    # 5) Formata axes
    ax.xaxis.set_major_formatter(fmt)
    ax.set_xlabel(x_label, fontproperties=FONT_BOLD, fontsize=9, color='#26619C')
    ax.set_ylabel('Publicações', fontproperties=FONT_BOLD, fontsize=9, color='#26619C')
    ax.tick_params(axis='x', labelrotation=45, labelsize=10.5)
    ax.tick_params(axis='y', labelsize=10.5)

    # 6) Legenda
    legend = ax.legend(['Publicações'], loc='upper center', prop=FONT_REGULAR)
    legend.get_frame().set_linewidth(0)

    # 7) Salva PNG transparente
    plt.tight_layout()
    fig.savefig(output_path, transparent=True, bbox_inches='tight')
    plt.close(fig)
    return output_path


def generate_biweekly_dual_axis_chart(
    df: pd.DataFrame,
    output_path: str,
    width: int,
    height: int
) -> str:
    """
    Gera um gráfico de colunas (gap width 150%) e linha de engajamento.

    - df deve ter colunas ['Ano','Mês','Dia','Total_Publicações','Manifestações reais']
    - output_path: caminho do PNG a salvar
    - width, height: dimensões em pixels
    """
    # 1) Constrói data e agrega
    df['date'] = pd.to_datetime(
        df[['Ano', 'Mês', 'Dia']].astype(str).agg('-'.join, axis=1),
        format='%Y-%m-%d', errors='coerce'
    )
    agg = df.groupby('date').agg(
        Publicacoes=('Total_Publicações', 'sum'),
        Engajamento=('Manifestações reais', 'sum')
    ).reset_index()

    # 2) Cria figura transparente
    fig, ax1 = plt.subplots(figsize=(width/100, height/100))
    fig.patch.set_alpha(0)
    ax2 = ax1.twinx()

    # 3) Gráfico de colunas (Publicacoes)
    # width ajustado para gap width 150% ≈ 1.5 vezes largura padrão
    bar_width = 0.6
    ax2.bar(
        agg['date'], agg['Publicacoes'],
        width=bar_width, color='#F2F2F2', edgecolor='#A6A6A6', linewidth=0.75
    )

    # 4) Gráfico de linha (Engajamento)
    ax1.plot(
        agg['date'], agg['Engajamento'],
        linewidth=2, color='#26619C'
    )

    # 5) Formata axes
    ax1.xaxis.set_major_formatter(DateFormatter('%d/%m'))
    ax1.set_xlabel('Data', fontproperties=FONT_BOLD, fontsize=9, color='#26619C')
    ax1.set_ylabel('Engajamento', fontproperties=FONT_BOLD, fontsize=9, color='#26619C')
    ax2.set_ylabel('Publicações', fontproperties=FONT_BOLD, fontsize=9, color='#26619C')
    ax1.tick_params(labelsize=10.5)
    ax2.tick_params(labelsize=10.5)

    # 6) Legendas
    ax1.legend(['Engajamento'], loc='upper left', prop=FONT_REGULAR)
    ax2.legend(['Publicações'], loc='upper right', prop=FONT_REGULAR)

    # 7) Salva PNG transparente
    plt.tight_layout()
    fig.savefig(output_path, transparent=True, bbox_inches='tight')
    plt.close(fig)
    return output_path
