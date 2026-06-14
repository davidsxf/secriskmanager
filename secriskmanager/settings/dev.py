from .base import *  # noqa: F401, F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

INSTALLED_APPS += [
    "django_extensions",
    "debug_toolbar",
]

MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

INTERNAL_IPS = ["127.0.0.1"]

from debug_toolbar.settings import CONFIG_DEFAULTS

# 继承默认禁用面板 + 额外禁用静态文件面板
_extra_disabled = {
    "debug_toolbar.panels.staticfiles.StaticFilesPanel",
}
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": CONFIG_DEFAULTS["DISABLE_PANELS"] | _extra_disabled,
}

LOGGING = {
    "version": 1,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "DEBUG"},
}
