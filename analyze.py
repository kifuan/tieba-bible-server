"""
Analyzes word counts from spider.json.
See README.md for detail information.
"""

import re
import ujson
import jieba
import matplotlib.pyplot as plt

from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent
SPIDER_FILE = ROOT / 'data' / 'spider.json'
STOPWORDS_FILE = ROOT / 'stopwords.txt'
STOPWORDS = set(STOPWORDS_FILE.read_text('utf8').splitlines())
CHINESE_ENGLISH_NUMBER_REGEX = re.compile('[^\u4e00-\u9fa5a-zA-Z0-9]')

# You can change these two variables.
FONT = 'Microsoft YaHei'
LIMIT = 30


# Support for Chinese characters.
plt.rcParams['font.family'] = 'sans-serif'
# You can change it to other fonts.
plt.rcParams['font.sans-serif'] = FONT


def main():
    data = Counter(
        word
        for line in ujson.loads(SPIDER_FILE.read_text('utf8'))
        for word in jieba.cut(CHINESE_ENGLISH_NUMBER_REGEX.sub('', line))
        if word not in STOPWORDS and not word.isspace()
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
