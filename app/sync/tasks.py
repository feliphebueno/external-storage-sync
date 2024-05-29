import logging
import random
from pathlib import Path

import dramatiq
from requests.exceptions import RequestException

from django.conf import settings
from django.utils import timezone

from app.sync import utils
from app.sync.models import FileSync

logger = logging.getLogger(__name__)


@dramatiq.actor(time_limit=settings.SYNC_S3_TASK_TIME_LIMIT, max_retries=3)
def sync_s3_file_to_local_storage(file_sync_id: int, file_name: str):
    """
    Downloads the file from S3, saves it on local storage and update the FileSync object and cache.
    """
    file_path = f"{settings.STORAGE_PATH}/{file_name}"

    try:
        utils.download_nasa_curiosity_image(file_name, file_path)
    except RequestException as exception:
        logger.exception(
            f"HTTP Error downloading file: {exception}",
            extra={
                "file_sync_id": file_sync_id,
                "file_name": file_name,
            },
        )

        # Message data
        message = dramatiq.middleware.CurrentMessage.get_current_message()
        retries_so_far = message.options.get("retries", 0) or 1

        # Simulation of an exponential backoff retry policy for failed tasks to prevent retries spike/race conditions
        min_back_off = 3_000 * retries_so_far
        max_back_off = 60_000 * retries_so_far

        raise dramatiq.errors.Retry(str(exception), delay=random.randint(min_back_off, max_back_off))

    # In case of unhandled IO error we fail the task so it can be recovered later
    if not Path(file_path).exists():
        raise IOError("File not stored in local storage")

    # Maks this file as synced into the local storage
    file_sync = FileSync.objects.get(id=file_sync_id)
    file_sync.file_path = file_path
    file_sync.synced_at = timezone.now()
    file_sync.save(update_fields=["file_path", "synced_at"])

    # Update cache
    utils.update_stats_cache()
