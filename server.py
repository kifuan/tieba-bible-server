import uvicorn

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from config import config
from database import Database


app = FastAPI()
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=config.server.allowed_hosts
)


async def get_db() -> Database:
    """
    It is used for dependency injection.
    :return: the database instance.
    """

    return await Database.get_instance()


@app.get('/text')
async def handle_text(keyword: str = '', short: bool = False, db: Database = Depends(get_db)):
    if text := await db.get_random_text(keyword, short):
        return text

    return JSONResponse(
        content=f'no text contains given keyword {keyword}',
        status_code=404,
    )


@app.get('/count')
async def handle_count(keyword: str = '', short: bool = False, db: Database = Depends(get_db)):
    return await db.count(keyword, short)


if __name__ == '__main__':
    uvicorn.run(
        app='__main__:app',
        port=config.server.port,
    )
