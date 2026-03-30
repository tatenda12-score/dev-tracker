from django.urls import path, re_path

from .views import render_frontend_page, serve_frontend_asset


urlpatterns = [
    path("", lambda request: render_frontend_page(request, "index.html")),
    path("index.html", lambda request: render_frontend_page(request, "index.html")),
    path("login.html", lambda request: render_frontend_page(request, "login.html")),
    path("register.html", lambda request: render_frontend_page(request, "register.html")),
    path("dashboard.html", lambda request: render_frontend_page(request, "dashboard.html")),
    path("admin.html", lambda request: render_frontend_page(request, "admin.html")),
    re_path(r"^(?P<asset_path>(?:images/.+)|(?:.+\.(?:css|js|png|jpg|jpeg|gif|svg|webp|mp4)))$", serve_frontend_asset),
]
