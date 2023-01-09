import uvicorn
import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from pydantic import BaseModel
from typing import Union

from config import config
from database import Database


app = FastAPI()
app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.server.allowed_hosts)

# Use uvicorn logger.
logger = logging.getLogger('uvicorn')


class BodyAddCustomTexts(BaseModel):
    text: Union[str, list[str]]


@app.on_event('startup')
async def init_database():
    # Initialize the database on startup.
    Database.get_instance()
    logger.info('Initialized database')


@app.on_event('shutdown')
async def close_database():
    Database.get_instance().close_database()
    logger.info('Closed database')


@app.get('/text')
async def handle_text(keyword: str = ''):
    if text := Database.get_instance().get_random_text(keyword):
        return text

    return JSONResponse(
        content=f'no text contains given keyword {keyword}',
        status_code=404,
    )


@app.post('/text')
async def handle_add_custom_texts(body: BodyAddCustomTexts):
    texts = body.text
    if isinstance(texts, str):
        texts = [texts]

    max_length = config.server.custom_text_max_length
    if any(len(t) > max_length for t in texts):
        return JSONResponse(
            content=f'the max length of custom texts should be {max_length}',
            status_code=400,
        )

    Database.get_instance().add_texts(texts)
    return ''


@app.get('/count')
async def handle_count(keyword: str = ''):
    return Database.get_instance().count(keyword)


if __name__ == '__main__':
    uvicorn.run(
        app='__main__:app',
        port=config.server.port,
    )
