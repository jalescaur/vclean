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

# --- Padrões de stoplist (dinâmico) ---
_stoplist_patterns = [_obfuscable_pattern(w) for w in STOPWORDS]
# correspondência em palavra inteira
STOPLIST_PATTERN = re.compile(r'(?ix)\b(?:' + '|'.join(_stoplist_patterns) + r')\b')
# correspondência dentro de substrings
SUBSTR_STOPLIST_PATTERN = re.compile(r'(?ix)(?:' + '|'.join(_stoplist_patterns) + r')')

# --- Carregamento de profanidades externas ---
PROFANITIES_FILE = BASE_DIR / 'utils' / 'profanities.txt'
if PROFANITIES_FILE.is_file():
    _profane_terms = _load_terms(PROFANITIES_FILE)
else:
    _profane_terms = []
# adiciona obfuscação para 'fuck'
_profane_terms.append(r'f[\W_]*u[\W_]*c[\W_]*k')
# padrões de profanidade
PROFANITY_PATTERN = re.compile(r'(?ix)\b(?:' + '|'.join(_profane_terms) + r')\b')
SUBSTR_PROFANITY_PATTERN = re.compile(r'(?ix)(?:' + '|'.join(_profane_terms) + r')')

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
      0) Remove palavrões (whole-word)
      1) Remove palavrões (substring)
      2) Remove stoplist (whole-word)
      3) Remove stoplist (substring)
      4) Remove risadas
      5) Remove tudo que não for letra
      6) Tokeniza e filtra por tamanho mínimo e STOPWORDS
    """
    texto = PROFANITY_PATTERN.sub(' ', texto)
    texto = SUBSTR_PROFANITY_PATTERN.sub(' ', texto)
    texto = STOPLIST_PATTERN.sub(' ', texto)
    texto = SUBSTR_STOPLIST_PATTERN.sub(' ', texto)
    texto = LAUGHTER_PATTERN.sub(' ', texto)
    texto = NON_LETTER_PATTERN.sub(' ', texto)

    palavras = texto.split()
    filtradas = [
        w for w in palavras
        if len(w) >= tamanho_minimo and w.upper() not in STOPWORDS
    ]

    return ' '.join(filtradas)
