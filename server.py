import ujson
import random
import uvicorn
import asyncio

from fastapi import FastAPI
from fastapi.logger import logger
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Iterator, Union

from config import config


DATA_DIR = Path(__file__).parent / 'data'

CUSTOM_FILE = DATA_DIR / 'custom.json'

SPIDER_FILE = DATA_DIR / 'spider.json'


app = FastAPI()
app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.server.allowed_hosts)

# Keep a global variable reference to the task to avoid being collected by GC.
spider_task: Optional[asyncio.Task] = None


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
            logger.warn('you have not run spider.py yet, please run it when the server is running')
            SPIDER_FILE.write_text('[]', encoding='utf8')

        if not CUSTOM_FILE.exists():
            # The content of custom.json is just an empty array by default.
            CUSTOM_FILE.write_text('[]', encoding='utf8')

        spider = ujson.loads(SPIDER_FILE.read_text('utf8'))
        custom = ujson.loads(CUSTOM_FILE.read_text('utf8'))
        return cls(spider, custom)

    def reload_spider_data(self) -> None:
        """
        Reloads spider data.
        """

        self._spider = ujson.loads(SPIDER_FILE.read_text('utf8'))

    def get_keyword(self, keyword: str) -> list[str]:
        """
        Gets data filtered by specified keyword.
        :param keyword: the keyword to filter.
        :return: filtered data.
        """

        # Check if the keyword was cached first.
        if keyword in self._caches:
            return self._caches[keyword]

        result = [text for text in self if keyword in text]

        # Cache the keyword if specified.
        if keyword in config.server.cached_keywords:
            self._caches[keyword] = result

        return result

    def add_custom_texts(self, texts: list[str]) -> None:
        """
        Adds custom texts from the user.
        :param texts: the texts to add.
        """

        self._custom.extend(texts)

        # Clear caches to ensure that new contents will be loaded.
        self._caches.clear()

        # Update contents to the file.
        content = ujson.dumps(self._custom, ensure_ascii=False)
        CUSTOM_FILE.write_text(content, encoding='utf8')

    def __len__(self):
        return len(self._spider) + len(self._custom)

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
    text: Union[str, list[str]]


@app.get('/text')
async def handle_text(keyword: str = ''):
    if texts := Dataset.get_instance().get_keyword(keyword):
        return random.choice(texts)

    return JSONResponse(
        content=f'no text has matched the specified keyword {keyword}',
        status_code=404
    )


@app.post('/text')
async def handle_add_custom_texts(body: BodyAddCustomTexts):
    texts = body.text
    if isinstance(texts, str):
        texts = [texts]

    max_size = config.server.custom_text_max_size
    if any(len(t) > max_size for t in texts):
        return JSONResponse(
            content=f'max size of custom text is {max_size}',
            status_code=400
        )

    Dataset.get_instance().add_custom_texts(texts)
    return ''


@app.get('/count')
async def handle_count(keyword: str = ''):
    return len(Dataset.get_instance().get_keyword(keyword))


@app.post('/reload')
async def handle_reload():
    dataset = Dataset.get_instance()
    len1 = len(dataset)
    dataset.reload_spider_data()
    return len(dataset) - len1


if __name__ == '__main__':
    uvicorn.run('__main__:app', port=config.server.port)
