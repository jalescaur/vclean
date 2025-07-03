import re
from pathlib import Path
from utils.wordcloud_utils import STOPWORDS

BASE_DIR = Path(__file__).parent

# --- Funções auxiliares ---

def _load_terms(file_path: Path) -> list[str]:
    """
    Lê linhas não vazias/não comentadas e retorna lista de termos em minúsculas.
    """
    text = file_path.read_text(encoding='utf-8')
    return [line.strip().lower() for line in text.splitlines() if line.strip() and not line.startswith('#')]


def _obfuscable_pattern(term: str) -> str:
    """
    Gera padrão que permite junk chars entre letras, ex.: "p.o.r.r.a".
    """
    return ''.join(f"{re.escape(ch)}[\W_]*" for ch in term)

# --- Carrega profanidades ---
PROFANITIES_FILE = BASE_DIR / 'utils' / 'profanities.txt'
profanities = _load_terms(PROFANITIES_FILE) if PROFANITIES_FILE.is_file() else []
# incluindo variações de 'fuck'
profanities.append('fuck')
profane_patterns = [_obfuscable_pattern(term) for term in profanities]
PROFANITY_PATTERN = re.compile(r'(?i)(?:' + '|'.join(profane_patterns) + r')')

# --- Padrões de tokens indesejados ---
# risadas completas
LAUGHTER_PATTERN = re.compile(r'(?i)^(?:k{3,}|(?:ha){2,}|(?:he){2,}|lol+|lmao|rs{2,}|rsrs)$')
# repetições de mesma letra
REPEAT_PATTERN = re.compile(r'(?i)^([a-zà-ÿ])\1{2,}$')
# remove qualquer caractere não letra/espaço
NON_LETTER_PATTERN = re.compile(r'[^a-zà-ÿ\s]+')


def preprocessar_texto(texto: str, tamanho_minimo: int = 3) -> str:
    """
    Limpa e filtra tokens para wordcloud:
      1) Lowercase e remove não-letras
      2) Tokeniza por espaço
      3) Filtra:
           - tamanho < tamanho_minimo
           - em STOPWORDS (exato, uppercase)
           - corresponde a PROFANITY_PATTERN
           - corresponde a REPEAT_PATTERN
           - corresponde a LAUGHTER_PATTERN
      4) Retorna texto limpo
    """
    texto = texto.lower()
    texto = NON_LETTER_PATTERN.sub(' ', texto)
    tokens = texto.split()
    clean_tokens = []
    for w in tokens:
        if len(w) < tamanho_minimo:
            continue
        if w.upper() in STOPWORDS:
            continue
        if PROFANITY_PATTERN.search(w):
            continue
        if REPEAT_PATTERN.match(w):
            continue
        if LAUGHTER_PATTERN.match(w):
            continue
        clean_tokens.append(w)
    return ' '.join(clean_tokens)
