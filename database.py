import databases

from typing import Iterable, Optional, AsyncGenerator, Union
from config import config


class Database:
    """
    The database to record data from both the spider and the user.
    """

    _instance: Optional['Database'] = None

    def __init__(self, db: databases.Database) -> None:
        self._db = db

    @classmethod
    async def get_instance(cls) -> 'Database':
        """
        Gets database instance, which is singleton.
        :return: the instance.
        """

        if cls._instance is not None:
            return cls._instance

        db = databases.Database('sqlite+aiosqlite:///./data/db.sqlite')

        async with db:
            # Initialize tables.
            await db.execute('''
            CREATE TABLE IF NOT EXISTS texts (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                `text` TEXT NOT NULL UNIQUE
            );
            ''')
            await db.execute('''
            CREATE TABLE IF NOT EXISTS visited_threads (
                `tid` INTEGER PRIMARY KEY NOT NULL
            );
            ''')

        cls._instance = cls(db)
        return cls._instance

    async def __aiter__(self) -> AsyncGenerator[str, None]:
        """
        Generates all texts in the database.
        """

        async with self._db as db:
            async for row in db.iterate('SELECT text FROM texts'):
                yield row[0]

    async def add_visited_threads(self, tid: Iterable[int]) -> None:
        """
        Adds multiple visited thread ids.
        :param tid: multiple thread ids.
        """

        async with self._db as db:
            query = 'INSERT OR IGNORE INTO visited_threads (tid) VALUES (:tid)'
            values = [{'tid': t} for t in tid]
            await db.execute_many(query, values)

    async def check_if_visited_thread(self, tid: int) -> bool:
        """
        Checks if the given thread is visited.
        :param tid: the thread id.
        :return: whether it is visited.
        """

        async with self._db as db:
            query = 'SELECT * FROM visited_threads WHERE tid=:tid'
            values = {'tid': tid}
            return await db.fetch_one(query, values) is not None

    async def add_texts(self, texts: Iterable[str]) -> None:
        """
        Adds multiple texts to the database.
        :param texts: texts to add.
        """

        async with self._db as db:
            query = 'INSERT OR IGNORE INTO texts (text) VALUES (:text)'
            values = [{'text': text} for text in texts]
            await db.execute_many(query, values)

    async def get_random_text(self, keyword: str, short: bool) -> Optional[str]:
        """
        Gets a random text by given keyword.
        :param keyword: the keyword.
        :param short: whether to get a short text.
        :return: the random text, which will be None if no text contains the keyword.
        """

        async with self._db as db:
            # The length is read from server configurations, which won't cause SQL injection.
            query = (
                f'SELECT text FROM texts WHERE LENGTH(text) < {config.server.short_length} '
                'AND INSTR (text, :keyword) > 0 ORDER BY RANDOM() LIMIT 1'
                if short else
                'SELECT text FROM texts WHERE INSTR(text, :keyword) > 0 '
                'ORDER BY RANDOM() LIMIT 1'
            )
            values = {'keyword': keyword}
            if result := await db.fetch_one(query, values):
                return result[0]

        return None

    async def count(self, keyword: str, short: bool) -> int:
        """
        Counts for given keyword.
        :param keyword: the keyword to count.
        :param short: whether to count short texts.
        :return: the count of given keyword.
        """

        async with self._db as db:
            # The length is read from server configurations, which won't cause SQL injection.
            query = (
                f'SELECT COUNT(*) FROM texts WHERE LENGTH(text) < {config.server.short_length} '
                'AND INSTR(text, :keyword) > 0'
                if short else
                'SELECT COUNT(*) FROM texts WHERE INSTR(text, :keyword) > 0'
            )
            values = {'keyword': keyword}
            count = await db.fetch_one(query, values)
            return count[0]
