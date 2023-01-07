import ujson
import random
import uvicorn

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse


def load_dataset() -> list[str]:
    path = Path(__file__).parent / 'data' / 'dataset.json'
    if not path.exists():
        raise FileNotFoundError('no dataset.json, please run merge.py first.')
    return ujson.loads(path.read_text('utf8'))


# Uvicorn port.
PORT = 8003

# All texts.
DATASET = load_dataset()


app = FastAPI()


@app.get('/')
async def handle_text(keyword: str = ''):
    if not keyword:
        return random.choice(DATASET)

    dataset = [text for text in DATASET if keyword in text]
    if dataset:
        return random.choice(dataset)

    return PlainTextResponse(f'No text has matched keyword {keyword}', 404)

if __name__ == '__main__':
    uvicorn.run('__main__:app', port=PORT)
