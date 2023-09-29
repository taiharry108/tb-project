from dependency_injector.wiring import Provide, inject
from container import Container
from core.some_service import SomeService


@inject
async def test_some_service(
    some_service: SomeService = Provide[Container.some_service],
):
    assert some_service
