from pydantic import BaseModel


class File(BaseModel):
    filename: str
    id: int

    class Config:
        orm_mode = True
