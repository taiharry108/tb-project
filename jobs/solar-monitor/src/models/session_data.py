from datetime import datetime

from pydantic import BaseModel

class SessionData(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: float

    # create a property to check if the session is expired
    # a session is expired if expires_at is larger than datetime.timestamp()
    @property
    def is_expired(self):
        return self.expires_at < datetime.now().timestamp()
