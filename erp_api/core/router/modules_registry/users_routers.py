"""
============================================= Start Noted users_routers ===================================
Author : PT. Dapur Perangkat Lunak Indonesia | KoffieSoft Group | https://www.koffiesoft.com/ | info@koffiesoft.com
1. Daftar router modul `users` (core/modules/users), hanya di-import oleh core/router/api_router.py
2. Sengaja TIDAK ditaruh di core/modules/users/__init__.py: __init__.py ikut dijalankan setiap kali
   apa pun di bawah paket tsb di-import (termasuk model/crud) -> memuat semua router -> circular import.
3. Pemanggilan di api_router.py:
    from core.router.modules_registry.users_routers import nama_router
4. Panduan lengkap: core/router/router_readme.md
============================================= END Noted users_routers ===================================
"""

from core.modules.users.router import users_router
