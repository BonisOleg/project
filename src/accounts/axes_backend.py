"""Axes не ламає authenticate() без request (тестовий клієнт, команди)."""

from axes.backends import AxesStandaloneBackend


class OyraAxesBackend(AxesStandaloneBackend):
    def authenticate(self, request=None, username=None, password=None, **kwargs):
        if request is None:
            return None
        return super().authenticate(
            request, username=username, password=password, **kwargs,
        )
