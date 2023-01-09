import ujson
import shutil

from pathlib import Path

from spider import process_text
from database import Database


THREADS_DIR = Path(__file__).parent / 'data' / 'threads'


def migrate() -> None:
    """
    Merge all threads the spider fetched in JSON files.
    """

    database = Database.get_instance()

    if not THREADS_DIR.exists():
        print('You has already migrated.')
        return

    files = [
        file for file in THREADS_DIR.iterdir() if file.suffix == '.json'
    ]

    if not files:
        shutil.rmtree(THREADS_DIR)
        print('No thread file in directory threads. Removed directory directly.')
        return

    migrated_texts = database.add_texts(
        process_text(text)
        for file in files
        for text in ujson.loads(file.read_text('utf8'))
    )

    migrated_threads = database.add_visited_threads(int(file.stem) for file in files)

    print(f'Migrated {migrated_texts} texts, {migrated_threads} threads.')

    shutil.rmtree(THREADS_DIR)
    print('Removed threads directory.')


if __name__ == '__main__':
    migrate()
