import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_portal.settings")

from app.main import app as fastapi_app, startup as fastapi_startup


fastapi_startup()
django_asgi_app = get_asgi_application()

API_PREFIXES = (
    "/auth",
    "/users",
    "/tasks",
    "/job-cards",
    "/analytics",
    "/admin",
    "/health",
    "/protected",
)


async def application(scope, receive, send):
    scope_type = scope.get("type")
    path = scope.get("path", "")

    if scope_type == "lifespan":
        message = await receive()
        if message["type"] == "lifespan.startup":
            await send({"type": "lifespan.startup.complete"})
        elif message["type"] == "lifespan.shutdown":
            await send({"type": "lifespan.shutdown.complete"})
        return

    if any(path == prefix or path.startswith(f"{prefix}/") for prefix in API_PREFIXES):
        await fastapi_app(scope, receive, send)
        return

    await django_asgi_app(scope, receive, send)
