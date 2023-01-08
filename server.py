import uvicorn
import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from pydantic import BaseModel
from typing import Union

from config import config
from dataset import Dataset


app = FastAPI()
app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.server.allowed_hosts)

# Use uvicorn logger.
logger = logging.getLogger('uvicorn')


class BodyAddCustomTexts(BaseModel):
    text: Union[str, list[str]]


@app.on_event('startup')
async def init_dataset():
    # Initialize the dataset on startup.
    Dataset.get_instance()
    logger.info('Initialized dataset')


@app.on_event('shutdown')
async def close_dataset():
    Dataset.get_instance().close_dataset()
    logger.info('Closed dataset')


@app.get('/text')
async def handle_text(keyword: str = ''):
    if text := Dataset.get_instance().get_random_text(keyword):
        return text

    return JSONResponse(
        content=f'no text contains given keyword {keyword}',
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
            content=f'max size of custom texts should be {max_size}',
            status_code=400
        )

    Dataset.get_instance().add_texts(texts)
    return ''


@app.get('/count')
async def handle_count(keyword: str = ''):
    return Dataset.get_instance().count_keyword(keyword)


if __name__ == '__main__':
    uvicorn.run(
        app='__main__:app',
        port=config.server.port,
    )
