import ujson
import random
import uvicorn

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Iterator, Union


ROOT = Path(__file__).parent

CONFIG_FILE = ROOT / 'config.json'

CUSTOM_FILE = ROOT / 'data' / 'custom.json'

SPIDER_FILE = ROOT / 'data' / 'spider.json'


class ServerConfig(BaseModel):
    # Server port.
    port: int

    # Max size for custom-upload texts.
    custom_text_max_size: int

    # Keywords to be cached.
    cached_keywords: list[str]

    # Allowed hosts for security.
    allowed_hosts: list[str]


config = ServerConfig.parse_obj(ujson.loads(CONFIG_FILE.read_text('utf8'))['server'])

app = FastAPI()
app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.allowed_hosts)


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

        if not CUSTOM_FILE.exists():
            # The content of custom.json is just an empty array by default.
            CUSTOM_FILE.write_text('[]', encoding='utf8')

        spider = ujson.loads(SPIDER_FILE.read_text('utf8'))
        custom = ujson.loads(CUSTOM_FILE.read_text('utf8'))
        return cls(spider, custom)

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
        if keyword in config.cached_keywords:
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
        return PlainTextResponse(
            content=random.choice(texts)
        )

    return PlainTextResponse(
        content=f'no text has matched the specified keyword {keyword}',
        status_code=404
    )


@app.post('/text')
async def handle_add_custom_texts(body: BodyAddCustomTexts):
    texts = body.text
    if isinstance(texts, str):
        texts = [texts]

    max_size = config.custom_text_max_size
    if any(len(t) > max_size for t in texts):
        return PlainTextResponse(
            content=f'max size of custom text is {max_size}',
            status_code=400
        )

    Dataset.get_instance().add_custom_texts(texts)
    return PlainTextResponse()


@app.get('/count')
async def handle_count(keyword: str = ''):
    data = Dataset.get_instance().get_keyword(keyword)
    return PlainTextResponse(
        content=str(len(data))
    )


if __name__ == '__main__':
    uvicorn.run('__main__:app', port=config.port, host='0.0.0.0')
