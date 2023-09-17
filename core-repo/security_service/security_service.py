from jose import jwt


from logging import getLogger


logger = getLogger(__name__)


class SecurityService:
    def __init__(self,
                 public_key: str,
                 algorithm: str):                
        self.public_key = public_key
        self.algorithm = algorithm

    def decode_access_token(self, token: str):
        return jwt.decode(token, self.public_key, algorithms=[self.algorithm])
