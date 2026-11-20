"""IP клієнта для лімітів. Nginx підставляє X-Real-IP з $remote_addr."""


def client_ip(request) -> str:
    forwarded = (request.META.get('HTTP_X_REAL_IP') or '').split(',')[0].strip()
    if forwarded:
        return forwarded
    return (request.META.get('REMOTE_ADDR') or '0.0.0.0').strip() or '0.0.0.0'
