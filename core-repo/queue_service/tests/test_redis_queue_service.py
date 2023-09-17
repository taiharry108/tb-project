import pytest
from redis import Redis

from queue_service.redis_queue_service import RedisQueueService
from queue_service.messages import Message, DefaultMessage


@pytest.fixture(scope="module")
def timeout() -> int:
    return 1


@pytest.fixture(scope="module")
def queue_name() -> str:
    return "test_queue"


@pytest.fixture(scope="module")
def message() -> Message:
    return DefaultMessage()


@pytest.fixture(scope="module")
def redis_instance() -> Redis:
    return Redis("default-redis")


@pytest.fixture(autouse=True, scope="module")
def run_before_and_after_tests(redis_instance: Redis, queue_name: str):
    yield
    redis_instance.delete(queue_name)


@pytest.fixture
def redis_queue_service(redis_instance: Redis, timeout: int) -> RedisQueueService:
    return RedisQueueService(redis_instance, timeout)


def test_add_message_to_queue(queue_name: str, message: Message, redis_queue_service: RedisQueueService, redis_instance: Redis):
    queue_length = redis_instance.llen(queue_name)
    new_queue_length = redis_queue_service.add_message_to_queue(
        queue_name, message)
    assert new_queue_length - queue_length == 1


def test_get_message_from_queue(queue_name: str, redis_queue_service: RedisQueueService, redis_instance: Redis):
    assert redis_instance.llen(queue_name)
    message = redis_queue_service.get_message_from_queue(queue_name)
    assert message
    assert isinstance(message, Message)


def test_get_message_from_queue_when_no_message(queue_name: str, redis_queue_service: RedisQueueService, redis_instance: Redis):
    assert redis_instance.llen(queue_name) == 0
    message = redis_queue_service.get_message_from_queue(queue_name)
    assert message is None


def test_delete_message_from_queue(queue_name: str, redis_queue_service: RedisQueueService, redis_instance: Redis):
    # generate messages
    messages = [DefaultMessage() for _ in range(10)]
    [redis_instance.rpush(queue_name, message.to_json())
     for message in messages]

    assert redis_instance.llen(queue_name) == 10

    no_of_ele_removed = redis_queue_service.delete_message_from_queue(
        queue_name, messages[5])
    assert no_of_ele_removed == 1


def test_delete_non_existent_message_from_queue(queue_name: str, redis_queue_service: RedisQueueService):
    no_of_ele_removed = redis_queue_service.delete_message_from_queue(
        queue_name, DefaultMessage())
    assert no_of_ele_removed == 0
