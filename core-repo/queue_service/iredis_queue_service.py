from typing import Protocol
from queue_service.messages import Message


class IRedisQueueService(Protocol):
    def add_message_to_queue(self, queue_name: str, message: Message) -> int:
        """Add a message to queue"""

    def get_message_from_queue(self, queue_name: str) -> Message:
        """Pop a message from queue"""

    def delete_message_from_queue(self, queue_name: str, message: Message) -> int:
        """Delete a message from queue"""
