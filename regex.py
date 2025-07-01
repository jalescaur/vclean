import re

def clean_text(text):
    """
    Função para remover risadas do texto.
    """
    regex = r'(?i)(?<!\w)\b(?:k{1,}|hah?a+h?a+|a?[a-z]*(?:h[ae]|k[ae]|u[ae])+[a-z]*)\b|(?:[a-zA-Z][áéíóúàèìòùâêîôûãõäëïöüñç]|[áéíóúàèìòùâêîôûãõäëïöüñç]|\b[a-zA-Z]\d|\d[a-zA-Z]\b)(?!\w)'
    return re.sub(regex, '', text)

