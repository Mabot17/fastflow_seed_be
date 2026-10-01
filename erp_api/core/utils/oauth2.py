# ============================================= Start Noted OAuth2 ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. get_current_user -> dependency wajib token di setiap endpoint yang butuh login
#    identity: TokenData = Depends(get_current_user)
# ============================================= END Noted OAuth2 ===================================
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from core.utils.response_handle import show_unauthorized
from core.utils.token import TokenData, verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=show_unauthorized(),
        headers={"WWW-Authenticate": "Bearer"},
    )
    return verify_token(token, credentials_exception)
