import sqlite3

from pathlib import Path
from typing import Iterable, Optional, Generator


class Database:
    """
    The database to record data from both the spider and the user.
    """

    _instance: Optional['Database'] = None

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._init_database()

    @classmethod
    def get_instance(cls) -> 'Database':
        """
        Gets database instance, which is singleton.
        :return: the instance.
        """

        if cls._instance is None:
            conn = sqlite3.connect(Path(__file__).parent / 'data' / 'db.sqlite')
            cls._instance = cls(conn)

        return cls._instance

    def _init_database(self) -> None:
        # Initialize the database if it needs to.
        with self._conn:
            self._conn.executescript('''
            CREATE TABLE IF NOT EXISTS texts (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                `text` TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS visited_threads (
                `tid` INTEGER PRIMARY KEY NOT NULL
            );
            ''')

    def close_database(self) -> None:
        """
        Closes the database.
        It should be called when exiting.
        """

        self._conn.close()

        # Clean the instance as well.
        self.__class__._instance = None

    def get_random_text(self, keyword: str) -> Optional[str]:
        """
        Gets a random text which contains the keyword.
        :param keyword: the keyword to filter.
        :return: the random text, which will be None if no text contains the keyword.
        """

        with self._conn:
            if result := self._conn.execute(
                'SELECT text FROM texts WHERE INSTR(text, ?) > 0 ORDER BY RANDOM() LIMIT 1',
                (keyword, ),
            ).fetchone():
                return result[0]

        # There is no result in the database.
        return None

    def __iter__(self) -> Generator[str, None, None]:
        """
        Generates all texts in the database.
        """

        with self._conn:
            for row in self._conn.execute('SELECT text FROM texts'):
                yield row[0]

    def add_visited_threads(self, tid: Iterable[int]) -> int:
        """
        Adds multiple visited thread ids.
        :param tid: multiple thread ids.
        :return: the count of added threads.
        """

        with self._conn:
            return self._conn.executemany(
                'INSERT OR IGNORE INTO visited_threads (tid) VALUES (?)',
                ((t, ) for t in tid)
            ).rowcount

    def check_if_visited_thread(self, tid: int) -> bool:
        """
        Checks if the given thread is visited.
        :param tid: the thread id.
        :return: whether it is visited.
        """

        with self._conn:
            return self._conn.execute(
                'SELECT * FROM visited_threads WHERE tid=?', (tid, )
            ).fetchone() is not None

    def add_texts(self, texts: Iterable[str]) -> int:
        """
        Adds multiple texts to the database.
        :param texts: texts to add.
        :return: the count of affected lines.
        """

        with self._conn:
            return self._conn.executemany(
                'INSERT OR IGNORE INTO texts (text) VALUES (?)',
                ((text, ) for text in texts)
            ).rowcount

    def count(self, keyword: str) -> int:
        """
        Counts for given keyword.
        :param keyword: the keyword to count.
        :return: the count of given keyword.
        """

        with self._conn:
            return self._conn.execute(
                'SELECT COUNT(*) FROM texts WHERE INSTR(text, ?)', (keyword, )
            ).fetchone()[0]
