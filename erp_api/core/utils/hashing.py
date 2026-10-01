# ============================================= Start Noted Hashing ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. Hash password dengan pbkdf2_sha256 (disimpan di kolom users.user_passwd_sha)
# ============================================= END Noted Hashing ===================================
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class Hash:
    @staticmethod
    def pbkdf2_sha256(password: str) -> str:
        return pwd_context.hash(secret=password)

    @staticmethod
    def verify(hashed_password: str, plain_password: str) -> bool:
        if not hashed_password:
            return False
        try:
            return pwd_context.verify(secret=plain_password, hash=hashed_password)
        except (ValueError, TypeError):
            return False
