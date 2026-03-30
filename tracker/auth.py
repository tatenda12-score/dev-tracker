from datetime import datetime, timedelta
import os

from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from jose import JWTError, jwt

from .models import TrackerUser


SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def serialize_user(user: TrackerUser):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }


def hash_password(password: str):
    return make_password(str(password)[:72])


def verify_password(plain_password: str, password_hash: str):
    return check_password(str(plain_password)[:72], password_hash)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        email = payload.get("sub")
        if not user_id or not email:
            return None
        return TrackerUser.objects.filter(id=user_id, email=email).first()
    except JWTError:
        return None


def require_auth(request):
    user = get_current_user(request)
    if not user:
        return None, JsonResponse({"detail": "Invalid authentication credentials"}, status=401)
    return user, None


def require_admin(request):
    user, error = require_auth(request)
    if error:
        return None, error
    if user.role != "ADMIN":
        return None, JsonResponse({"detail": "Admin only"}, status=403)
    return user, None
