import re

def clean_text(text):
    """
    Função para remover risadas do texto.
    """
    regex = r'(?i)\b(?:k{1,}|hah?a+h?a+|a?[a-z]*(?:h[ae]|k[ae]|u[ae])+[a-z]*)\b'
    return re.sub(regex, '', text)

