from django.test import TestCase

from app.sync.models import FileSync


class FileSyncTest(TestCase):
    def test_file_sync_model(self):
        new_file_sync = FileSync.objects.create(
            oeid="mocked",
            file_name="A350-XWB.jpg",
            payload_checksum="mock",
            file_path="/tmp/A350-XWB.jpg",
            ref_id="mock",
            file_type="image/jpg",
        )

        self.assertGreaterEqual(new_file_sync.id, 1)
        self.assertEqual(str(new_file_sync), "A350-XWB.jpg")
