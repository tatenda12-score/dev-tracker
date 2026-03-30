import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import render


FRONTEND_DIR = settings.BASE_DIR / "Frontend"


def render_frontend_page(request, template_name: str):
    template_path = FRONTEND_DIR / template_name
    if not template_path.exists():
        raise Http404("Page not found")
    return render(request, template_name)


def serve_frontend_asset(request, asset_path: str):
    safe_path = (FRONTEND_DIR / asset_path).resolve()
    if FRONTEND_DIR.resolve() not in safe_path.parents and safe_path != FRONTEND_DIR.resolve():
        raise Http404("Asset not found")
    if not safe_path.exists() or not safe_path.is_file():
        raise Http404("Asset not found")

    content_type, _ = mimetypes.guess_type(str(safe_path))
    return FileResponse(open(safe_path, "rb"), content_type=content_type or "application/octet-stream")
