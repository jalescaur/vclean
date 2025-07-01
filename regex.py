import re

def clean_text(text):
    """
    Remove risadas do texto, como 'kkkk', 'hahaha', 'huahuahua', etc.
    """
    regex = r'''(?ix)
        (?<!\w)
        (
            (k){3,}                # kkkk, kkkkkk
            |(ha){2,}              # hahaha, hahahaha
            |(h[ae]{1,2}){2,}      # hehehe, huehue, hahaha
            |(rs){2,}              # rsrsrs
            |(ua){2,}              # uaua, uauaua
        )
        (?!\w)
    '''
    return re.sub(regex, '', text).strip()

def remove_palavras_curtas(texto: str, tamanho_minimo: int = 4) -> str:
    """
    Remove palavras com menos de `tamanho_minimo` letras.
    """
    return " ".join([
        w for w in re.findall(r'\b\w+\b', texto)
        if len(w) >= tamanho_minimo
    ])
