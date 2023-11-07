import yaml

from kink import di
from async_service import AsyncService
from download_service import DownloadService

from services import DMHYScapingService, DelugeService
from store_service import FSStoreService


def _load_config_file() -> dict:
    with open("config.yml") as f:
        return yaml.safe_load(f)


def bootstrap_di() -> None:
    config_obj = _load_config_file()

    for key, value in config_obj.items():
        di[key] = value

    di["store_service"] = FSStoreService()

    di["max_connections"] = di["download_service"]["max_connections"]
    di["max_keepalive_connections"] = di["download_service"][
        "max_keepalive_connections"
    ]
    di["headers"] = di["download_service"]["headers"]

    di["num_workers"] = di["async_service"]["num_workers"]
    di["delay"] = di["async_service"]["delay"]

    di[AsyncService] = lambda di: AsyncService(di["num_workers"], di["delay"])

    di.factories[DownloadService] = lambda di: DownloadService(
        di["max_connections"],
        di["max_keepalive_connections"],
        di["headers"],
        di["store_service"],
    )

    di.factories[DMHYScapingService] = lambda di: DMHYScapingService(
        di[DownloadService]
    )

    di.factories[DelugeService] = lambda di: DelugeService(
        di["deluge_service"]["url"], di[DownloadService]
    )
