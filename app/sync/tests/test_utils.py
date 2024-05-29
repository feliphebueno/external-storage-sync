import tempfile
from unittest import mock

from django.test import override_settings, RequestFactory, TestCase


import requests_mock

from app.sync import utils


@override_settings(NASA_API_URL="mock://api.nasa.gov", NASA_API_KEY="mock-api-key", NASA_REQUEST_CACHE_TIMEOUT=3_000)
class DownloadNasaCuriosityImageTest(TestCase):
    @mock.patch("app.sync.utils.stream_download_file_from_url")
    @mock.patch("app.sync.utils.cache")
    @mock.patch("app.sync.utils.requests")
    def test_download_nasa_curiosity_image_with_cache_entries(
        self, p_requests, p_cache, p_stream_download_file_from_url
    ):
        p_cache.get.return_value = [{"img_src": "mock://api.nasa.gov/A330-neo.jpg"}]

        utils.download_nasa_curiosity_image(file_name="mock.jpg", file_path="/tmp/mock.jpg")

        p_requests.get.assert_not_called()
        p_cache.set.assert_not_called()
        p_stream_download_file_from_url.assert_called_once_with(
            "mock://api.nasa.gov/A330-neo.jpg", destination_path="/tmp/mock.jpg"
        )

    @mock.patch("app.sync.utils.stream_download_file_from_url")
    @mock.patch("app.sync.utils.cache")
    def test_download_nasa_curiosity_image(self, p_cache, p_stream_download_file_from_url):
        expected_url = "mock://api.nasa.gov/mars-photos/api/v1/rovers/curiosity/photos"
        mocked_response = {"photos": [{"img_src": "mock://api.nasa.gov/A330-900.jpg"}]}
        p_cache.get.return_value = None
        with requests_mock.Mocker() as mock_request:
            mock_request.get(expected_url, json=mocked_response)
            utils.download_nasa_curiosity_image(file_name="mock.jpg", file_path="/tmp/mock.jpg")

        p_cache.set.assert_called_once_with("nasa_endpoint_data", mocked_response["photos"], timeout=3_000)
        p_stream_download_file_from_url.assert_called_once_with(
            "mock://api.nasa.gov/A330-900.jpg", destination_path="/tmp/mock.jpg"
        )


class StreamDownloadFileFromUrl(TestCase):
    def test_stream_download_file_from_url(self):
        expected_url = "mock://api.nasa.gov/777-300ER.jpg"
        mocked_file_content = b"x" * 30_000

        with tempfile.TemporaryDirectory() as tmp_dir:
            destination_path = f"{tmp_dir}/777-300ER.jpg"

            with requests_mock.Mocker() as mock_request:
                mock_request.get(expected_url, content=mocked_file_content)
                utils.stream_download_file_from_url(source_url=expected_url, destination_path=destination_path)

            written_file_content = open(destination_path, "rb").read()

        self.assertEqual(written_file_content, mocked_file_content)


@override_settings(
    AWS_CREDENTIALS={
        "aws_access_key_id": "key_id",
        "aws_secret_access_key": "access_key",
        "region_name": "us-east-2",
        "bucket_name": "s3_bucket",
    }
)
class DownloadFileFromS3Test(TestCase):
    @mock.patch("app.sync.utils.Config")
    @mock.patch("app.sync.utils.boto3")
    def test_download_fle_from_s3(self, p_boto3, p_config):
        s3_service_mock = mock.Mock()
        p_boto3.resource.return_value = s3_service_mock

        utils.download_fle_from_s3(file_name="mock.jpg", file_path="/tmp/mock.jpg")

        p_boto3.resource.assert_called_once_with(
            "s3",
            aws_access_key_id="key_id",
            aws_secret_access_key="access_key",
            config=p_config.return_value,
        )
        p_config.assert_called_once_with(signature_version="s3v4", region_name="us-east-2")
        s3_service_mock.meta.client.download_file.assert_called_once_with("s3_bucket", "mock.jpg", "/tmp/mock.jpg")


class GetRequestKeyRateLimitTest(TestCase):
    def test_get_request_key_rate_limit(self):
        request = RequestFactory().post("/sync/", headers={"Authorization": "XYZ", "REMOTE_ADDR": "127.0.0.1"})

        key_name = utils.get_request_key_rate_limit(mock.Mock(), request)

        self.assertEqual(key_name, "XYZ-127.0.0.1")


class IncreaseQueuedStatsCacheTest(TestCase):
    @mock.patch("app.sync.utils.cache")
    def test_increase_queued_stats_cache_no_cache_entries(self, p_cache):
        p_cache.get.return_value = None

        utils.increase_queued_stats_cache()

        p_cache.set.assert_not_called()

    @mock.patch("app.sync.utils.cache")
    def test_increase_queued_stats_cache(self, p_cache):
        p_cache.get.return_value = {"queued_objects_count": 0, "synced_objects_stats": 100}

        utils.increase_queued_stats_cache()

        p_cache.set.assert_called_once_with(
            "synced_objects_stats",
            {"queued_objects_count": 1, "synced_objects_stats": 100},
        )
