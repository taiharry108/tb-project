from dataclasses import dataclass
from queue_service.messages import Message, MessageType


@dataclass
class EncryptMessage(Message[MessageType]):
    filename: str = ""
    username: str = ""
    encryption_success: bool = False
