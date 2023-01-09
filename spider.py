import re
import asyncio
import aiotieba

from typing import AsyncGenerator
from pathlib import Path

from config import config
from database import Database


DATA_DIR = Path(__file__).parent / 'data'

REPLY_PREFIX_REGEX = re.compile(r'回复.+[:：]\s*')


def process_text(text: str) -> str:
    """
    Processes the text, removing reply prefix.
    :param text: the text to process.
    :return: the processed text.
    """

    return REPLY_PREFIX_REGEX.sub('', text.strip())


async def get_thread_texts(client: aiotieba.Client, tid: int) -> AsyncGenerator[str, None]:
    """
    Gets texts from given thread.
    :param client: the tieba client.
    :param tid: the thread id.
    :return: the texts of given thread.
    """

    if Database.get_instance().check_if_visited_thread(tid):
        aiotieba.LOG.warning(f'The thread {tid} is visited. Skipping.')
        return

    aiotieba.LOG.info(f'Getting thread {tid}.')

    page_number = 1
    while page_number <= config.spider.max_post_pages:
        await asyncio.sleep(1)
        posts = await client.get_posts(tid, pn=page_number)
        for post in posts:
            yield process_text(post.contents.text)

        if not posts.has_more:
            return

        page_number += 1


async def save_page(client: aiotieba.Client, name: str, pn: int) -> None:
    """
    Gets texts from given page.
    :param client: the tieba client.
    :param name: the forum name.
    :param pn: the page number.
    """

    aiotieba.LOG.info(f'Getting page {pn}.')
    database = Database.get_instance()
    threads = await client.get_threads(name, pn=pn, sort=1)
    added_texts = 0

    for thread in threads:
        added_texts += database.add_texts([
            text async for text in get_thread_texts(client, thread.tid)
        ])

    added_threads = database.add_visited_threads(thread.tid for thread in threads)
    aiotieba.LOG.info(f'Added {added_threads} threads containing {added_texts} texts from page {pn}.')


async def save_pages(name: str, start_page: int, end_page: int) -> None:
    """
    Saves specified pages.
    :param name: the forum name.
    :param start_page: the start page number.
    :param end_page: the end page number.
    """

    async with aiotieba.Client('default') as client:
        for page_number in range(start_page, end_page + 1):
            await save_page(client, name, page_number)


if __name__ == '__main__':
    asyncio.run(save_pages(
        config.spider.forum_name,
        config.spider.start_page,
        config.spider.end_page,
    ))

    # Close the database when exiting.
    Database.get_instance().close_database()
