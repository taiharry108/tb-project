from abc import abstractmethod, ABCMeta
import time
from typing import Union

from queue_service.iredis_queue_service import IRedisQueueService
from queue_service.messages import Message


class QueueListener(metaclass=ABCMeta):
    def __init__(
        self,
        queue_service: IRedisQueueService,
        queue_name: str,
        out_queue_name: Union[str, None] = None,
        sleep_time: int = 1,
    ):
        self.queue_name = queue_name
        self.queue_service = queue_service
        self.out_queue_name = out_queue_name
        self._sleep_time = sleep_time

    def listen(self):
        while True:
            message = self.queue_service.get_message_from_queue(self.queue_name)
            if message:
                message = self._process_message(message)
            if self.out_queue_name and message:
                self.queue_service.add_message_to_queue(self.out_queue_name, message)
            time.sleep(self._sleep_time)

    @abstractmethod
    def _process_message(self, message: Message):
        """Main function to process message"""
