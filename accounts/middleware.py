"""IP 白名单访问控制中间件"""
from django.conf import settings
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin


class IPWhitelistMiddleware(MiddlewareMixin):
    """检查请求 IP 是否在白名单中"""

    def process_request(self, request):
        # 仅在配置了白名单时启用
        from .models import AllowedIP
        allowed = AllowedIP.objects.filter(is_active=True)
        if not allowed.exists():
            return  # 没有白名单配置，允许所有 IP

        # 获取客户端 IP
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            ip = xff.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "")

        # 检查是否在白名单中
        for entry in allowed:
            if entry.contains(ip):
                return

        # 记录并拒绝
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"被 IP 白名单拒绝的请求: {ip} -> {request.path}")
        return HttpResponseForbidden(f"<h1>403 Forbidden</h1><p>您的 IP ({ip}) 不在系统允许的访问范围内。</p>")
