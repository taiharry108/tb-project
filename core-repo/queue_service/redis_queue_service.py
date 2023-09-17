from redis import Redis
from typing import Generic, Type
from queue_service.iredis_queue_service import IRedisQueueService
from queue_service.messages import MessageType


class RedisQueueService(IRedisQueueService, Generic[MessageType]):
    def __init__(self, redis: Redis, message_cls: Type[MessageType], timeout: int = 10):
        self.redis = redis
        self.timeout = timeout
        self.message_cls = message_cls

    def add_message_to_queue(self, queue_name: str, message: MessageType) -> int:
        """Add a message to queue"""
        return self.redis.rpush(queue_name, message.to_json())

    def get_message_from_queue(self, queue_name: str) -> MessageType:
        """Pop a message from queue"""
        resp = self.redis.blpop(queue_name, timeout=self.timeout)

        if resp:
            message = resp[1]
            return self.message_cls.from_json(message)
        return None

    def delete_message_from_queue(self, queue_name: str, message: MessageType) -> int:
        """Delete a message from queue"""
        no_of_ele_removed = self.redis.lrem(
            queue_name, count=1, value=message.to_json())
        return no_of_ele_removed
