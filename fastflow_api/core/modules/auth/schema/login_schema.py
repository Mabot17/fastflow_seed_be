# ============================================= Start Noted Schema ===================================
# Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
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
