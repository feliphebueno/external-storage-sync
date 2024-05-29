from django.conf import settings
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.utils.safestring import mark_safe

from .models import FileSync


@admin.register(FileSync)
class FileSyncAdmin(ModelAdmin):
    list_display = ("id", "file_name", "created_at", "synced_at")
    search_fields = ("file_name", "payload_checksum", "ref_id")
    readonly_fields = [
        "oeid",
        "file_name",
        "payload_checksum",
        "file_path",
        "ref_id",
        "file_type",
        "created_at",
        "synced_at",
        "file_preview",
    ]

    def file_preview(self, obj: FileSync):
        if not (obj.synced_at):
            return "File not synced"

        file_url = f"{settings.MEDIA_URL}{obj.file_name}"

        return mark_safe(
            f"""<a target="_blank" title="Click to open full image" href="{file_url}">"""
            f"""<img width="600px" src="{file_url}" />"""
            """</a>"""
        )
