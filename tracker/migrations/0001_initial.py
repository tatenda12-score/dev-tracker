from django.db import migrations, models
import django.db.models.deletion

import tracker.time_utils


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TrackerUser",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("email", models.EmailField(db_index=True, max_length=254, unique=True)),
                ("password_hash", models.CharField(max_length=255)),
                ("role", models.CharField(default="USER", max_length=20)),
                ("created_at", models.DateTimeField(default=tracker.time_utils.now_harare)),
            ],
            options={"db_table": "users"},
        ),
        migrations.CreateModel(
            name="JobCard",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, null=True)),
                ("github_link", models.CharField(blank=True, max_length=500, null=True)),
                ("status", models.CharField(db_index=True, default="Pending", max_length=50)),
                ("created_at", models.DateTimeField(default=tracker.time_utils.now_harare)),
                ("opened_at", models.DateTimeField(blank=True, null=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("duration", models.FloatField(blank=True, null=True)),
                ("assigned_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assigned_jobs", to="tracker.trackeruser")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="job_cards", to="tracker.trackeruser")),
            ],
            options={"db_table": "job_cards"},
        ),
        migrations.CreateModel(
            name="Task",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, null=True)),
                ("github_link", models.CharField(blank=True, max_length=500, null=True)),
                ("status", models.CharField(db_index=True, default="Pending", max_length=50)),
                ("created_at", models.DateTimeField(default=tracker.time_utils.now_harare)),
                ("start_time", models.DateTimeField(blank=True, null=True)),
                ("end_time", models.DateTimeField(blank=True, null=True)),
                ("time_taken", models.FloatField(blank=True, null=True)),
                ("hours_spent", models.FloatField(default=0)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("assigned_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assigned_tasks", to="tracker.trackeruser")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tasks", to="tracker.trackeruser")),
            ],
            options={"db_table": "tasks"},
        ),
        migrations.CreateModel(
            name="TaskUpdate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(default=tracker.time_utils.now_harare)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tracker.trackeruser")),
                ("task", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="updates", to="tracker.task")),
            ],
            options={"db_table": "task_updates"},
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.CharField(max_length=500)),
                ("is_read", models.BooleanField(db_index=True, default=False)),
                ("created_at", models.DateTimeField(default=tracker.time_utils.now_harare)),
                ("sender", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="sent_notifications", to="tracker.trackeruser")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="tracker.trackeruser")),
            ],
            options={"db_table": "notifications"},
        ),
        migrations.CreateModel(
            name="JobUpdate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(default=tracker.time_utils.now_harare)),
                ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="updates", to="tracker.jobcard")),
            ],
            options={"db_table": "job_updates"},
        ),
    ]
