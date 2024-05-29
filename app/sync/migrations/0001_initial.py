# Generated by Django 5.0.3 on 2024-03-31 23:30

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FileSync",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("oeid", models.CharField(db_index=True, max_length=30)),
                ("file_name", models.CharField(db_index=True, max_length=35)),
                ("payload_checksum", models.CharField(db_index=True, max_length=255)),
                ("file_path", models.CharField(default=None, max_length=255, null=True)),
                ("ref_id", models.CharField(db_index=True, max_length=30)),
                ("file_type", models.CharField(max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("synced_at", models.DateTimeField(default=None, null=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]