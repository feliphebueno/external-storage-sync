import hmac
import json
from unittest import mock

from model_bakery import baker

from django.utils import timezone
from django.test import override_settings, RequestFactory, TestCase


from app.sync.models import FileSync
from app.sync.views import rate_limited_error_view


@override_settings(SECRET_KEY="mock-test-secret-key")
class SyncViewTest(TestCase):
    def setUp(self):
        self.base_request_body = {
            "oeid": "mock",
            "ref_id": "mock",
            "file_name": "mock",
            "file_type": "image/jpeg",
        }

    @mock.patch("app.sync.views.cache")
    def test_get_synced_objects_no_cache_entries(self, p_cache):
        # Synced
        baker.make("sync.FileSync", synced_at=timezone.now())

        # Not synced
        baker.make("sync.FileSync", synced_at=None)

        p_cache.get.return_value = None

        response = self.client.get("/sync/")

        p_cache.get.assert_called_once_with("synced_objects_stats")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"synced_objects_count": 1, "queued_objects_count": 1})
        # self.assertEqual(len(connection.queries), 2)

    @mock.patch("app.sync.views.update_stats_cache")
    @mock.patch("app.sync.views.cache")
    def test_get_synced_objects_with_cache_entries(self, p_cache, p_update_stats_cache):
        p_cache.get.return_value = {
            "synced_objects_count": 1_000,
            "queued_objects_count": 10,
        }

        response = self.client.get("/sync/")

        p_update_stats_cache.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"synced_objects_count": 1_000, "queued_objects_count": 10})

    @mock.patch("app.sync.views.increase_queued_stats_cache")
    def test_post_sync_object_already_exists(self, p_increase_queued_stats_cache):
        request_body_json = json.dumps(self.base_request_body)
        existing_checksum = self.calculate_body_real_hmac(request_body_json.encode())

        # Existing object in the DB
        baker.make("sync.FileSync", payload_checksum=existing_checksum)

        response = self.client.post(
            "/sync/",
            data=self.base_request_body,
            content_type="application/json",
            headers={"Authorization": existing_checksum},
        )

        p_increase_queued_stats_cache.assert_not_called()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {"detail": "Object already exists"})

    @mock.patch("app.sync.views.increase_queued_stats_cache")
    @mock.patch("app.sync.views.sync_s3_file_to_local_storage")
    def test_post_sync_object(self, p_sync_s3_file_to_local_storage, p_increase_queued_stats_cache):
        self.base_request_body["file_name"] = "747-400.jpg"
        request_body_json = json.dumps(self.base_request_body)
        existing_checksum = self.calculate_body_real_hmac(request_body_json.encode())

        response = self.client.post(
            "/sync/",
            data=self.base_request_body,
            content_type="application/json",
            headers={"Authorization": existing_checksum},
        )

        queued_object = FileSync.objects.get(file_name="747-400.jpg")

        p_sync_s3_file_to_local_storage.send.assert_called_once_with(queued_object.id, file_name="747-400.jpg")
        p_increase_queued_stats_cache.assert_called_once_with()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"detail": "Object queued for sync"})

    @staticmethod
    def calculate_body_real_hmac(request_body: bytes):
        return hmac.new(
            key=bytes("mock-test-secret-key", "utf-8"),
            msg=request_body,
            digestmod="sha256",
        ).hexdigest()


class RateLimitedErrorViewTest(TestCase):
    def test_rate_limited_error_view(self):
        request = RequestFactory().get("/sync/")

        response = rate_limited_error_view(request, mock.Mock())

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.content, b"""{"error": "Too many requests"}""")
