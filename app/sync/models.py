from django.db import models


class FileSyncQuerySet(models.QuerySet):
    def get_synced_objects_count(self):
        return self.filter(synced_at__isnull=False).only("id").count()

    def get_queued_objects_count(self):
        return self.filter(synced_at__isnull=True).only("id").count()

    def exists_synced_file(self, payload_checksum: str) -> bool:
        return self.filter(payload_checksum=payload_checksum).exists()

    def create_new_file_sync(
        self, oeid: str, file_name: str, payload_checksum: str, ref_id: str, file_type: str
    ) -> "FileSync":
        return self.create(
            oeid=oeid,
            file_name=file_name,
            payload_checksum=payload_checksum,
            ref_id=ref_id,
            file_type=file_type,
        )


class FileSync(models.Model):
    oeid = models.CharField(max_length=30, db_index=True)
    file_name = models.CharField(max_length=35, db_index=True)
    payload_checksum = models.CharField(max_length=255, db_index=True)
    file_path = models.CharField(max_length=255, null=True, default=None)
    ref_id = models.CharField(max_length=30, db_index=True)
    file_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    synced_at = models.DateTimeField(null=True, default=None)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Synced files"

    def __str__(self):
        return self.file_name

    objects = FileSyncQuerySet().as_manager()
