from logging import getLogger
from typing import Any, Dict, List, Union
from database.database_service import DatabaseService

from typing import List, TypeVar, Type
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession as Session
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload

T = TypeVar("T")

logger = getLogger(__name__)


def add_session(func):
    @wraps(func)
    async def wrapped(self, *args, **kwargs):
        async with self.db_service.session() as session:
            async with session.begin():
                return await func(self, session, *args, **kwargs)

    return wrapped


def rearrange_items(
    og_items, shuffled_items, unique_key, og_is_value=False, keep_none=False
):
    if og_is_value:
        idx_dict = {item: idx for idx, item in enumerate(og_items)}
    else:
        idx_dict = {getattr(item, unique_key): idx for idx, item in enumerate(og_items)}

    new_list = [None for _ in enumerate(og_items)]

    for item in shuffled_items:
        new_list[idx_dict[getattr(item, unique_key)]] = item

    if not keep_none:
        new_list = [item for item in new_list if item is not None]

    return new_list


class CRUDService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service

    async def get_item_by_id(
        self,
        session: Session,
        orm_obj_type: Type[T],
        id: int,
        preload_child_name: str = None,
    ) -> T:
        """Get item by id, return None if not exists"""
        q = select(orm_obj_type).where(getattr(orm_obj_type, "id") == id)
        if preload_child_name:
            q = q.options(selectinload(getattr(orm_obj_type, preload_child_name)))
        try:
            result = (await session.execute(q)).one()
        except NoResultFound:
            return None
        return result[0]

    async def get_attr_of_item_by_id(
        self,
        session: Session,
        orm_obj_type: Type[T],
        id: int,
        attr_name: str,
        preload_child_name: str = None,
    ):
        db_item = await self.get_item_by_id(
            session, orm_obj_type, id, preload_child_name=preload_child_name
        )
        return getattr(db_item, attr_name)

    async def get_items_by_ids(
        self, session: Session, orm_obj_type: Type[T], ids: List[int], keep_none=False
    ) -> List[T]:
        """Get item by id, return empty list if not exists"""
        q = select(orm_obj_type).where(getattr(orm_obj_type, "id").in_(ids))
        result = await session.execute(q)
        result = [t[0] for t in result.all()]
        db_items = rearrange_items(ids, result, "id", True, keep_none=keep_none)
        return db_items

    async def get_item_by_attr(
        self, session: Session, orm_obj_type: Type[T], attr_name: str, attr_value: Any
    ) -> T:
        return await self.get_item_by_attrs(
            session, orm_obj_type, **{attr_name: attr_value}
        )

    async def get_item_by_attrs(
        self, session: Session, orm_obj_type: Type[T], **kwargs
    ) -> T:
        q = select(orm_obj_type)
        for attr_name, attr_value in kwargs.items():
            q = q.where(getattr(orm_obj_type, attr_name) == attr_value)
        result = await session.execute(q)
        try:
            (result,) = result.one()
        except NoResultFound:
            return None
        return result

    async def get_id_by_attr(
        self, session: Session, orm_obj_type: Type[T], attr_name: str, attr_value: Any
    ) -> int:
        return (
            await self.get_item_by_attr(session, orm_obj_type, attr_name, attr_value)
        ).id

    async def get_items_by_attr(
        self,
        session: Session,
        orm_obj_type: Type[T],
        attr_name: str,
        attr_values: List[Any],
    ) -> List[T]:
        q = select(orm_obj_type).where(
            getattr(orm_obj_type, attr_name).in_(attr_values)
        )
        result = await session.execute(q)
        result = [t[0] for t in result.all()]

        db_items = rearrange_items(attr_values, result, attr_name, True)
        return db_items

    async def get_items_by_same_attr(
        self,
        session: Session,
        orm_obj_type: Type[T],
        attr_name: str,
        attr_value: Any,
        sort_key: str = None,
    ) -> List[T]:
        q = select(orm_obj_type).where(getattr(orm_obj_type, attr_name) == attr_value)

        if sort_key is not None:
            q = q.order_by(getattr(orm_obj_type, sort_key))

        result = await session.execute(q)
        result = [t[0] for t in result.all()]

        return result

    async def get_items_of_obj(
        self, session: Session, orm_obj_type: Type[T], obj_id: int, attr_name: str
    ) -> List[T]:
        db_obj = await self.get_item_by_id(session, orm_obj_type, obj_id, attr_name)
        return getattr(db_obj, attr_name)

    async def item_obj_iteraction(
        self,
        session: Session,
        orm_obj_type: Type[T],
        orm_item_type: Type[T],
        obj_id: int,
        item_id: int,
        func,
        **kwargs,
    ):
        db_obj = await self.get_item_by_id(session, orm_obj_type, obj_id)
        db_item = await self.get_item_by_id(session, orm_item_type, item_id)

        if not db_obj or not db_item:
            return False

        return await func(session, db_obj, db_item, **kwargs)

    async def add_item_to_obj(
        self,
        session: Session,
        orm_obj_type: Type[T],
        orm_item_type: Type[T],
        obj_id: int,
        item_id: int,
        attr_name: str,
        auto_commit: bool = True,
    ) -> bool:
        async def append_item(session, db_obj, db_item):
            db_obj = await self.get_item_by_id(
                session, orm_obj_type, db_obj.id, attr_name
            )
            if not db_item in getattr(db_obj, attr_name):
                getattr(db_obj, attr_name).append(db_item)
                if auto_commit:
                    await session.commit()
                return db_obj
            return None

        return await self.item_obj_iteraction(
            session, orm_obj_type, orm_item_type, obj_id, item_id, append_item
        )

    async def remove_item_from_obj(
        self,
        session: Session,
        orm_obj_type: Type[T],
        orm_item_type: Type[T],
        obj_id: int,
        item_id: int,
        attr_name: str,
        auto_commit: bool = True,
    ) -> bool:
        async def remove_item(session, db_obj, db_item):
            db_obj = await self.get_item_by_id(
                session, orm_obj_type, db_obj.id, attr_name
            )
            if db_item in getattr(db_obj, attr_name):
                getattr(db_obj, attr_name).remove(db_item)
                if auto_commit:
                    await session.commit()
                return db_obj
            return None

        return await self.item_obj_iteraction(
            session, orm_obj_type, orm_item_type, obj_id, item_id, remove_item
        )

    async def create_obj(
        self,
        session: Session,
        orm_obj_type: Type[T],
        auto_commit: bool = True,
        **kwargs,
    ) -> T:
        db_item = orm_obj_type(**kwargs)
        session.add(db_item)
        if auto_commit:
            await session.commit()
        return db_item

    async def bulk_create_objs(
        self,
        session: Session,
        orm_obj_type: Type[T],
        items: List[Dict],
        auto_commit: bool = True,
    ) -> List[T]:
        logger.info(f"Going to bulk create {len(items)} items")
        result = [orm_obj_type(**item) for item in items]
        session.add_all(result)
        if auto_commit:
            await session.commit()
        return result

    async def bulk_create_objs_with_unique_key(
        self,
        session: Session,
        orm_obj_type: Type[T],
        items: List[Dict],
        unique_key: str,
        auto_commit: bool = True,
        update_attrs: List[str] = None,
    ) -> List[T]:
        """Bulk create jobs, but check if a value exsists for a unique key"""
        ordered_values = [item[unique_key] for item in items]
        db_items = await self.get_items_by_attr(
            session, orm_obj_type, unique_key, ordered_values
        )

        existing_unique_keys = set(getattr(db_item, unique_key) for db_item in db_items)

        if update_attrs:
            item_dict = {
                item[unique_key]: item
                for item in items
                if item[unique_key] in existing_unique_keys
            }
            db_item_dict = {
                getattr(db_item, unique_key): db_item for db_item in db_items
            }
            for key in db_item_dict:
                db_item = db_item_dict[key]
                item = item_dict[key]
                for attr_name in update_attrs:
                    setattr(db_item, attr_name, item[attr_name])

        # filter out items that already exist
        items = [item for item in items if not item[unique_key] in existing_unique_keys]
        new_db_items = await self.bulk_create_objs(
            session, orm_obj_type, items, auto_commit
        )
        result_db_items = db_items + new_db_items
        return rearrange_items(ordered_values, result_db_items, unique_key, True)

    async def _update_object(
        self,
        session: Session,
        orm_obj_type: Type[T],
        id: int,
        auto_commit: bool = True,
        **kwargs,
    ) -> Union[T, None]:
        q = select(orm_obj_type).where(getattr(orm_obj_type, "id") == id)
        db_item = (await session.execute(q)).one()[0]
        logger.info(db_item)
        if not db_item:
            return None
        for key, value in kwargs.items():
            if not hasattr(db_item, key):
                return None
            setattr(db_item, key, value)
        if auto_commit:
            await session.commit()
        return db_item

    async def update_object(
        self,
        session: Session,
        orm_obj_type: Type[T],
        id: int,
        auto_commit: bool = True,
        **kwargs,
    ) -> Union[T, None]:
        return await self._update_object(
            session, orm_obj_type, id, auto_commit=auto_commit, **kwargs
        )
