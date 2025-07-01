import re
from wordcloud_utils import STOPWORDS

def clean_text(text):
    """
    Remove risadas do texto, como 'kkkk', 'hahaha', 'rsrs', etc.
    """
    regex = r'''(?ix)
        (?<!\w)
        (
            (k){3,}
            |(ha){2,}
            |(h[ae]{1,2}){2,}
            |(rs){2,}
            |(ua){2,}
        )
        (?!\w)
    '''
    return re.sub(regex, '', text).strip()

def preprocessar_texto(texto: str, tamanho_minimo: int = 4) -> str:
    """
    Remove risadas, palavras curtas, símbolos, e stopwords da stoplist.
    """
    texto = clean_text(texto)
    
    # Apenas palavras com letras e acentos, nada de números ou símbolos
    palavras = re.findall(r'\b[a-zA-ZÀ-ÿ]{2,}\b', texto)

    # Filtro: tamanho + não estar na stoplist
    palavras_filtradas = [
        w for w in palavras
        if len(w) >= tamanho_minimo and w.upper() not in STOPWORDS
    ]
    
    return " ".join(palavras_filtradas)
