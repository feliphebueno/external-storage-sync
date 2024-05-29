from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

from .views import django_status
from app.sync.views import SyncView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sync/", SyncView.as_view(), name="sync"),
    path("status.html", django_status, name="django_status"),
]

# Django toolbar settings
if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static("/files/", document_root=settings.MEDIA_ROOT)

    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar  # noqa

        urlpatterns += [
            path("__debug__/", include(debug_toolbar.urls)),
        ]
