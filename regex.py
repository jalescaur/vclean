import re

def clean_text(text):
    """
    Função para remover risadas do texto.
    """
    regex = r'''(?ix)
        (?<!\w)
        \b
        (
            k{4,}                                     # pelo menos 4 'k'
            |hah?a+h?a+                               # risadas tipo 'haha'
            |[a-z]{0,}[hku][ae][a-z]{2,}              # sons tipo 'hue', 'kae', com pelo menos 4 caracteres
            |[a-z]{4,}                                # qualquer palavra com 4+ letras
            |[a-zA-Z][áéíóúàèìòùâêîôûãõäëïöüñç]       # letras com acento
            |[áéíóúàèìòùâêîôûãõäëïöüñç]{2,}           # acentuadas com mínimo 2 caracteres
            |\b[a-zA-Z]\d{3,}                         # letra seguida de 3+ números
            |\b\d{3,}[a-zA-Z]                         # número seguido de letra
        )
        \b
        (?!\w)
    '''
    return re.sub(regex, '', text)

