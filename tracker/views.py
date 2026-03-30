import json
from datetime import timedelta

from django.db.models import Sum
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .auth import create_access_token, hash_password, require_admin, require_auth, serialize_user, verify_password
from .models import JobCard, JobUpdate, Notification, Task, TaskUpdate, TrackerUser
from .time_utils import ensure_harare, now_harare


def parse_body(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}
    return request.POST.dict()


def serialize_task(task):
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "start_time": task.start_time.isoformat() if task.start_time else None,
        "end_time": task.end_time.isoformat() if task.end_time else None,
        "time_taken": float(task.time_taken or 0),
        "hours_spent": float(task.hours_spent or 0),
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "github_link": task.github_link,
        "owner_id": task.owner_id,
        "assigned_by_id": task.assigned_by_id,
    }


def serialize_task_update(update):
    return {
        "id": update.id,
        "message": update.message,
        "created_at": update.created_at.isoformat() if update.created_at else None,
        "author_name": update.author.name if update.author_id else "Unknown",
        "author_role": update.author.role if update.author_id else "USER",
    }


def serialize_job(job):
    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "status": job.status,
        "owner_id": job.owner_id,
        "assigned_by_id": job.assigned_by_id,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "opened_at": job.opened_at.isoformat() if job.opened_at else None,
        "closed_at": job.closed_at.isoformat() if job.closed_at else None,
        "duration": float(job.duration or 0),
        "github_link": job.github_link,
    }


def serialize_job_update(update):
    return {
        "id": update.id,
        "message": update.message,
        "created_at": update.created_at.isoformat() if update.created_at else None,
        "author_name": "Team update",
        "author_role": "INFO",
    }


def create_notification(user_id, sender_id, message):
    Notification.objects.create(message=message, user_id=user_id, sender_id=sender_id, is_read=False, created_at=now_harare())


def build_user_daily_chart(user_id: int, days: int = 7):
    today = now_harare()
    labels, item_counts, hour_totals = [], [], []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        task_count = Task.objects.filter(owner_id=user_id, completed_at__range=(start, end)).count()
        job_count = JobCard.objects.filter(owner_id=user_id, closed_at__range=(start, end)).count()
        task_hours = Task.objects.filter(owner_id=user_id, completed_at__range=(start, end)).aggregate(total=Sum("hours_spent"))["total"] or 0
        job_seconds = JobCard.objects.filter(owner_id=user_id, closed_at__range=(start, end)).aggregate(total=Sum("duration"))["total"] or 0
        labels.append(day.strftime("%a"))
        item_counts.append(int(task_count) + int(job_count))
        hour_totals.append(round((float(task_hours) * 3600 + float(job_seconds)) / 3600, 2))
    return {"labels": labels, "items": item_counts, "hours": hour_totals}


def build_admin_daily_chart(days: int = 7):
    today = now_harare()
    labels, completed_items, performance_hours = [], [], []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        task_count = Task.objects.filter(completed_at__range=(start, end)).count()
        job_count = JobCard.objects.filter(closed_at__range=(start, end)).count()
        task_hours = Task.objects.filter(completed_at__range=(start, end)).aggregate(total=Sum("hours_spent"))["total"] or 0
        job_seconds = JobCard.objects.filter(closed_at__range=(start, end)).aggregate(total=Sum("duration"))["total"] or 0
        labels.append(day.strftime("%a"))
        completed_items.append(int(task_count) + int(job_count))
        performance_hours.append(round(float(task_hours) + (float(job_seconds) / 3600), 2))
    return {"labels": labels, "completed_items": completed_items, "hours": performance_hours}


def health_check(request):
    return JsonResponse({"status": "ok"})


def protected_route(request):
    current_user, error = require_auth(request)
    if error:
        return error
    return JsonResponse({"success": True, "message": "You are authenticated", "user": {"email": current_user.email, "role": current_user.role}})


