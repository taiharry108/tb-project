from dataclasses import dataclass, field
from dataclasses_json import DataClassJsonMixin
import uuid
from time import time
from typing import Any, Generic, Optional, TypeVar, Union, Type

MessageType = TypeVar('MessageType', bound='Message')


@dataclass
class Error:
    """
    Describes an error that occurred in a worker that was passed back up to the broker.
    Attributes:
        message  A message describing the error.
        retry    Whether or not the broker should retry sending this message back to the worker the error came from.
        surface  Whether or not the broker should surface the error message.
    """
    message: str
    retry: bool = False
    surface: bool = False
    exception_type: Union[Type[Exception], None] = None


@dataclass
class Message(Generic[MessageType], DataClassJsonMixin):
    """
    Attributes:
        start        A timestamp indicating when a worker started processing the message.
        stop         A timestamp indicating when a worker finished processing the message.
        error        An object describing an error that occurred in the worker.
        message_id   An id unique to every message.
        retry_count  The number of times the message has been retried by the same worker.
    """
    start: Optional[time] = None
    stop: Optional[time] = None
    # Union with Any until workers are on board with error format.
    error: Optional[Union[Error, Any]] = None
    message_id: uuid.UUID = field(default_factory=uuid.uuid4)
    retry_count: int = field(default=0)


@dataclass
class DefaultMessage(Message[MessageType]):
    """Default Message"""


@dataclass
class EncryptMessage(Message[MessageType]):
    filename: str = ""
    username: str = ""
    encryption_success: bool = False
