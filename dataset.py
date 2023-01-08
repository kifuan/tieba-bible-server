import sqlite3

from pathlib import Path
from typing import Iterable, Optional, Iterator


DATABASE_FILE = Path(__file__).parent / 'data' / 'db.sqlite'


class Dataset:
    """
    The dataset to record data from both spider and user.
    """

    _instance: Optional['Dataset'] = None

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._init_database()

    @classmethod
    def get_instance(cls) -> 'Dataset':
        """
        Gets dataset instance, which is singleton.
        :return: the instance.
        """

        if cls._instance is None:
            conn = sqlite3.connect(DATABASE_FILE)
            cls._instance = cls(conn)

        return cls._instance

    def _init_database(self):
        # Initialize the database if it needs to.
        with self._conn:
            cursor = self._conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS texts (
                `id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                `text` TEXT NOT NULL UNIQUE
            );
            ''')

    def close_dataset(self) -> None:
        """
        Closes the dataset.
        It should be called when the program should exit.
        """

        self._conn.close()

        # Clean the instance as well.
        self.__class__._instance = None

    def get_random_text(self, keyword: str) -> Optional[str]:
        """
        Gets a random text which contains the keyword.
        :param keyword: the keyword to filter.
        :return: the random text, it will be None if no text contains the keyword.
        """

        with self._conn:
            cursor = self._conn.cursor()
            cursor.execute('SELECT text FROM texts WHERE instr(text, ?) > 0 ORDER BY random() LIMIT 1', (keyword, ))
            if result := cursor.fetchone():
                return result[0]

        # There is no result in the database.
        return None

    def __iter__(self) -> Iterator[str]:
        """
        Generates all texts in the database.
        """

        with self._conn:
            cursor = self._conn.cursor()
            cursor.execute('SELECT text FROM texts')
            for row in cursor.fetchall():
                yield row[0]

    def add_texts(self, texts: Iterable[str]) -> None:
        """
        Adds multiple texts to the database.
        :param texts: texts to add.
        """

        with self._conn:
            cursor = self._conn.cursor()
            # The executemany needs a generator of tuples.
            cursor.executemany('INSERT OR IGNORE INTO texts (text) VALUES (?)', ((text, ) for text in texts))

    def count_keyword(self, keyword: str) -> int:
        """
        Counts for given keyword.
        :param keyword: the keyword to count.
        :return: the count of given keyword.
        """

        with self._conn:
            cursor = self._conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM texts WHERE instr(text, ?)', (keyword, ))
            return cursor.fetchone()[0]

    def __len__(self) -> int:
        """
        Gets the count of the database.
        :return: the count of the database.
        """

        # Count for an empty string to count all.
        return self.count_keyword('')