@csrf_exempt
def login_view(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    username = request.POST.get("username") or request.POST.get("email")
    password = request.POST.get("password", "")
    user = TrackerUser.objects.filter(email=username).first()
    if not user or not verify_password(password, user.password_hash):
        return JsonResponse({"detail": "Invalid email or password"}, status=401)
    access_token = create_access_token({"sub": user.email, "user_id": user.id, "role": user.role})
    return JsonResponse({"success": True, "data": {"access_token": access_token, "token_type": "bearer", "user": serialize_user(user)}, "message": "Login successful"})


def auth_me(request):
    current_user, error = require_auth(request)
    if error:
        return error
    return JsonResponse({"success": True, "data": serialize_user(current_user)})


@csrf_exempt
def register_user(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    data = parse_body(request)
    email = (data.get("email") or "").strip()
    if TrackerUser.objects.filter(email=email).exists():
        return JsonResponse({"detail": "Email already registered"}, status=409)
    user = TrackerUser.objects.create(
        name=(data.get("name") or "").strip(),
        email=email,
        password_hash=hash_password(data.get("password", "")),
        role="USER",
        created_at=now_harare(),
    )
    return JsonResponse({"success": True, "data": serialize_user(user), "message": "User created successfully"}, status=201)


def user_me(request):
    return auth_me(request)


@csrf_exempt
def users_collection(request):
    if request.method != "GET":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    _, error = require_admin(request)
    if error:
        return error
    skip = int(request.GET.get("skip", 0))
    limit = int(request.GET.get("limit", 10))
    search = request.GET.get("search")
    users = TrackerUser.objects.all().order_by("id")
    if search:
        users = users.filter(email__icontains=search)
    return JsonResponse({"success": True, "data": [serialize_user(user) for user in users[skip:skip + limit]]})


@csrf_exempt
def promote_user(request, user_id):
    _, error = require_admin(request)
    if error:
        return error
    user = TrackerUser.objects.filter(id=user_id).first()
    if not user:
        return JsonResponse({"detail": "User not found"}, status=404)
    if user.role == "ADMIN":
        return JsonResponse({"success": False, "message": "User already admin"})
    user.role = "ADMIN"
    user.save(update_fields=["role"])
    return JsonResponse({"success": True, "message": f"{user.email} promoted to ADMIN"})


@csrf_exempt
def delete_user(request, user_id):
    _, error = require_admin(request)
    if error:
        return error
    user = TrackerUser.objects.filter(id=user_id).first()
    if not user:
        return JsonResponse({"detail": "User not found"}, status=404)
    user.delete()
    return JsonResponse({"success": True, "message": "User deleted"})


def my_tasks(request):
    current_user, error = require_auth(request)
    if error:
        return error
    tasks = Task.objects.filter(owner=current_user).order_by("-id")
    return JsonResponse({"success": True, "data": [serialize_task(task) for task in tasks]})


def tasks_collection(request):
    current_user, error = require_admin(request)
    if error:
        return error
    tasks = Task.objects.select_related("owner").order_by("-id")
    data = [{
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "github_link": task.github_link,
        "owner_name": task.owner.name if task.owner_id else "Unknown",
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "time_taken": float(task.time_taken or 0),
    } for task in tasks]
    return JsonResponse({"success": True, "data": data})


@csrf_exempt
def start_task(request, task_id):
    current_user, error = require_auth(request)
    if error:
        return error
    task = Task.objects.filter(id=task_id).first()
    if not task:
        return JsonResponse({"detail": "Task not found"}, status=404)
    if task.owner_id != current_user.id:
        return JsonResponse({"detail": "Not allowed"}, status=403)
    if task.status == "In Progress":
        return JsonResponse({"success": False, "message": "Already started"})
    task.status = "In Progress"
    task.start_time = now_harare()
    task.save(update_fields=["status", "start_time"])
    return JsonResponse({"success": True, "message": "Task started"})


@csrf_exempt
def complete_task(request, task_id):
    current_user, error = require_auth(request)
    if error:
        return error
    task = Task.objects.filter(id=task_id).first()
    if not task:
        return JsonResponse({"detail": "Task not found"}, status=404)
    if task.owner_id != current_user.id:
        return JsonResponse({"detail": "Not allowed"}, status=403)
    if not task.start_time:
        return JsonResponse({"success": False, "message": "Start task first"})
    if task.status == "Completed":
        return JsonResponse({"success": False, "message": "Already completed"})
    task.status = "Completed"
    task.end_time = now_harare()
    task.time_taken = (ensure_harare(task.end_time) - ensure_harare(task.start_time)).total_seconds()
    task.hours_spent = round(task.time_taken / 3600, 2)
    task.completed_at = task.end_time
    task.save()
    for admin in TrackerUser.objects.filter(role="ADMIN"):
        create_notification(admin.id, current_user.id, f"{current_user.name} completed task: {task.title}")
    return JsonResponse({"success": True, "message": "Task completed"})


@csrf_exempt
def assign_task(request):
    current_user, error = require_admin(request)
    if error:
        return error
    data = parse_body(request)
    title = data.get("title")
    owner_id = data.get("owner_id")
    if not title or not owner_id:
        return JsonResponse({"detail": "Missing fields"}, status=400)
    task = Task.objects.create(
        title=title,
        description=data.get("description"),
        owner_id=int(owner_id),
        assigned_by=current_user,
        status="Pending",
        github_link=data.get("github_link"),
        created_at=now_harare(),
    )
    create_notification(task.owner_id, current_user.id, f"New task assigned: {title}")
    return JsonResponse({"success": True, "message": "Task assigned successfully"})


@csrf_exempt
def add_task_update(request, task_id):
    current_user, error = require_auth(request)
    if error:
        return error
    task = Task.objects.filter(id=task_id).first()
    if not task:
        return JsonResponse({"detail": "Task not found"}, status=404)
    if current_user.role != "ADMIN" and task.owner_id != current_user.id:
        return JsonResponse({"detail": "Not allowed"}, status=403)
    data = parse_body(request)
    message = (data.get("message") or "").strip()
    if not message:
        return JsonResponse({"detail": "Message required"}, status=400)
    update = TaskUpdate.objects.create(task=task, author=current_user, message=message, created_at=now_harare())
    if current_user.role == "ADMIN":
        create_notification(task.owner_id, current_user.id, f"Admin commented on task: {task.title}")
    else:
        for admin in TrackerUser.objects.filter(role="ADMIN"):
            create_notification(admin.id, current_user.id, f"{current_user.name} updated task: {task.title}")
    return JsonResponse({"success": True, "message": "Task update added", "data": serialize_task_update(update)})


def notifications_collection(request):
    current_user, error = require_auth(request)
    if error:
        return error
    notifications = Notification.objects.filter(user=current_user).order_by("-created_at")
    return JsonResponse({
        "success": True,
        "data": [{"id": n.id, "message": n.message, "is_read": n.is_read, "created_at": n.created_at.isoformat() if n.created_at else None} for n in notifications],
        "meta": {"unread_count": notifications.filter(is_read=False).count()},
    })


@csrf_exempt
def mark_notifications_read(request):
    current_user, error = require_auth(request)
    if error:
        return error
    Notification.objects.filter(user=current_user, is_read=False).update(is_read=True)
    return JsonResponse({"success": True, "message": "Marked as read"})


@csrf_exempt
def mark_single_notification_read(request, notification_id):
    current_user, error = require_auth(request)
    if error:
        return error
    notification = Notification.objects.filter(id=notification_id, user=current_user).first()
    if not notification:
        return JsonResponse({"detail": "Notification not found"}, status=404)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return JsonResponse({"success": True, "message": "Notification marked as read"})


def my_dashboard(request):
    current_user, error = require_auth(request)
    if error:
        return error
    tasks = Task.objects.filter(owner=current_user)
    total_seconds = sum(task.time_taken or 0 for task in tasks)
    return JsonResponse({"success": True, "data": {
        "name": current_user.name,
        "assigned": tasks.count(),
        "completed": tasks.filter(status="Completed").count(),
        "in_progress": tasks.filter(status="In Progress").count(),
        "hours": round(total_seconds / 3600, 2),
    }})


def task_detail(request, task_id):
    current_user, error = require_auth(request)
    if error:
        return error
    task = Task.objects.filter(id=task_id).select_related("owner", "assigned_by").first()
    if not task:
        return JsonResponse({"detail": "Task not found"}, status=404)
    if current_user.role != "ADMIN" and task.owner_id != current_user.id:
        return JsonResponse({"detail": "Not allowed"}, status=403)
    updates = TaskUpdate.objects.filter(task=task).select_related("author").order_by("created_at")
    return JsonResponse({"success": True, "data": {
        "task": {**serialize_task(task), "owner_name": task.owner.name, "assigned_by_name": task.assigned_by.name},
        "updates": [serialize_task_update(update) for update in updates],
    }})


def job_cards_collection(request):
    current_user, error = require_auth(request)
    if error:
        return error
    if request.method == "POST":
        if current_user.role != "ADMIN":
            return JsonResponse({"detail": "Admin only"}, status=403)
        data = parse_body(request)
        title = data.get("title")
        owner_id = data.get("owner_id")
        if not title or not owner_id:
            return JsonResponse({"detail": "Missing required fields"}, status=400)
        job = JobCard.objects.create(
            title=title,
            description=data.get("description"),
            owner_id=int(owner_id),
            assigned_by=current_user,
            status="Pending",
            github_link=data.get("github_link"),
            created_at=now_harare(),
        )
        create_notification(job.owner_id, current_user.id, f"New job assigned: {title}")
        return JsonResponse({"success": True, "message": "Job created successfully", "data": serialize_job(job)})
    jobs = JobCard.objects.order_by("-id") if current_user.role == "ADMIN" else JobCard.objects.filter(owner=current_user).order_by("-id")
    return JsonResponse({"success": True, "data": [serialize_job(job) for job in jobs]})


@csrf_exempt
def open_job(request, job_id):
    current_user, error = require_auth(request)
    if error:
        return error
    job = JobCard.objects.filter(id=job_id).first()
    if not job:
        return JsonResponse({"detail": "Job not found"}, status=404)
    if job.owner_id != current_user.id:
        return JsonResponse({"detail": "Not allowed"}, status=403)
    if job.status == "Closed":
        return JsonResponse({"detail": "Job already closed"}, status=400)
    if job.status == "Open":
        return JsonResponse({"success": False, "message": "Already open"})
    job.status = "Open"
    job.opened_at = now_harare()
    job.save(update_fields=["status", "opened_at"])
    return JsonResponse({"success": True, "message": "Job started"})


@csrf_exempt
def add_job_update(request, job_id):
    current_user, error = require_auth(request)
    if error:
        return error
    job = JobCard.objects.filter(id=job_id).first()
    if not job:
        return JsonResponse({"detail": "Job not found"}, status=404)
    if current_user.role != "ADMIN" and job.owner_id != current_user.id:
        return JsonResponse({"detail": "Not allowed"}, status=403)
    if current_user.role != "ADMIN" and job.status != "Open":
        return JsonResponse({"detail": "Job must be open"}, status=400)
    data = parse_body(request)
    message = (data.get("message") or "").strip()
    if not message:
        return JsonResponse({"detail": "Message required"}, status=400)
    update = JobUpdate.objects.create(job=job, message=message, created_at=now_harare())
    if current_user.role == "ADMIN":
        create_notification(job.owner_id, current_user.id, f"Admin updated job: {job.title}")
    else:
        for admin in TrackerUser.objects.filter(role="ADMIN"):
            create_notification(admin.id, current_user.id, f"{current_user.name} updated job: {job.title}")
    return JsonResponse({"success": True, "message": "Update added", "data": serialize_job_update(update)})


@csrf_exempt
def close_job(request, job_id):
    current_user, error = require_auth(request)
    if error:
        return error
    job = JobCard.objects.filter(id=job_id).first()
    if not job:
        return JsonResponse({"detail": "Job not found"}, status=404)
    if job.owner_id != current_user.id:
        return JsonResponse({"detail": "Not allowed"}, status=403)
    job.status = "Closed"
    job.closed_at = now_harare()
    if job.opened_at and job.closed_at:
        job.duration = (ensure_harare(job.closed_at) - ensure_harare(job.opened_at)).total_seconds()
    job.save()
    for admin in TrackerUser.objects.filter(role="ADMIN"):
        create_notification(admin.id, current_user.id, f"{current_user.name} closed job: {job.title}")
    return JsonResponse({"success": True, "message": "Job closed"})


def job_detail(request, job_id):
    current_user, error = require_auth(request)
    if error:
        return error
    job = JobCard.objects.filter(id=job_id).select_related("owner", "assigned_by").first()
    if not job:
        return JsonResponse({"detail": "Job not found"}, status=404)
    if current_user.role != "ADMIN" and job.owner_id != current_user.id:
        return JsonResponse({"detail": "Not allowed"}, status=403)
    updates = JobUpdate.objects.filter(job=job).order_by("created_at")
    return JsonResponse({"success": True, "data": {
        "job": {**serialize_job(job), "owner_name": job.owner.name, "assigned_by_name": job.assigned_by.name},
        "updates": [serialize_job_update(update) for update in updates],
    }})


def total_hours(request):
    current_user, error = require_auth(request)
    if error:
        return error
    total = Task.objects.filter(owner=current_user).aggregate(total=Sum("hours_spent"))["total"] or 0
    return JsonResponse({"success": True, "data": {"user": current_user.email, "total_hours": float(total)}, "message": "Total hours retrieved successfully"})


def weekly_summary(request):
    current_user, error = require_auth(request)
    if error:
        return error
    one_week_ago = now_harare() - timedelta(days=7)
    total = Task.objects.filter(owner=current_user, completed_at__gte=one_week_ago).aggregate(total=Sum("hours_spent"))["total"] or 0
    return JsonResponse({"success": True, "data": {"week_start": str(one_week_ago.date()), "total_hours": float(total)}, "message": "Weekly summary retrieved successfully"})


def leaderboard(request):
    _, error = require_admin(request)
    if error:
        return error
    rows = []
    for user in TrackerUser.objects.all():
        total = Task.objects.filter(owner=user).aggregate(total=Sum("hours_spent"))["total"] or 0
        if total:
            rows.append({"user": user.email, "total_hours": float(total)})
    rows.sort(key=lambda row: row["total_hours"], reverse=True)
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return JsonResponse({"success": True, "data": rows, "message": "Leaderboard retrieved successfully"})


def whoami(request):
    current_user, error = require_auth(request)
    if error:
        return error
    return JsonResponse({"email": current_user.email, "role": current_user.role})


def productivity_score(request):
    current_user, error = require_auth(request)
    if error:
        return error
    one_week_ago = now_harare() - timedelta(days=7)
    total = Task.objects.filter(owner=current_user, completed_at__gte=one_week_ago).aggregate(total=Sum("hours_spent"))["total"] or 0
    return JsonResponse({"success": True, "data": {"user": current_user.email, "weekly_hours": float(total), "productivity_score": round(float(total) / 7, 2)}, "message": "Productivity score calculated successfully"})


def my_charts(request):
    current_user, error = require_auth(request)
    if error:
        return error
    completed = Task.objects.filter(owner=current_user, status="Completed").count() + JobCard.objects.filter(owner=current_user, status="Closed").count()
    in_progress = Task.objects.filter(owner=current_user, status="In Progress").count() + JobCard.objects.filter(owner=current_user, status="Open").count()
    pending = Task.objects.filter(owner=current_user, status="Pending").count() + JobCard.objects.filter(owner=current_user, status="Pending").count()
    return JsonResponse({"success": True, "data": {
        "pie": {"labels": ["Completed", "In Progress", "Pending"], "data": [completed, in_progress, pending]},
        "bar": build_user_daily_chart(current_user.id, days=7),
        "line": build_user_daily_chart(current_user.id, days=7),
    }})


def admin_dashboard(request):
    _, error = require_admin(request)
    if error:
        return error
    return JsonResponse({
        "total_jobs": JobCard.objects.count(),
        "active_tasks": Task.objects.filter(status="In Progress").count(),
        "completed_tasks": Task.objects.filter(status="Completed").count(),
        "overdue_tasks": Task.objects.filter(status="Overdue").count(),
    })


def analytics_charts(request):
    _, error = require_admin(request)
    if error:
        return error
    completed = Task.objects.filter(status="Completed").count() + JobCard.objects.filter(status="Closed").count()
    in_progress = Task.objects.filter(status="In Progress").count() + JobCard.objects.filter(status="Open").count()
    pending = Task.objects.filter(status="Pending").count() + JobCard.objects.filter(status="Pending").count()
    chart = build_admin_daily_chart(days=7)
    return JsonResponse({
        "pie": {"labels": ["Completed", "In Progress", "Pending"], "data": [completed, in_progress, pending]},
        "bar": {"labels": chart["labels"], "data": chart["completed_items"]},
        "line": {"labels": chart["labels"], "data": chart["hours"]},
    })
