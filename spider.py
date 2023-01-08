import re
import ujson
import asyncio
import aiotieba

from typing import AsyncIterator
from pathlib import Path

from config import config
from dataset import Dataset


ROOT_DIR = Path(__file__).parent

DATA_DIR = ROOT_DIR / 'data'

POSTS_DIR = DATA_DIR / 'posts'


# The regex to remove reply prefix.
REPLY_PREFIX_REGEX = re.compile(r'回复.+[:：]\s*')


def get_post_json(tid: int) -> Path:
    return POSTS_DIR / f'{tid}.json'


async def get_and_save_posts(tid: int, texts: AsyncIterator[str]) -> list[str]:
    """
    Saves posts in tid.json and returns the list of texts.
    :param tid: the thread id.
    :param texts: the async generator of texts.
    """

    list_texts = [text async for text in texts]
    with open(get_post_json(tid), 'w', encoding='utf8') as f:
        ujson.dump(list_texts, f, ensure_ascii=False)
    return list_texts


async def get_posts(client: aiotieba.Client, tid: int) -> AsyncIterator[str]:
    if get_post_json(tid).exists():
        aiotieba.LOG.warning(f'The tid {tid} exists.')
        return

    page_number = 1
    while page_number <= config.spider.max_post_pages:
        await asyncio.sleep(1)
        posts = await client.get_posts(tid, pn=page_number)
        for post in posts:
            yield post.contents.text
        if not posts.has_more:
            break
        page_number += 1

    aiotieba.LOG.debug(f'Saved post contents to {tid}.json.')


async def save_page(client: aiotieba.Client, name: str, page_number: int) -> None:
    dataset = Dataset.get_instance()
    aiotieba.LOG.debug(f'Saving page {page_number}.')
    threads = await client.get_threads(name, pn=page_number, sort=1)
    for thread in threads:
        texts = await get_and_save_posts(thread.tid, get_posts(client, thread.tid))
        dataset.add_texts(texts)


async def save_pages(name: str, start_page: int, end_page: int) -> None:
    """
    Saves specified pages.
    :param name: the forum name.
    :param start_page: the start page number.
    :param end_page: the end page number.
    """

    async with aiotieba.Client('default') as client:
        for page in range(start_page, end_page + 1):
            await save_page(client, name, page)


def merge_posts() -> None:
    """
    Merge all posts the spider fetched in JSON files.
    """
    dataset = Dataset.get_instance()
    # Remove reply prefixes for all texts.
    processed_dataset = {
        REPLY_PREFIX_REGEX.sub('', item.strip())
        for file in POSTS_DIR.iterdir() if file.suffix == '.json'
        for item in ujson.loads(file.read_text('utf8'))
    }
    # Remove empty texts by the simple condition.
    len1 = len(dataset)
    dataset.add_texts(text for text in processed_dataset if text)
    aiotieba.LOG.info(f'Added {len(dataset) - len1} texts.')


if __name__ == '__main__':
    if config.spider.merge_only:
        merge_posts()
    else:
        asyncio.run(save_pages(config.spider.forum_name, config.spider.start_page, config.spider.end_page))

    # Close the dataset when the program exits.
    Dataset.get_instance().close_dataset()

