from pydantic import BaseModel, HttpUrl

class Site(BaseModel):
    id: int
    name: str
    url: HttpUrl

    class Config:
        orm_mode = True
