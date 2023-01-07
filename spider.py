import ujson
import asyncio
import aiotieba
from pathlib import Path


DATA = Path(__file__).parent / 'data' / 'raw'


def check_if_exists(tid: int):
    return (DATA / f'{tid}.json').exists()


def save_file(tid: int, texts: list[str]) -> None:
    filepath = DATA / f'{tid}.json'
    with open(filepath, 'w', encoding='utf8') as f:
        ujson.dump(texts, f, ensure_ascii=False)


async def get_posts(client: aiotieba.Client, tid: int, total_pages: int) -> None:
    if check_if_exists(tid):
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


async def get_page(client: aiotieba.Client, name: str, page_number: int = 1, total_posts_pages: int = 20):
    threads = await client.get_threads(name, pn=page_number)
    for thread in threads:
        await get_posts(client, thread.tid, total_posts_pages)


async def main(name: str):
    async with aiotieba.Client('default') as client:
        for i in range(31, 40):
            aiotieba.LOG.debug(f'saving page {i}')
            await get_page(client, name, i)


if __name__ == '__main__':
    asyncio.run(main('复制粘贴'))
