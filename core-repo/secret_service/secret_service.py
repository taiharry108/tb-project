import os

class SecretService:
    def get_secret(self, secret_name: str) -> str:
        # check if secret_name is under /etc/secrets/{secret_name}
        if os.path.exists(f"/etc/secrets/{secret_name}"):
            with open(f"/etc/secrets/{secret_name}") as f:
                return f.read()
        return os.environ[secret_name]
