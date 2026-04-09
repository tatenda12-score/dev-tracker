import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import render


FRONTEND_DIR = settings.BASE_DIR / "Frontend"


def render_frontend_page(request, template_name: str):
    template_path = FRONTEND_DIR / template_name
    if not template_path.exists():
        raise Http404("Page not found")
    return render(request, template_name)


def build_openapi_schema(request):
    base_url = request.build_absolute_uri("/").rstrip("/")
    bearer_security = [{"BearerAuth": []}]
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Dev Tracker API",
            "version": "1.0.0",
            "description": "Production API documentation for the Dev Tracker system.",
        },
        "servers": [{"url": base_url}],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Paste the access token returned by /auth/login.",
                }
            },
            "schemas": {
                "LoginRequest": {
                    "type": "object",
                    "required": ["username", "password"],
                    "properties": {
                        "username": {"type": "string", "example": "admin@example.com"},
                        "password": {"type": "string", "example": "password123"},
                    },
                },
                "UserCreateRequest": {
                    "type": "object",
                    "required": ["name", "email", "password"],
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string", "format": "email"},
                        "password": {"type": "string"},
                    },
                },
                "AssignTaskRequest": {
                    "type": "object",
                    "required": ["title", "owner_id"],
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "owner_id": {"type": "integer"},
                        "estimated_hours": {"type": "number", "format": "float"},
                        "due_date": {"type": "string", "format": "date"},
                        "github_link": {"type": "string", "format": "uri"},
                    },
                },
                "CreateJobRequest": {
                    "type": "object",
                    "required": ["title", "owner_id"],
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "owner_id": {"type": "integer"},
                        "estimated_hours": {"type": "number", "format": "float"},
                        "due_date": {"type": "string", "format": "date"},
                        "github_link": {"type": "string", "format": "uri"},
                    },
                },
                "UpdateMessageRequest": {
                    "type": "object",
                    "required": ["message"],
                    "properties": {
                        "message": {"type": "string"},
                    },
                },
            },
        },
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health check",
                    "responses": {"200": {"description": "API is healthy"}},
                }
            },
            "/auth/login": {
                "post": {
                    "summary": "Login",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/LoginRequest"}
                            },
                            "application/x-www-form-urlencoded": {
                                "schema": {"$ref": "#/components/schemas/LoginRequest"}
                            },
                        },
                    },
                    "responses": {"200": {"description": "Login successful"}},
                }
            },
            "/auth/me": {
                "get": {
                    "summary": "Current authenticated user",
                    "security": bearer_security,
                    "responses": {"200": {"description": "Current user profile"}},
                }
            },
            "/users/register": {
                "post": {
                    "summary": "Register user",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserCreateRequest"}
                            }
                        },
                    },
                    "responses": {"201": {"description": "User created"}},
                }
            },
            "/users/": {
                "get": {
                    "summary": "List users",
                    "security": bearer_security,
                    "responses": {"200": {"description": "User list"}},
                }
            },
            "/users/promote/{user_id}": {
                "put": {
                    "summary": "Promote user to admin",
                    "security": bearer_security,
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {"200": {"description": "User promoted"}},
                }
            },
            "/users/{user_id}": {
                "delete": {
                    "summary": "Delete user",
                    "description": "Admin-only endpoint to permanently delete a user.",
                    "security": bearer_security,
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {
                        "200": {"description": "User deleted"},
                        "404": {"description": "User not found"},
                    },
                }
            },
            "/tasks/": {
                "get": {
                    "summary": "List all tasks",
                    "security": bearer_security,
                    "responses": {"200": {"description": "Task list"}},
                }
            },
            "/tasks/my-tasks": {
                "get": {
                    "summary": "List current user's tasks",
                    "security": bearer_security,
                    "responses": {"200": {"description": "My tasks"}},
                }
            },
            "/tasks/assign-task": {
                "post": {
                    "summary": "Assign task",
                    "security": bearer_security,
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AssignTaskRequest"}
                            }
                        },
                    },
                    "responses": {"200": {"description": "Task assigned"}},
                }
            },
            "/tasks/start/{task_id}": {
                "put": {
                    "summary": "Start task",
                    "security": bearer_security,
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {"200": {"description": "Task started"}},
                }
            },
            "/tasks/complete/{task_id}": {
                "put": {
                    "summary": "Complete task",
                    "security": bearer_security,
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {"200": {"description": "Task completed"}},
                }
            },
            "/tasks/update/{task_id}": {
                "post": {
                    "summary": "Add task update",
                    "security": bearer_security,
                    "parameters": [
                        {
                            "name": "task_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UpdateMessageRequest"}
                            }
                        },
                    },
                    "responses": {"200": {"description": "Task update added"}},
                }
            },
            "/job-cards/": {
                "get": {
                    "summary": "List job cards",
                    "security": bearer_security,
                    "responses": {"200": {"description": "Job card list"}},
                },
                "post": {
                    "summary": "Create job card",
                    "security": bearer_security,
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/CreateJobRequest"}
                            }
                        },
                    },
                    "responses": {"200": {"description": "Job created"}},
                },
            },
            "/job-cards/open/{job_id}": {
                "put": {
                    "summary": "Open job card",
                    "security": bearer_security,
                    "parameters": [
                        {
                            "name": "job_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {"200": {"description": "Job started"}},
                }
            },
            "/job-cards/close/{job_id}": {
                "put": {
                    "summary": "Close job card",
                    "security": bearer_security,
                    "parameters": [
                        {
                            "name": "job_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {"200": {"description": "Job closed"}},
                }
            },
            "/job-cards/update/{job_id}": {
                "post": {
                    "summary": "Add job update",
                    "security": bearer_security,
                    "parameters": [
                        {
                            "name": "job_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UpdateMessageRequest"}
                            }
                        },
                    },
                    "responses": {"200": {"description": "Job update added"}},
                }
            },
            "/analytics/dashboard": {
                "get": {
                    "summary": "Admin dashboard stats",
                    "security": bearer_security,
                    "responses": {"200": {"description": "Admin KPI summary"}},
                }
            },
            "/analytics/charts": {
                "get": {
                    "summary": "Admin charts data",
                    "security": bearer_security,
                    "responses": {"200": {"description": "Admin chart data"}},
                }
            },
            "/analytics/my-charts": {
                "get": {
                    "summary": "User chart data",
                    "security": bearer_security,
                    "responses": {"200": {"description": "User chart data"}},
                }
            },
        },
    }


