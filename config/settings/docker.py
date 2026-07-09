from .production import *  # noqa: F403

# TLS terminates at nginx; Gunicorn serves HTTP only
SECURE_SSL_REDIRECT = False
