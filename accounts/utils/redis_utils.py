import redis
from django.conf import settings

class VerificationEmail:
    PREFIX = 'email_verify'
    TTL = 60

    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_CONFIG['HOST'],
            port=settings.REDIS_CONFIG['PORT'],
            db=settings.REDIS_CONFIG['DB'],
            decode_responses=True
        )

    def _code_key(self, email:str) -> str:
        return f'{self.PREFIX}:code:{email}'

    def set_code(self, email: str, code: str) -> str:
        if self.client.exists(self._code_key(email)):
            return "Code already sent"
        
        self.client.setex(self._code_key(email), self.TTL, code)

        return "OK"

    def get_code(self, email: str) -> str:
        if self.client.exists(self._code_key(email)):
            return self.client.get(self._code_key(email))
        
        return None

    def compare_code(self, email: str, code: str) -> bool:
        stored_code = self.get_code(email)

        print(stored_code)
        print(code)

        if stored_code:
            if stored_code == code:
                return True
            
        return False
