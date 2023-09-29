from database_service import DatabaseService

from pathlib import Path
from encrypt_service.encrypt_service import EncryptService
from queue_service.messages import Error, EncryptMessage
from queue_service.queue_listener import QueueListener


class InQueueListener(QueueListener):
    def __init__(
        self,
        database_service: DatabaseService,
        encrypt_service: EncryptService,
        config: dict,
        **kwargs,
    ):
        self.database_service = database_service
        self.encrypt_service = encrypt_service
        self.upload_path = config["upload_path"]
        self.encrypted_path = config["encrypted_path"]
        super().__init__(**kwargs)

    def _process_message(self, message: EncryptMessage) -> EncryptMessage:
        username = message.username
        filename = message.filename
        key = self.database_service.get_private_key_from_username(username)

        try:
            if message.is_encrypt:
                func = self.encrypt_service.encrypt_file_sync
            else:
                func = self.encrypt_service.decrypt_file_sync

            success = func(
                key=key.encode("utf-8"),
                src_file=Path(f"{self.upload_path}/{filename}"),
                dest_file=Path(f"{self.encrypted_path}/{filename}"),
            )
            message.encryption_success = success
        except Exception as ex:
            error = Error(message=str(ex), exception_type=type(ex))
            message.error = error
        return message
