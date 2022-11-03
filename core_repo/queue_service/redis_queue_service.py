import json
from redis import Redis

from queue_service.iredis_queue_service import IRedisQueueService
from queue_service.messages import Message

class RedisQueueService(IRedisQueueService):
    def __init__(self, redis: Redis, timeout: int):
        self.redis = redis
        self.timeout = timeout
    
    def add_message_to_queue(self, queue_name: str, message: Message) -> int:
        """Add a message to queue"""
        return self.redis.rpush(queue_name, message.to_json())
    
    def get_message_from_queue(self, queue_name: str) -> Message:
        """Pop a message from queue"""
        resp = self.redis.blpop(queue_name, timeout=self.timeout)

        if resp:
            message = resp[1]            
            return Message.from_json(message)
        return None
    
    def delete_message_from_queue(self, queue_name: str, message: Message) -> int:
        """Delete a message from queue"""
        no_of_ele_removed = self.redis.lrem(
            queue_name, count=1, value=message.to_json())
        return no_of_ele_removed
