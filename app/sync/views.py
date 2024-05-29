from django.http.response import HttpResponse as HttpResponse
from django_ratelimit.decorators import ratelimit

from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from app.sync.models import FileSync
from app.sync.tasks import sync_s3_file_to_local_storage
from app.sync.utils import increase_queued_stats_cache, get_request_key_rate_limit, update_stats_cache


class SyncView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return super().dispatch(request, *args, **kwargs)

    @method_decorator(ratelimit(key="ip", rate="50/m", method="GET", block=False))
    def get(self, request: HttpRequest):
        objects_stats = cache.get("synced_objects_stats")
        if not objects_stats:
            objects_stats = update_stats_cache()

        return JsonResponse(objects_stats)

    @method_decorator(ratelimit(key=get_request_key_rate_limit, rate="50/m", method="POST", block=False))
    def post(self, request: HttpRequest):
        payload_checksum = request.headers.get("Authorization")

        if FileSync.objects.exists_synced_file(payload_checksum):
            return JsonResponse({"detail": "Object already exists"}, status=409)

        request_data = request.POST
        file_sync = FileSync.objects.create_new_file_sync(
            oeid=request_data["oeid"],
            file_name=request_data["file_name"],
            ref_id=request_data["ref_id"],
            file_type=request_data["file_type"],
            payload_checksum=payload_checksum,
        )

        # Enqueues the file download task
        sync_s3_file_to_local_storage.send(file_sync.id, file_name=file_sync.file_name)

        # Updates the cache
        increase_queued_stats_cache()

        return JsonResponse({"detail": "Object queued for sync"}, status=201)


def rate_limited_error_view(request, _) -> JsonResponse:
    """
    Return a specific JSON response when the rate limit is exceeded.
    """
    return JsonResponse({"error": "Too many requests"}, status=429)