def openapi_schema_view(request):
    return JsonResponse(build_openapi_schema(request))


def swagger_ui_view(request):
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dev Tracker API Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    <style>
        body { margin: 0; background: linear-gradient(180deg, #eef4ff 0%, #f8fbff 100%); font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; }
        .topbar { display: none; }
        .docs-header { padding: 24px 28px 12px; color: #0f172a; }
        .docs-header h1 { margin: 0 0 8px; font-size: 2rem; }
        .docs-header p { margin: 0; color: #475569; }
        #swagger-ui { margin: 0 auto 24px; max-width: 1200px; background: #fff; border: 1px solid rgba(15, 23, 42, 0.08); border-radius: 24px; box-shadow: 0 20px 60px rgba(37, 99, 235, 0.12); overflow: hidden; }
    </style>
</head>
<body>
    <div class="docs-header">
        <h1>Dev Tracker API</h1>
        <p>Swagger documentation for production operations, including user deletion and admin task controls.</p>
    </div>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.ui = SwaggerUIBundle({
            url: "/openapi.json",
            dom_id: "#swagger-ui",
            deepLinking: true,
            presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
            layout: "StandaloneLayout",
            persistAuthorization: true
        });
    </script>
</body>
</html>"""
    return HttpResponse(html)


def serve_frontend_asset(request, asset_path: str):
    safe_path = (FRONTEND_DIR / asset_path).resolve()
    if FRONTEND_DIR.resolve() not in safe_path.parents and safe_path != FRONTEND_DIR.resolve():
        raise Http404("Asset not found")
    if not safe_path.exists() or not safe_path.is_file():
        raise Http404("Asset not found")

    content_type, _ = mimetypes.guess_type(str(safe_path))
    return FileResponse(open(safe_path, "rb"), content_type=content_type or "application/octet-stream")
