# ============================================= Start Noted API Router ===================================
# Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
# 1. Satu-satunya tempat semua router didaftarkan ke FastAPI (lihat router_readme.md)
# 2. Router modul di-import dari core/router/modules_registry/<modul>_routers.py
# 3. Modul baru didaftarkan otomatis oleh `fastflow module new` / `fastflow module register`
# ============================================= END Noted API Router ===================================
from fastapi import APIRouter, Depends, Request

from core.router import api_docs
from core.router.api_middleware import MaintenanceException

from core.router.modules_registry.auth_routers import (
    login_router,
)

from core.router.modules_registry.users_routers import (
    users_router,
)


def maintenance_guard(
    not_allow_methods: set[str] | None = None,
    message: str = "Fitur sedang dalam proses pembaruan data. Silakan coba kembali beberapa saat lagi.",
):
    """
    Matikan method tertentu sementara (respons 503), contoh:

    apiSettings.include_router(
        users_router.routerUsers,
        prefix="/sistem",
        dependencies=[maintenance_guard({"POST", "PUT", "PATCH", "DELETE"})]
    )
    """
    not_allow_methods = not_allow_methods or set()

    async def _guard(request: Request):
        if request.method in not_allow_methods:
            raise MaintenanceException(message)

    return Depends(_guard)


apiSettings = APIRouter()

# Start router Dokumentasi & Versi
apiSettings.include_router(api_docs.routerDocs)
apiSettings.include_router(api_docs.routerVersi)

# Start router Authentication
apiSettings.include_router(login_router.routerLogin)
apiSettings.include_router(users_router.routerUsers, prefix="/sistem")
