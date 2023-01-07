import ujson

from pathlib import Path


DATA = Path(__file__).parent / 'data'
RAW = DATA / 'raw'
DATASET = DATA / 'dataset.json'


def merge():
    texts = list({
        item
        for file in RAW.iterdir() if file.suffix == '.json'
        for item in ujson.loads(file.read_text('utf8')) if item.strip() != ''
    })

    with DATASET.open('w', encoding='utf8') as f:
        ujson.dump(texts, f, ensure_ascii=False)


if __name__ == '__main__':
    merge()
