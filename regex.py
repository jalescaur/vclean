import re
from pathlib import Path
from utils.wordcloud_utils import STOPWORDS

BASE_DIR = Path(__file__).parent

# --- Funções auxiliares ---

def _load_terms(file_path: Path) -> list[str]:
    """
    Lê cada linha não-vazia e não-comentada,
    faz escape para regex e retorna a lista de termos.
    """
    text = file_path.read_text(encoding='utf-8')
    terms = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        terms.append(re.escape(line.lower()))
    return terms


def _obfuscable_pattern(term: str) -> str:
    """
    Transforma `term` em um padrão que permite junk chars entre letras,
    ex.: "p[oO\.]*r[r]+a" etc.
    """
    escaped = re.escape(term.lower())
    return ''.join(f"{ch}[\W_]*" for ch in escaped)


# --- Padrões pré-compilados ---

# 1) Stoplist dinâmica (termos indesejados do STOPWORDS)
_stoplist_patterns = [_obfuscable_pattern(w) for w in STOPWORDS]
STOPLIST_PATTERN = re.compile(r'(?ix)\b(?:' + '|'.join(_stoplist_patterns) + r')\b')

# 2) Palavrões externos (via arquivo utils/profanities.txt)
PROFANITIES_FILE = BASE_DIR / 'utils' / 'profanities.txt'
_profane_terms = _load_terms(PROFANITIES_FILE)
# captura variações obfuscadas de palavrões (ex: f.u.c.k)
_profane_terms.append(r'f[\W_]*u[\W_]*c[\W_]*k')
PROFANITY_PATTERN = re.compile(r'(?ix)\b(?:' + '|'.join(_profane_terms) + r')\b')

# 3) Risadas (kkkk, hahaha, lol, rsrs…)
LAUGHTER_PATTERN = re.compile(r'''
    (?ix)           # ignore case + verbose
    \b
    (?:
        k{3,}         |  # kkkk...
        (?:ha){2,}    |  # hahaha...
        (?:he){2,}    |  # hehehe...
        lol+          |  # lol, lolll...
        lmao          |  # lmao
        rs{2,}           # rsrs...
    )
    \b
''', re.VERBOSE)

# 4) Tudo que não for letra ou espaço
NON_LETTER_PATTERN = re.compile(r'[^A-Za-zÀ-ÿ\s]+')


def preprocessar_texto(texto: str, tamanho_minimo: int = 3) -> str:
    """
    Pipeline de limpeza:
      0) Remove palavrões e variações
      1) Remove stopwords obfuscáveis
      2) Remove risadas
      3) Remove tudo que não for letra (mantém espaços)
      4) Tokeniza e filtra por tamanho mínimo e STOPWORDS
    """
    # 0) palavrões → espaço
    texto = PROFANITY_PATTERN.sub(' ', texto)
    # 1) stoplist obfuscável → espaço
    texto = STOPLIST_PATTERN.sub(' ', texto)
    # 2) risadas → espaço
    texto = LAUGHTER_PATTERN.sub(' ', texto)
    # 3) não-letras → espaço
    texto = NON_LETTER_PATTERN.sub(' ', texto)

    # 4) tokenização e filtragem final
    palavras = texto.split()
    filtradas = [
        w for w in palavras
        if len(w) >= tamanho_minimo and w.upper() not in STOPWORDS
    ]

    return ' '.join(filtradas)
