import ujson
import random
import uvicorn

from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from functools import cache


# Uvicorn port.
PORT = 8003

# Keywords to cache.
CACHED_KEYWORDS = ['原神', '压缩毛巾']

# Cached datasets. It will be updated at runtime when matches keyword in `CACHED_KEYWORDS`
CACHED_DATASETS = {}

app = FastAPI()


@cache
def load_dataset() -> list[str]:
    path = Path(__file__).parent / 'data' / 'dataset.json'
    if not path.exists():
        raise FileNotFoundError('no dataset.json, please run merge.py first.')
    return ujson.loads(path.read_text('utf8'))


def load_keyword_dataset(keyword: str) -> list[str]:
    dataset = load_dataset()

    if not keyword:
        return dataset

    if keyword in CACHED_DATASETS:
        return CACHED_DATASETS[keyword]

    dataset = [text for text in dataset if keyword in text]

    # Cache it at the first time, and it will use cached data next time.
    if keyword in CACHED_KEYWORDS:
        CACHED_DATASETS[keyword] = dataset

    return dataset


@app.get('/')
async def handle_text(keyword: str = ''):
    if dataset := load_keyword_dataset(keyword):
        return random.choice(dataset)
    return PlainTextResponse(f'No text has matched keyword {keyword}', 404)

if __name__ == '__main__':
    uvicorn.run('__main__:app', port=PORT)
