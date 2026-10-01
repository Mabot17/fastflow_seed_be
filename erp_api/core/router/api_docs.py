# ============================================= Start Noted API Docs ===================================
# Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
# 1. Halaman dokumentasi: /docs (Swagger), /redoc, /rapidoc
# 2. Versi API: /version, /version/changelog (isi CHANGELOG.md)
# 3. Bagian dari kerangka (bukan modul), didaftarkan di api_router.py
# ============================================= END Noted API Docs ===================================
import logging

from fastapi import APIRouter, Request
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
from fastapi.responses import HTMLResponse, PlainTextResponse

from core.config import ROOT_FOLDER
from core.router.api_metadata import TITLE_API, VERSI_API

routerDocs = APIRouter(include_in_schema=False)
routerVersi = APIRouter(tags=["Version"])


def _openapi_url(request: Request) -> str:
    return f"{request.scope.get('root_path', '')}/openapi.json"


@routerDocs.get("/docs")
async def swagger_ui_html(request: Request):
    return get_swagger_ui_html(
        openapi_url=_openapi_url(request),
        title=f"{TITLE_API} - Swagger UI",
        oauth2_redirect_url="/docs/oauth2-redirect",
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui.css",
        swagger_ui_parameters={"docExpansion": "none", "filter": True, "defaultModelsExpandDepth": -1},
    )


@routerDocs.get("/docs/oauth2-redirect")
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@routerDocs.get("/redoc")
async def redoc_html(request: Request):
    return get_redoc_html(
        openapi_url=_openapi_url(request),
        title=f"{TITLE_API} - ReDoc",
        redoc_js_url="https://unpkg.com/redoc@2.1.5/bundles/redoc.standalone.js",
    )


@routerDocs.get("/rapidoc")
async def rapidoc_html(request: Request):
    return HTMLResponse(f"""<!DOCTYPE html>
<html>
<head>
    <title>{TITLE_API} - RapiDoc</title>
    <meta charset="utf-8"/>
    <script type="module" src="https://unpkg.com/rapidoc@9.3.8/dist/rapidoc-min.js"></script>
</head>
<body>
    <rapi-doc spec-url="{_openapi_url(request)}" theme="light" render-style="focused"
              allow-search="true" allow-advanced-search="true" use-path-in-nav-bar="true"
              show-method-in-nav-bar="as-colored-block" allow-authentication="true"></rapi-doc>
</body>
</html>""")


@routerVersi.get("/", include_in_schema=False)
@routerVersi.get("/version")
async def versi():
    return {"version": VERSI_API}


@routerVersi.get("/version/changelog", response_class=PlainTextResponse)
async def changelog():
    path = ROOT_FOLDER / "CHANGELOG.md"
    try:
        return path.read_bytes().decode("utf-8", errors="replace")
    except FileNotFoundError:
        return "CHANGELOG.md tidak ditemukan"
    except Exception as e:
        logging.error(f"Error membaca CHANGELOG.md: {e}")
        return "Gagal membaca CHANGELOG.md"
