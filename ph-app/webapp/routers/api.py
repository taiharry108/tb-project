from dependency_injector.wiring import inject, providers
from fastapi import APIRouter
from fastapi_cache.decorator import cache
from logging import getLogger
from typing import List

from models.search_result import SearchResult
from services.ph_service import search_ph, get_vid_result

router = APIRouter()

logger = getLogger(__name__)

FactoryAggregate = providers.FactoryAggregate


@router.get("/search")
@inject
@cache(expire=3600)
async def search(
        keyword: str,
        page: int = 1,
) -> SearchResult:
    search_result = await search_ph(keyword.lower(), page)
    return search_result


@router.get("/vid")
@inject
async def get_vid(vid_id: str):    
    return await get_vid_result(vid_id)
