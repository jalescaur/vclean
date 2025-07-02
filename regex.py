import re
from pathlib import Path
from utils.wordcloud_utils import STOPWORDS

BASE_DIR = Path(__file__).parent

# --- Funções auxiliares ---

def _load_terms(file_path: Path) -> list[str]:
    text = file_path.read_text(encoding='utf-8')
    terms = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        terms.append(re.escape(line.lower()))
    return terms


def _obfuscable_pattern(term: str) -> str:
    escaped = re.escape(term.lower())
    return ''.join(f"{ch}[\W_]*" for ch in escaped)

# --- Stoplist dinâmico (termos indesejados) ---
_stoplist_patterns = [_obfuscable_pattern(w) for w in STOPWORDS]
# whole-word match (token exato)
STOPLIST_PATTERN = re.compile(r'(?ix)\b(?:' + '|'.join(_stoplist_patterns) + r')\b')
# substring match (remover tokens que contenham o termo)
SUBSTR_STOPLIST_PATTERN = re.compile(r'(?ix)\b\w*(?:' + '|'.join(_stoplist_patterns) + r')\w*\b')

# --- Palavrões externos (via utils/profanities.txt) ---
PROFANITIES_FILE = BASE_DIR / 'utils' / 'profanities.txt'
if PROFANITIES_FILE.is_file():
    _profane_terms = _load_terms(PROFANITIES_FILE)
else:
    _profane_terms = []
# adiciona obfuscação para 'fuck'
_profane_terms.append(r'f[\W_]*u[\W_]*c[\W_]*k')
# whole-word match
PROFANITY_PATTERN = re.compile(r'(?ix)\b(?:' + '|'.join(_profane_terms) + r')\b')
# substring match (tokens que contenham o termo)
SUBSTR_PROFANITY_PATTERN = re.compile(r'(?ix)\b\w*(?:' + '|'.join(_profane_terms) + r')\w*\b')

# --- Risadas ---
LAUGHTER_PATTERN = re.compile(r'''
    (?ix)
    \b
    (?:
        k{3,}
      | (?:ha){2,}
      | (?:he){2,}
      | lol+
      | lmao
      | rs{2,}
    )
    \b
''', re.VERBOSE)

# --- Não-letras ---
NON_LETTER_PATTERN = re.compile(r'[^A-Za-zÀ-ÿ\s]+')


def preprocessar_texto(texto: str, tamanho_minimo: int = 3) -> str:
    """
    Pipeline de limpeza:
      0) Remove palavrões (whole-word e substring)
      1) Remove stoplist (whole-word e substring)
      2) Remove risadas
      3) Remove tudo que não for letra
      4) Tokeniza e filtra por tamanho mínimo e STOPWORDS
    """
    # 0) profanidades
    texto = PROFANITY_PATTERN.sub(' ', texto)
    texto = SUBSTR_PROFANITY_PATTERN.sub(' ', texto)
    # 1) stoplist dinâmica
    texto = STOPLIST_PATTERN.sub(' ', texto)
    texto = SUBSTR_STOPLIST_PATTERN.sub(' ', texto)
    # 2) risadas
    texto = LAUGHTER_PATTERN.sub(' ', texto)
    # 3) não-letras
    texto = NON_LETTER_PATTERN.sub(' ', texto)

    # 4) tokenização e filtragem final
    palavras = texto.split()
    filtradas = [
        w for w in palavras
        if len(w) >= tamanho_minimo and w.upper() not in STOPWORDS
    ]

    return ' '.join(filtradas)
