from concurrent.futures import ProcessPoolExecutor
from dotenv import dotenv_values
import sqlalchemy
from redis import Redis

from database_service import DatabaseService
from encrypt_service.fernet_encrypt_service import FernetEncryptService
from store_service.b2_store_service import B2StoreService
from store_service.fs_store_service import FSStoreService

from in_queue_listener import InQueueListener
from out_queue_listener import OutQueueListener
from queue_service.messages import EncryptMessage
from queue_service.redis_queue_service import RedisQueueService


IN_QUEUE_NAME = "in_queue_name"
OUT_QUEUE_NAME = "out_queue_name"
REDIS_URL = "redis_url"
DB_CONN_STR = "db_conn_str"


def in_queue_listen(config: dict, in_queue_name: str, out_queue_name: str):
    redis_instance = Redis(config[REDIS_URL])
    engine = sqlalchemy.create_engine(config[DB_CONN_STR])
    database_service = DatabaseService(engine)
    fs_store_service = FSStoreService()
    fes = FernetEncryptService(fs_store_service)
    queue_service = RedisQueueService[EncryptMessage](
        redis=redis_instance, message_cls=EncryptMessage, timeout=0
    )

    queue_listener = InQueueListener(
        database_service=database_service,
        encrypt_service=fes,
        config=config,
        queue_service=queue_service,
        queue_name=in_queue_name,
        out_queue_name=out_queue_name,
    )
    queue_listener.listen()


def out_queue_listen(config: dict, in_queue_name: str):
    redis_instance = Redis(config[REDIS_URL])
    fs_store_service = B2StoreService(
        "tb-project-app", config["application_key_id"], config["application_key"]
    )
    queue_service = RedisQueueService[EncryptMessage](
        redis=redis_instance, message_cls=EncryptMessage, timeout=0
    )

    queue_listener = OutQueueListener(
        store_service=fs_store_service,
        config=config,
        queue_service=queue_service,
        queue_name=in_queue_name,
    )
    queue_listener.listen()


def main():
    print("staring app")
    config = dotenv_values(".env")
    in_queue_name = config[IN_QUEUE_NAME]
    out_queue_name = config[OUT_QUEUE_NAME]

    with ProcessPoolExecutor(2) as executor:
        in_future = executor.submit(
            in_queue_listen, config, in_queue_name, out_queue_name
        )
        out_future = executor.submit(out_queue_listen, config, out_queue_name)

        out_future.result()


if __name__ == "__main__":
    main()
