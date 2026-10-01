# ============================================= Start Noted Token ===================================
# Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
# 1. Buat & verifikasi JWT. SECRET_KEY & masa berlaku dari core/.env (JANGAN ditulis di kode)
# 2. TokenData = identitas user yang sedang login, dipakai di router: identity: TokenData = Depends(get_current_user)
# ============================================= END Noted Token ===================================
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from pydantic import BaseModel

from core.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_DAYS

ALGORITHM = "HS256"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    sub: Optional[str] = None
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    grup: Optional[str] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def verify_token(token: str, credentials_exception) -> TokenData:
    try:
        payload = decode_token(token)
        sub: str = payload.get("sub")
        if sub is None:
            raise credentials_exception
        return TokenData(
            sub=sub,
            user_id=payload.get("user_id"),
            user_name=payload.get("user_name"),
            grup=payload.get("grup"),
        )
    except JWTError:
        raise credentials_exception
