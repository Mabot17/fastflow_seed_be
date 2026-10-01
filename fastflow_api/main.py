# ============================================= Start Noted Main ===================================
# Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
# 1. Entry point: uvicorn main:app (jalankan dari folder fastflow_api)
# 2. Urutan request: CORS -> api_middleware_response -> LoggingMiddleware -> api_router
# 3. `app` di akhir file adalah Socket.IO yang membungkus FastAPI (fastapi_app)
# ============================================= END Noted Main ===================================
import json

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core import config
from core.jobs.jobs_config import lifespan
from core.router import api_router
from core.router.api_log_middleware import LoggingMiddleware
from core.router.api_metadata import DESCRIPTION_API, TAGS_METADATA_API, TITLE_API, VERSI_API
from core.router.api_middleware import (
    MaintenanceException,
    api_middleware_response,
    maintenance_exception_handler,
    validation_exception_handler,
)
from core.socket.socket_router import get_socket_app
from core.utils import log

logger = log.setup_custom_logger("root")

fastapi_app = FastAPI(
    title=TITLE_API,
    version=VERSI_API,
    description=DESCRIPTION_API,
    openapi_tags=TAGS_METADATA_API,
    root_path=config.ROOT_PATH,
    lifespan=lifespan,
    docs_url=None,       # halaman docs custom di core/router/api_docs.py
    redoc_url=None,
)

fastapi_app.mount("/static", StaticFiles(directory=str(config.UPLOAD_FOLDER)), name="static")
fastapi_app.include_router(api_router.apiSettings)


def build_custom_openapi(app: FastAPI):
    """Contoh respons error yang identik dipindah ke components/responses lalu dirujuk dengan $ref."""
    default_openapi = app.openapi

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        spec = default_openapi()
        components = spec.setdefault("components", {}).setdefault("responses", {})
        index = {}
        for operations in spec.get("paths", {}).values():
            for operation in operations.values():
                responses = operation.get("responses", {})
                for code, response in list(responses.items()):
                    if code.startswith("2"):
                        continue
                    key = json.dumps(response, sort_keys=True)
                    if key not in index:
                        name = f"Error{code}" if f"Error{code}" not in components else f"Error{code}_{len(components)}"
                        components[name] = response
                        index[key] = name
                    responses[code] = {"$ref": f"#/components/responses/{index[key]}"}
        app.openapi_schema = spec
        return spec

    return custom_openapi


fastapi_app.openapi = build_custom_openapi(fastapi_app)

fastapi_app.add_exception_handler(RequestValidationError, validation_exception_handler)
fastapi_app.add_exception_handler(MaintenanceException, maintenance_exception_handler)
fastapi_app.add_middleware(LoggingMiddleware)
fastapi_app.middleware("http")(api_middleware_response)
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=config.CORS_ORIGINS != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Server ASGI utama (Socket.IO + FastAPI)
app = get_socket_app(fastapi_app)
