import re
import ujson
import aiohttp
import asyncio
import aiotieba


from yarl import URL
from pathlib import Path

from config import config


ROOT_DIR = Path(__file__).parent

DATA_DIR = ROOT_DIR / 'data'

POSTS_DIR = DATA_DIR / 'posts'

SPIDER_FILE = DATA_DIR / 'spider.json'


# The regex to remove reply prefix.
REPLY_PREFIX_REGEX = re.compile(r'回复.+[:：]\s*')


def get_post_json(tid: int) -> Path:
    return POSTS_DIR / f'{tid}.json'


def save_file(tid: int, texts: list[str]) -> None:
    with open(get_post_json(tid), 'w', encoding='utf8') as f:
        ujson.dump(texts, f, ensure_ascii=False)


async def save_posts(client: aiotieba.Client, tid: int) -> None:
    if get_post_json(tid).exists():
        aiotieba.LOG.warning(f'tid {tid} exists')
        return

    page_number = 1
    texts = []
    while page_number <= config.spider.max_post_pages:
        await asyncio.sleep(1)
        posts = await client.get_posts(tid, pn=page_number)
        texts.extend(post.contents.text for post in posts)
        if not posts.has_more:
            break
        page_number += 1

    aiotieba.LOG.debug(f'saved post contents to {tid}.json.')
    save_file(tid, texts)


async def save_page(client: aiotieba.Client, name: str, page_number: int):
    threads = await client.get_threads(name, pn=page_number)
    for thread in threads:
        await save_posts(client, thread.tid)


async def save_pages(name: str, start_page: int, end_page: int) -> None:
    """
    Saves specified pages.
    :param name: the forum name.
    :param start_page: the start page number.
    :param end_page: the end page number.
    """

    async with aiotieba.Client('default') as client:
        for page in range(start_page, end_page + 1):
            aiotieba.LOG.debug(f'saving page {page}.')
            await save_page(client, name, page)


def merge_posts() -> None:
    """
    Merge all posts the spider fetched in JSON files.
    """

    with SPIDER_FILE.open('w', encoding='utf8') as f:
        # Remove reply prefixes for all texts.
        processed_dataset = {
            REPLY_PREFIX_REGEX.sub('', item.strip())
            for file in POSTS_DIR.iterdir() if file.suffix == '.json'
            for item in ujson.loads(file.read_text('utf8'))
        }
        # Remove empty texts by the simple condition.
        dataset = [text for text in processed_dataset if text]
        ujson.dump(dataset, f, ensure_ascii=False)
    aiotieba.LOG.info('merged all posts.')


async def refresh_server_if_configured() -> None:
    """
    Reloads the server if config.spider.reload_server is set to true.
    """

    if not config.spider.reload_server:
        return

    url = str(URL.build(
        scheme='http',
        host=config.server.host,
        port=config.server.port,
        path='/reload'
    ))
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as resp:
            if resp.status != 200:
                aiotieba.LOG.error('failed to reload the server')
                return
            len_diff = await resp.json(encoding='utf8')

    aiotieba.LOG.info(f'added {len_diff} texts.')


async def start_spider():
    try:
        await save_pages(config.spider.forum_name, config.spider.start_page, config.spider.end_page)
    finally:
        merge_posts()
        await refresh_server_if_configured()


if __name__ == '__main__':
    asyncio.run(start_spider())
