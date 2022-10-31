from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import sys
import time
from logging import config, getLogger
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from cryptography.fernet import Fernet

from core.key_management_service import KeyManagementService

config.fileConfig("logging.conf")

logger = getLogger(__name__)
CHUNK_SIZE = 1024 * 4


def encrypt_file(key: str, src_path: Path, desk_path: Path):
    logger.info(f"going to encrypt file from {src_path} to {desk_path}")
    fernet = Fernet(key)

    with open(desk_path, 'wb') as out_f:
        with open(src_path, 'rb') as in_f:
            while True:
                data = in_f.read(CHUNK_SIZE)
                if not data:
                    break
                out_f.write(fernet.encrypt(data))


class FileCreatedEventHandler(FileSystemEventHandler):
    def __init__(self, process_pool: ProcessPoolExecutor,
                 key_management_service: KeyManagementService):
        super().__init__()
        self.process_pool = process_pool
        self.key_management_service = key_management_service

    def on_created(self, event: FileSystemEvent):
        super().on_created(event)
        if not event.is_directory:
            src_path = Path(event.src_path)
            logger.info(f"Files detected: {src_path=}")
            username = src_path.parent.name            
            dest_path = src_path.parent.parent.parent/"encrypted"/username/src_path.name
            dest_path.parent.mkdir(exist_ok=True, parents=True)
            key = self.key_management_service.get_key(username)
            logger.info(f"Key: {key=}")

            self.process_pool.submit(encrypt_file, key, src_path, dest_path)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    process_pool = ProcessPoolExecutor(2)
    event_handler = FileCreatedEventHandler(process_pool, KeyManagementService("http://localhost:60801/admin/key"))
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
