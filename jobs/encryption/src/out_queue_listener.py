from encrypt_message import EncryptMessage

from store_service.store_service import StoreService
from queue_service.queue_listener import QueueListener


class OutQueueListener(QueueListener):
    def __init__(self, store_service: StoreService, config: dict, **kwargs):
        self.upload_path = config['upload_path']
        self.store_service = store_service
        super().__init__(**kwargs)

    def _process_message(self, message: EncryptMessage) -> EncryptMessage:
        encryption_success = message.encryption_success
        if encryption_success:
            # Remove file if successful
            self.store_service.remove_file(
                f"{self.upload_path}/{message.filename}")
