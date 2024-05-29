import logging
import os
import random
import requests

import boto3  # noqa
from botocore.client import Config  # noqa

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest

from app.sync.models import FileSync

logger = logging.getLogger(__name__)


def update_stats_cache() -> dict:
    """
    Update the cache with the synced objects stats from the database and returns the up-to-date value.
    """
    objects_stats = {
        "synced_objects_count": FileSync.objects.get_synced_objects_count(),
        "queued_objects_count": FileSync.objects.get_queued_objects_count(),
    }
    cache.set("synced_objects_stats", objects_stats, timeout=settings.STATS_CACHE_TIMEOUT)

    return objects_stats


def download_nasa_curiosity_image(file_name: str, file_path: str) -> str:
    """
    DISCLAIMER: This replaces the `download_fle_from_s3` function on this DEMO version of this project.
    Fetches a random image from NASA public API under MARS Curiosity Rover public library and stores it locally
    """
    # Sol = Martian day in which Curiosity took the photos listed in the endpoint response
    sol = random.randint(1, 999)

    nasa_endpoint_data = cache.get("nasa_endpoint_data")
    if not nasa_endpoint_data:
        response = requests.get(
            url=f"{settings.NASA_API_URL}/mars-photos/api/v1/rovers/curiosity/photos",
            params={
                "sol": sol,
                "api_key": settings.NASA_API_KEY,
            },
        )
        nasa_endpoint_data = response.json()["photos"]
        cache.set("nasa_endpoint_data", nasa_endpoint_data, timeout=settings.NASA_REQUEST_CACHE_TIMEOUT)

    available_photos = [photo["img_src"] for photo in nasa_endpoint_data]
    source_url = random.choice(available_photos)

    # Actually downloads the binary file into the storage
    stream_download_file_from_url(source_url, destination_path=file_path)

    return file_path


def stream_download_file_from_url(source_url: str, destination_path: str) -> None:
    """
    DISCLAIMER: This is also part of the demo, in the original implementation this was handled by AWS boto3 library
    Streams a file in chunks of 10Kb to avoid memory spikes in case of huge file download
    """
    chunk_size = 10_000
    with open(destination_path, "wb+") as file_handle:
        for chunk in requests.get(source_url, stream=True).iter_content(chunk_size=chunk_size, decode_unicode=True):
            file_handle.write(chunk)
            file_handle.flush()
            os.fsync(file_handle)


def download_fle_from_s3(file_name: str, file_path: str) -> None:  # noqa
    """
    DISCLAIMER: This used to be the function called by the `sync_s3_file_to_local_storage` task, but for the purposes of
    this DEMO it was disconnected from the task just so the we can run the project without actual AWS Credentials.
    Downloads the file from S3 and saves it on specified file_path.
    """
    aws_credentials = settings.AWS_CREDENTIALS
    s3 = boto3.resource(
        "s3",
        aws_access_key_id=aws_credentials["aws_access_key_id"],
        aws_secret_access_key=aws_credentials["aws_secret_access_key"],
        config=Config(signature_version="s3v4", region_name=aws_credentials["region_name"]),
    )
    s3.meta.client.download_file(aws_credentials["bucket_name"], file_name, file_path)


def get_request_key_rate_limit(_, request: HttpRequest) -> str:
    """
    Returns the key for the rate limit decorator based on the request.
    """
    return "{}-{}".format(request.headers.get("Authorization"), request.META.get("REMOTE_ADDR"))


def increase_queued_stats_cache() -> None:
    """
    Increase the queued objects count in the cache, if the cache exists.
    """
    objects_stats = cache.get("synced_objects_stats")
    if not objects_stats:
        return

    objects_stats["queued_objects_count"] += 1
    cache.set("synced_objects_stats", objects_stats)
