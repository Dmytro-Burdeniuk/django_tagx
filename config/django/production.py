from config.env import env

from .base import *  # noqa F403

DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])  # type: ignore[arg-type]
