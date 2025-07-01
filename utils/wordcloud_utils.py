# utils/wordcloud_utils.py
import os
from random import choice
from wordcloud import WordCloud

def load_stoplist():
    path = os.path.join(os.path.dirname(__file__), '..', 'stoplist.txt')
    with open(path, 'r', encoding='utf-8') as f:
        return set(line.strip().upper() for line in f if line.strip())

STOPWORDS = load_stoplist()

def generate_wordcloud(
    text: str,
    output_path: str,
    font_path: str = os.path.join('assets','fonts','aptos-bold.ttf'),
    colors: list = ['#26619C', '#C5C6D0'],
    width: int = 800,
    height: int = 400
):
    """Gera PNG transparente em upper case, fonte Aptos Bold e stopwords."""
    wc = WordCloud(
        width=width, height=height,
        background_color=None, mode='RGBA',
        stopwords=STOPWORDS,
        font_path=font_path
    ).generate(text.upper())

    wc = wc.recolor(color_func=lambda *args, **kwargs: choice(colors))
    wc.to_file(output_path)
