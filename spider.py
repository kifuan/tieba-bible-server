import ujson
import asyncio
import aiotieba

from pathlib import Path


DATA_DIR = Path(__file__).parent / 'data'
POSTS_DIR = DATA_DIR / 'posts'
DATASET_FILE = DATA_DIR / 'dataset.json'


def get_post_json(tid: int) -> Path:
    return POSTS_DIR / f'{tid}.json'


def save_file(tid: int, texts: list[str]) -> None:
    with open(get_post_json(tid), 'w', encoding='utf8') as f:
        ujson.dump(texts, f, ensure_ascii=False)


async def save_posts(client: aiotieba.Client, tid: int, total_pages: int) -> None:
    if get_post_json(tid).exists():
        aiotieba.LOG.warning(f'tid {tid} exists')
        return

    page_number = 1
    texts = []
    while page_number <= total_pages:
        await asyncio.sleep(1)
        posts = await client.get_posts(tid, pn=page_number)
        texts.extend(post.text for post in posts)
        if not posts.has_more:
            break
        page_number += 1

    aiotieba.LOG.debug(f'saved {tid}.json')
    save_file(tid, texts)


async def save_page(client: aiotieba.Client, name: str, page_number: int = 1, total_posts_pages: int = 20):
    threads = await client.get_threads(name, pn=page_number)
    for thread in threads:
        await save_posts(client, thread.tid, total_posts_pages)


async def save_pages(name: str, page_start: int, page_end: int = -1) -> None:
    """
    Saves specified pages.
    It will only save `page_start` if `page_end` is set to -1 by default.
    :param name: the forum name.
    :param page_start: the start page number.
    :param page_end: the end page number.
    """

    if page_end == -1:
        page_end = page_start

    async with aiotieba.Client('default') as client:
        for page in range(page_start, page_end + 1):
            aiotieba.LOG.debug(f'saving page {page}')
            await save_page(client, name, page)

    # Merge all posts.
    with DATASET_FILE.open('w', encoding='utf8') as f:
        dataset = list({
            item.strip()
            for file in POSTS_DIR.iterdir() if file.suffix == '.json'
            for item in ujson.loads(file.read_text('utf8')) if item.strip() != ''
        })
        ujson.dump(dataset, f, ensure_ascii=False)


if __name__ == '__main__':
    asyncio.run(save_pages('复制粘贴', 1))
