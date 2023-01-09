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
    Note that the json files are no longer used.
    The spider saves data into the database directly.
    This function is not deleted for compatibility, to check if specified thread is visited.
    :param tid: the thread id.
    :return: the json file path of given thread id.
    """

    return THREADS_DIR / f'{tid}.json'


async def get_thread_texts(client: aiotieba.Client, tid: int) -> AsyncIterator[str]:
    """
    Gets texts from given thread.
    :param client: the tieba client.
    :param tid: the thread id.
    :return: the iterator of texts from given thread.
    """

    database = Database.get_instance()

    if get_thread_json_file(tid).exists():
        aiotieba.LOG.warning(f'The thread file {tid}.json exists. Skipping.')
        return

    if database.check_if_visited_thread(tid):
        aiotieba.LOG.warning(f'The thread {tid} is visited. Skipping.')
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

    # Adds this thread into visited threads.
    database.add_visited_thread(tid)
    aiotieba.LOG.info(f'Saved thread {tid}.')


async def get_page_texts(client: aiotieba.Client, name: str, page_number: int) -> AsyncIterator[str]:
    """
    Gets texts from given page.
    :param client: the tieba client.
    :param name: the forum name.
    :param page_number: the page number.
    :return: texts to add.
    """

    aiotieba.LOG.debug(f'Saving page {page_number}.')
    threads = await client.get_threads(name, pn=page_number, sort=1)

    for thread in threads:
        async for text in get_thread_texts(client, thread.tid):
            yield text


async def save_pages(name: str, start_page: int, end_page: int) -> None:
    """
    Saves specified pages.
    :param name: the forum name.
    :param start_page: the start page number.
    :param end_page: the end page number.
    """

    async with aiotieba.Client('default') as client:
        added_texts = Database.get_instance().add_texts([
            text for page in range(start_page, end_page + 1)
            async for text in get_page_texts(client, name, page)
        ])

    aiotieba.LOG.info(f'Added {added_texts} texts.')


async def main():
    await save_pages(config.spider.forum_name, config.spider.start_page, config.spider.end_page)
    Database.get_instance().close_database()


if __name__ == '__main__':
    asyncio.run(main())

