from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="due_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="task",
            name="estimated_hours",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="jobcard",
            name="due_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="jobcard",
            name="estimated_hours",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
