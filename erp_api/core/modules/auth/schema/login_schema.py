# ============================================= Start Noted Schema ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. Schema respons login & me (untuk dokumentasi /docs)
# ============================================= END Noted Schema ===================================
from typing import Optional
from core.shared.base import ResponseBaseSchema
from core.modules.users.schema.users_schema import UsersDataSchema


class LoginResponseSchema(ResponseBaseSchema):
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    data: Optional[UsersDataSchema] = None


class MeResponseSchema(ResponseBaseSchema):
    data: Optional[UsersDataSchema] = None
