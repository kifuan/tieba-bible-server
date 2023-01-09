"""
Analyzes word counts from spider.json.
See README.md for detail information.
"""

import re
import jieba
import matplotlib.pyplot as plt

from typing import Generator
from pathlib import Path
from collections import Counter

from config import config
from database import Database


STOPWORDS_FILE = Path(__file__).parent / 'data' / 'stopwords.txt'
STOPWORDS = set(STOPWORDS_FILE.read_text('utf8').splitlines())
CHINESE_ENGLISH_NUMBER_REGEX = re.compile('[^\u4e00-\u9fa5a-zA-Z0-9]')


# Support for Chinese characters.
plt.rcParams['font.family'] = 'sans-serif'
# You can change it to other fonts.
plt.rcParams['font.sans-serif'] = config.analyzer.font_name


def cut_text(text: str) -> Generator[str, None, None]:
    words = jieba.cut(CHINESE_ENGLISH_NUMBER_REGEX.sub('', text))
    if config.analyzer.once_per_file:
        words = set(words)

    for word in words:
        yield word


def main() -> None:
    database = Database.get_instance()
    min_len = config.analyzer.min_word_length
    data = Counter(
        word for text in database
        for word in cut_text(text)
        if word not in STOPWORDS and len(word) >= min_len
    )
    items = sorted(
        data.items(),
        key=lambda item: item[1],
        reverse=True
    )[:config.analyzer.limit]

    if not items:
        raise ValueError('cannot get any data')

    words, counts = map(list, zip(*items))
    plt.bar(words, counts)
    plt.title(f'Top {config.analyzer.limit}')
    plt.show()


if __name__ == '__main__':
    main()
