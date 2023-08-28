import os

from store_service.store_service import StoreService
from queue_service.queue_listener import QueueListener
from queue_service.messages import EncryptMessage


class OutQueueListener(QueueListener):
    def __init__(self, store_service: StoreService, config: dict, **kwargs):
        self.upload_path = config['upload_path']
        self.store_service = store_service
        self.encrypted_path = config['encrypted_path']
        super().__init__(**kwargs)

    def _process_message(self, message: EncryptMessage) -> EncryptMessage:
        encryption_success = message.encryption_success
        if encryption_success:
            # Remove file if successful
            os.remove(f"{self.upload_path}/{message.filename}")
            encrypt_file = f"{self.encrypted_path}/{message.filename}"
            with open(encrypt_file, 'rb') as f:
                result = self.store_service.persist_file_sync(encrypt_file, f.read())
                print(result)
