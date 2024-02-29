import asyncio

from itertools import islice
from logging import getLogger
from typing import Iterable, Coroutine, AsyncGenerator, TypeVar, Callable, Awaitable

logger = getLogger(__name__)

T = TypeVar("T")


def partition(lst, size):
    for i in range(0, len(lst), size):
        yield list(islice(lst, i, i + size))


def partition(lst, size):
    for i in range(0, len(lst), size):
        yield list(islice(lst, i, i + size))


class AsyncService:
    def __init__(self, num_workers: int, delay: float):
        self.num_workers = num_workers
        self.delay = delay

    async def work(
        self, items: Iterable, async_func: Callable[..., Awaitable[T]], **kwargs
    ) -> AsyncGenerator[T, None]:
        semaphore = asyncio.Semaphore(self.num_workers)

        async def sem_coro(coro: Coroutine):
            async with semaphore:
                result = await coro
                return result

        for part in partition(items, 10):
            tasks = [async_func(**item, **kwargs) for item in part]
            for item in asyncio.as_completed([sem_coro(c) for c in tasks]):
                to_return = await item
                yield to_return
