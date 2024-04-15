# Create a pydantic class called TeslaAccessTokenRequest
# Fields:
#    - grant_type: str
#    - client_id: str
#    - client_secret: str
#    - code: str
#    - redirect_uri: str
#    - audience: str
#

from pydantic import BaseModel

class TeslaAccessTokenRequest(BaseModel):
    grant_type: str
    client_id: str
    client_secret: str
    code: str
    redirect_uri: str
    audience: str

class TeslaRefreshTokenRequest(BaseModel):
    grant_type: str
    client_id: str
    refresh_token: str

class TeslaAccessTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
