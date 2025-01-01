from datetime import datetime
from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import Optional

from core.dmhy_team_enum import DMHYTeamEnum


class DMHYSearchResult(BaseModel):
    id: Optional[int] = None
    url: str
    post_datetime: datetime
    team: DMHYTeamEnum | None
    name: str
    model_config = ConfigDict(from_attributes=True)
