from pydantic import BaseModel, HttpUrl, ConfigDict


class Site(BaseModel):
    id: int
    name: str
    url: HttpUrl
    model_config = ConfigDict(from_attributes=True)
