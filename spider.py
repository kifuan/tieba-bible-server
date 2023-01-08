import re
import ujson
import asyncio
import aiotieba

from typing import AsyncIterator
from pathlib import Path

from config import config
from database import Database


ROOT_DIR = Path(__file__).parent

DATA_DIR = ROOT_DIR / 'data'

THREADS_DIR = DATA_DIR / 'threads'

REPLY_PREFIX_REGEX = re.compile(r'回复.+[:：]\s*')


def process_text(text: str) -> str:
    """
    Processes the text, removing reply prefix.
    :param text: the text to process.
    :return: the processed text.
    """

    return REPLY_PREFIX_REGEX.sub('', text.strip())


def get_thread_json_file(tid: int) -> Path:
    """
    Gets json file path of given thread id.
    :param tid: the thread id.
    :return: the json file path of given thread id.
    """

    return THREADS_DIR / f'{tid}.json'


async def get_and_save_thread(tid: int, texts: AsyncIterator[str]) -> list[str]:
    """
    Saves thread in tid.json and returns the list of texts.
    :param tid: the thread id.
    :param texts: the async generator of texts.
    :return: the list of texts.
    """

    list_texts = [text async for text in texts]
    with open(get_thread_json_file(tid), 'w', encoding='utf8') as f:
        ujson.dump(list_texts, f, ensure_ascii=False)
    return list_texts


async def get_threads(client: aiotieba.Client, tid: int) -> AsyncIterator[str]:
    """
    Gets threads.
    :param client: the tieba client.
    :param tid: the thread id.
    :return: the iterator of texts from given thread.
    """

    if get_thread_json_file(tid).exists():
        aiotieba.LOG.warning(f'The thread file {tid}.json exists. Skipping.')
        return

    page_number = 1
    while page_number <= config.spider.max_post_pages:
        await asyncio.sleep(1)
        posts = await client.get_posts(tid, pn=page_number)
        for post in posts:
            yield process_text(post.contents.text)

        if not posts.has_more:
            break

        page_number += 1

    aiotieba.LOG.debug(f'Saved thread contents to {tid}.json.')


async def save_page(client: aiotieba.Client, name: str, page_number: int) -> None:
    """
    Saves given page.
    :param client: the tieba client.
    :param name: the forum name.
    :param page_number: the page number.
    """

    database = Database.get_instance()
    aiotieba.LOG.debug(f'Saving page {page_number}.')
    threads = await client.get_threads(name, pn=page_number, sort=1)
    for thread in threads:
        texts = await get_and_save_thread(thread.tid, get_threads(client, thread.tid))
        database.add_texts(texts)


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


def merge_threads() -> None:
    """
    Merge all threads the spider fetched in JSON files.
    """

    database = Database.get_instance()
    aiotieba.LOG.info('Reading files.')
    # Remove empty texts by the simple condition.
    len1 = database.count_keyword()
    database.add_texts({
        process_text(text)
        for file in THREADS_DIR.iterdir() if file.suffix == '.json'
        for text in ujson.loads(file.read_text('utf8'))
    })
    len2 = database.count_keyword()
    aiotieba.LOG.info(f'Added {len2 - len1} texts.')


async def main():
    if config.spider.merge_only:
        merge_threads()
    else:
        await save_pages(config.spider.forum_name, config.spider.start_page, config.spider.end_page)

    Database.get_instance().close_database()


if __name__ == '__main__':
    asyncio.run(main())

