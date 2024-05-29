from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.http import HttpResponse

UserModel = get_user_model()


def django_status(request):
    UserModel.objects.exists()

    cache.set("django_status", "value", timeout=5)
    cache.get("django_status")

    return HttpResponse()
