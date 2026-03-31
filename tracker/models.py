from django.db import models

from .time_utils import now_harare


class TrackerUser(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, db_index=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=20, default="USER")
    created_at = models.DateTimeField(default=now_harare)

    class Meta:
        db_table = "users"


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    github_link = models.CharField(max_length=500, null=True, blank=True)
    owner = models.ForeignKey(TrackerUser, related_name="tasks", on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(TrackerUser, related_name="assigned_tasks", on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default="Pending", db_index=True)
    created_at = models.DateTimeField(default=now_harare)
    estimated_hours = models.FloatField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    time_taken = models.FloatField(null=True, blank=True)
    hours_spent = models.FloatField(default=0)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "tasks"


class TaskUpdate(models.Model):
    task = models.ForeignKey(Task, related_name="updates", on_delete=models.CASCADE)
    author = models.ForeignKey(TrackerUser, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(default=now_harare)

    class Meta:
        db_table = "task_updates"


class JobCard(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    github_link = models.CharField(max_length=500, null=True, blank=True)
    owner = models.ForeignKey(TrackerUser, related_name="job_cards", on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(TrackerUser, related_name="assigned_jobs", on_delete=models.CASCADE)
    status = models.CharField(max_length=50, default="Pending", db_index=True)
    created_at = models.DateTimeField(default=now_harare)
    estimated_hours = models.FloatField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = "job_cards"


class JobUpdate(models.Model):
    job = models.ForeignKey(JobCard, related_name="updates", on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(default=now_harare)

    class Meta:
        db_table = "job_updates"


class Notification(models.Model):
    message = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(default=now_harare)
    user = models.ForeignKey(TrackerUser, related_name="notifications", on_delete=models.CASCADE)
    sender = models.ForeignKey(TrackerUser, related_name="sent_notifications", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        db_table = "notifications"
