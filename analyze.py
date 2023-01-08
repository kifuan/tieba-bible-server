"""
Analyzes word counts from spider.json.
See README.md for detail information.
"""

import re
import jieba
import matplotlib.pyplot as plt

from pathlib import Path
from database import Database
from collections import Counter


STOPWORDS_FILE = Path(__file__).parent / 'data' / 'stopwords.txt'
STOPWORDS = set(STOPWORDS_FILE.read_text('utf8').splitlines())
CHINESE_ENGLISH_NUMBER_REGEX = re.compile('[^\u4e00-\u9fa5a-zA-Z0-9]')

# You can change these two variables.
FONT = 'Microsoft YaHei'
LIMIT = 30
MIN_WORD_LEN = 2


# Support for Chinese characters.
plt.rcParams['font.family'] = 'sans-serif'
# You can change it to other fonts.
plt.rcParams['font.sans-serif'] = FONT


def main():
    database = Database.get_instance()
    data = Counter(
        word for line in database
        for word in jieba.cut(CHINESE_ENGLISH_NUMBER_REGEX.sub('', line))
        if word not in STOPWORDS and len(word) >= MIN_WORD_LEN
    )
    items = sorted(data.items(), key=lambda item: item[1], reverse=True)[:LIMIT]
    if not items:
        raise ValueError('cannot get any data')
    words, counts = map(list, zip(*items))
    plt.bar(words, counts)
    plt.title(f'Top {LIMIT}')
    plt.show()


if __name__ == '__main__':
    main()
