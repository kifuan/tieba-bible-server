import ujson
import random
import uvicorn

from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from functools import cache

CONFIG = ujson.loads((Path(__file__).parent / 'config.json').read_text('utf8'))['server']

# Uvicorn port.
PORT = CONFIG['port']

# Keywords to cache.
CACHED_KEYWORDS = CONFIG['cached_keywords']

# Cached datasets. It will be updated at runtime when matches keyword in `CACHED_KEYWORDS`
CACHED_DATASETS = {}

app = FastAPI()


@cache
def load_dataset_file() -> list[str]:
    """
    Loads dataset from file.
    The result will be cached, so it's ok to call it multiple times.
    :return: the dataset from file.
    """

    path = Path(__file__).parent / 'data' / 'dataset.json'
    if not path.exists():
        raise FileNotFoundError('no dataset.json, please run spider.py first.')
    return ujson.loads(path.read_text('utf8'))


def load_keyword_dataset(keyword: str) -> list[str]:
    """
    Loads dataset for specified keyword.
    :param keyword: the keyword to load dataset.
    :return: the dataset for specified keyword.
    """

    dataset = load_dataset_file()

    if not keyword:
        return dataset

    if keyword in CACHED_DATASETS:
        return CACHED_DATASETS[keyword]

    dataset = [text for text in dataset if keyword in text]

    # Cache it at the first time, and it will use cached data next time.
    if keyword in CACHED_KEYWORDS:
        CACHED_DATASETS[keyword] = dataset

    return dataset


@app.get('/text')
async def handle_text(keyword: str = ''):
    """
    Gets specified text.
    :param keyword:
    :return:
    """
    if dataset := load_keyword_dataset(keyword):
        return random.choice(dataset)
    return PlainTextResponse(f'No text has matched keyword {keyword}', 404)


@app.get('/count')
async def handle_count(keyword: str = ''):
    """
    Gets count for specified keyword.
    :param keyword: the keyword to count.
    :return: the count of specified keyword in the dataset.
    """
    return len(load_keyword_dataset(keyword))


if __name__ == '__main__':
    uvicorn.run('__main__:app', port=PORT)
