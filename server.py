import ujson
import random
import uvicorn

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, Response

from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Iterator


ROOT = Path(__file__).parent

# Configurations for the server.
CONFIG = ujson.loads((ROOT / 'config.json').read_text('utf8'))['server']

# Custom texts file.
CUSTOM_FILE = ROOT / 'data' / 'custom.json'

# Dataset file from the spider.
SPIDER_FILE = ROOT / 'data' / 'spider.json'

# Uvicorn port.
PORT = CONFIG['port']

# Keywords to cache.
CACHED_KEYWORDS = CONFIG['cached_keywords']

app = FastAPI()


class Dataset:
    """
    The dataset to record data from both spider and user.
    """

    _instance: Optional['Dataset'] = None

    def __init__(self, spider: list[str], custom: list[str]):
        self._spider = spider
        self._custom = custom
        self._caches: dict[str, list[str]] = {}

    @classmethod
    def get_instance(cls) -> 'Dataset':
        """
        Gets dataset instance, which is singleton.
        :return: the instance.
        """

        if cls._instance is not None:
            return cls._instance

        if not SPIDER_FILE.exists():
            raise FileNotFoundError('spider.json not found, please run spider.py first')

        spider = ujson.loads(SPIDER_FILE.read_text('utf8'))
        custom = ujson.loads(CUSTOM_FILE.read_text('utf8'))
        return cls(spider, custom)

    def get_keyword(self, keyword: str) -> list[str]:
        """
        Gets data filtered with specified keyword.
        :param keyword: the keyword to filter.
        :return: filtered data.
        """

        # Check if the keyword was cached first.
        if keyword in self._caches:
            return self._caches[keyword]

        result = [text for text in self if keyword in text]

        # Cache the keyword if specified.
        if keyword in CACHED_KEYWORDS:
            print(f'cached keyword {keyword}')
            self._caches[keyword] = result

        return result

    def add_custom_texts(self, texts: list[str]) -> None:
        """
        Adds custom texts by the user.
        :param texts: the texts to add.
        """

        self._custom.extend(texts)

        # Clear caches to ensure that new contents will be loaded.
        self._caches.clear()

        # Update contents to the file.
        content = ujson.dumps(self._custom, ensure_ascii=False)
        CUSTOM_FILE.write_text(content, encoding='utf8')

    def __iter__(self) -> Iterator[str]:
        """
        Iterates through `self._spider` and `self._custom`.
        :return: the iterator.
        """

        for text in self._spider:
            yield text

        for text in self._custom:
            yield text


class BodyAddCustomTexts(BaseModel):
    texts: list[str]


@app.get('/text')
async def handle_text(keyword: str = ''):
    if matches := Dataset.get_instance().get_keyword(keyword):
        return random.choice(matches)
    return PlainTextResponse(f'No text has matched keyword {keyword}.', 404)


@app.post('/text')
async def handle_add_custom_texts(body: BodyAddCustomTexts):
    Dataset.get_instance().add_custom_texts(body.texts)
    return Response()


@app.get('/count')
async def handle_count(keyword: str = ''):
    return len(Dataset.get_instance().get_keyword(keyword))


if __name__ == '__main__':
    uvicorn.run('__main__:app', port=PORT)
