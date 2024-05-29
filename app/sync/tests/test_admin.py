from unittest import mock

from model_bakery import baker

from django.test import override_settings, TestCase
from django.utils import safestring, timezone

from app.sync import admin
from app.sync.models import FileSync


class FileSyncAdminTest(TestCase):
    def test_file_preview_with_not_synced_obj(self):
        # Not synced
        file_sync_obj = baker.make("sync.FileSync", synced_at=None)
        file_sync_admin = admin.FileSyncAdmin(FileSync, mock.Mock())

        result = file_sync_admin.file_preview(file_sync_obj)

        self.assertEqual(result, "File not synced")

    @override_settings(MEDIA_URL="/storage-media/")
    def test_file_preview_with_synced_obj(self):
        # Not synced
        file_sync_obj = baker.make("sync.FileSync", file_name="747-8.jpg", synced_at=timezone.now())
        file_sync_admin = admin.FileSyncAdmin(FileSync, mock.Mock())

        result = file_sync_admin.file_preview(file_sync_obj)

        expected_file_url = "/storage-media/747-8.jpg"
        safe_html = safestring.mark_safe(
            f"""<a target="_blank" title="Click to open full image" href="{expected_file_url}">"""
            f"""<img width="600px" src="{expected_file_url}" />"""
            """</a>"""
        )
        self.assertEqual(result, safe_html)
