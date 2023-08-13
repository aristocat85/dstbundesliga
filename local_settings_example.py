DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "mydatabase",
    }
}

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

X_FRAME_OPTIONS = "ALLOWALL"
XS_SHARING_ALLOWED_METHODS = ["POST", "GET", "OPTIONS", "PUT", "DELETE"]

DEBUG = True
