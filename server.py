import uvicorn
import logging

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from pydantic import BaseModel
from typing import Union

from config import config
from database import Database


app = FastAPI()
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=config.server.allowed_hosts
)

# Use uvicorn logger.
logger = logging.getLogger('uvicorn')


async def get_db() -> Database:
    """
    It is used for dependency injection.
    :return: the database instance.
    """
    return await Database.get_instance()


class BodyAddCustomTexts(BaseModel):
    text: Union[str, list[str]]


@app.get('/text')
async def handle_text(keyword: str = '', db: Database = Depends(get_db)):
    if text := await db.get_random_text(keyword):
        return text

    return JSONResponse(
        content=f'no text contains given keyword {keyword}',
        status_code=404,
    )


@app.post('/text')
async def handle_add_custom_texts(body: BodyAddCustomTexts, db: Database = Depends(get_db)):
    texts = body.text
    if isinstance(texts, str):
        texts = [texts]

    max_length = config.server.max_custom_text_length
    if any(len(t) > max_length for t in texts):
        return JSONResponse(
            content=f'the max length of custom texts should be {max_length}',
            status_code=400,
        )

    await db.add_texts(texts)
    return ''


@app.get('/count')
async def handle_count(keyword: str = '', db: Database = Depends(get_db)):
    return await db.count(keyword)


if __name__ == '__main__':
    uvicorn.run(
        app='__main__:app',
        port=config.server.port,
    )
