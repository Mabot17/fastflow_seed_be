"""
============================================= Start Noted auth_routers ===================================
Author : FastFlow | https://github.com/Mabot17/fastflow_seed_be
1. Daftar router modul `auth` (core/modules/auth), hanya di-import oleh core/router/api_router.py
2. Sengaja TIDAK ditaruh di core/modules/auth/__init__.py: __init__.py ikut dijalankan setiap kali
   apa pun di bawah paket tsb di-import (termasuk model/crud) -> memuat semua router -> circular import.
3. Pemanggilan di api_router.py:
    from core.router.modules_registry.auth_routers import nama_router
4. Panduan lengkap: core/router/router_readme.md
============================================= END Noted auth_routers ===================================
"""

from core.modules.auth.router import login_router
