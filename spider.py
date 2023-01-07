import re
import ujson
import asyncio
import aiotieba

from pathlib import Path


ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / 'data'
POSTS_DIR = DATA_DIR / 'posts'
DATASET_FILE = DATA_DIR / 'dataset.json'

# Configurations.
CONFIG = ujson.loads((ROOT_DIR / 'config.json').read_text('utf8'))['spider']

# Max post pages it will get.
MAX_POST_PAGES = CONFIG['max_post_pages']

# The start page to fetch.
START_PAGE = CONFIG['start_page']

# The end page to fetch. It can be -1 to get single start page.
END_PAGE = CONFIG['end_page']

# The forum name to fetch.
FORUM_NAME = CONFIG['forum_name']

# The regex to remove prefix to reply.
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
    while page_number <= MAX_POST_PAGES:
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
    It will only save `page_start` if `page_end` is set to -1.
    :param name: the forum name.
    :param start_page: the start page number.
    :param end_page: the end page number.
    """

    if end_page == -1:
        end_page = start_page

    async with aiotieba.Client('default') as client:
        for page in range(start_page, end_page + 1):
            aiotieba.LOG.debug(f'saving page {page}.')
            await save_page(client, name, page)


def merge_posts() -> None:
    """
    Merge all posts the spider fetched in JSON files.
    """

    with DATASET_FILE.open('w', encoding='utf8') as f:
        processed_dataset = {
            REPLY_PREFIX_REGEX.sub('', item.strip())
            for file in POSTS_DIR.iterdir() if file.suffix == '.json'
            for item in ujson.loads(file.read_text('utf8'))
        }
        # Remove empty texts by the simple condition.
        dataset = [text for text in processed_dataset if text]
        ujson.dump(dataset, f, ensure_ascii=False)
    aiotieba.LOG.info('merged all posts.')


if __name__ == '__main__':
    try:
        asyncio.run(save_pages(FORUM_NAME, START_PAGE, END_PAGE))
    finally:
        merge_posts()
