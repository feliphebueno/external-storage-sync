from unittest import mock

import dramatiq
from model_bakery import baker

from requests.exceptions import ConnectTimeout

from django.test import override_settings, TestCase

from app.sync import tasks


@override_settings(STORAGE_PATH="/tmp/storage")
class SyncS3FileToLocalStorageTest(TestCase):
    def setUp(self) -> None:
        self.queued_object = baker.make("sync.FileSync", synced_at=None)

    @mock.patch("app.sync.tasks.dramatiq.middleware.CurrentMessage.get_current_message")
    @mock.patch("app.sync.tasks.random")
    @mock.patch("app.sync.tasks.logger")
    @mock.patch("app.sync.tasks.utils")
    def test_sync_s3_file_to_local_storage_fail_retry_with_backoff(
        self, p_utils, p_logger, p_random, p_get_current_message
    ):
        p_random.randint.return_value = 45_458
        p_get_current_message.return_value.options = {"retries": 0}
        p_utils.download_nasa_curiosity_image.side_effect = ConnectTimeout("ConnectionTimeout")

        with self.assertRaises(dramatiq.errors.Retry) as retry_exception:
            tasks.sync_s3_file_to_local_storage(self.queued_object.id, "707-100.jpg")

        self.queued_object.refresh_from_db()
        p_utils.download_nasa_curiosity_image.assert_called_once_with("707-100.jpg", "/tmp/storage/707-100.jpg")
        p_logger.exception.assert_called_once_with(
            "HTTP Error downloading file: ConnectionTimeout",
            extra={
                "file_sync_id": self.queued_object.id,
                "file_name": "707-100.jpg",
            },
        )
        p_random.randint.assert_called_once_with(3_000, 60_000)

        self.assertEqual(retry_exception.exception.delay, 45_458)
        self.assertIsNone(self.queued_object.synced_at)

    @mock.patch("app.sync.tasks.Path")
    @mock.patch("app.sync.tasks.utils")
    def test_sync_s3_file_to_local_storage_fail_missing_file(self, p_utils, p_path):
        p_utils.download_nasa_curiosity_image.return_value = "/tmp/storage/707-100.jpg"
        p_path.return_value.exists.return_value = False

        with self.assertRaises(IOError) as io_error:
            tasks.sync_s3_file_to_local_storage(self.queued_object.id, "707-100.jpg")

        self.queued_object.refresh_from_db()
        p_utils.download_nasa_curiosity_image.assert_called_once_with("707-100.jpg", "/tmp/storage/707-100.jpg")
        self.assertEqual(str(io_error.exception), "File not stored in local storage")
        self.assertIsNone(self.queued_object.synced_at)

    @mock.patch("app.sync.tasks.Path")
    @mock.patch("app.sync.tasks.utils")
    def test_sync_s3_file_to_local_storage_done(self, p_utils, p_path):
        p_utils.download_nasa_curiosity_image.return_value = "/tmp/storage/707-100.jpg"
        p_path.return_value.exists.return_value = True

        tasks.sync_s3_file_to_local_storage(self.queued_object.id, "707-100.jpg")

        self.queued_object.refresh_from_db()
        p_utils.download_nasa_curiosity_image.assert_called_once_with("707-100.jpg", "/tmp/storage/707-100.jpg")
        self.assertEqual(self.queued_object.file_path, "/tmp/storage/707-100.jpg")
        self.assertIsNotNone(self.queued_object.synced_at)
