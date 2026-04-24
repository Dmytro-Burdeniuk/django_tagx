from django.conf import settings
from django.http import HttpRequest


def show_toolbar(request: HttpRequest) -> bool:
    return bool(settings.DEBUG)