# regex.py
import re
from wordcloud_utils import STOPWORDS

def clean_text(text):
    """
    Remove risadas do texto, como 'kkkk', 'hahaha', 'huahuahua', etc.
    """
    regex = r'''(?ix)
        (?<!\w)
        (
            (k){1,}                # kkkk, kkkkkk
            |(ha){1,}              # hahaha, hahahaha
            |(h[ae]{1,2}){2,}      # hehehe, huehue, hahaha
            |(rs){2,}              # rsrsrs
            |(ua){2,}              # uaua, uauaua
        )
        (?!\w)
    '''
    return re.sub(regex, '', text).strip()

def preprocessar_texto(texto: str, tamanho_minimo: int = 4) -> str:
    """
    Limpa risadas, remove palavras curtas e palavras da stoplist.
    """
    texto_limpo = clean_text(texto)
    palavras = re.findall(r'\b\w+\b', texto_limpo)
    return " ".join([
        w for w in palavras
        if len(w) >= tamanho_minimo and w.upper() not in STOPWORDS
    ])
