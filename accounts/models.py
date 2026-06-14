from django.db import models
import ipaddress


class AllowedIP(models.Model):
    """允许访问系统的 IP 段白名单"""

    class Meta:
        verbose_name = "允许访问的 IP 段"
        verbose_name_plural = "允许访问的 IP 段"
        ordering = ["cidr"]

    cidr = models.CharField(
        verbose_name="IP 段（CIDR）", max_length=43, unique=True,
        help_text="例如 172.21.40.0/24 或 192.168.1.0/24"
    )
    description = models.CharField(
        verbose_name="说明", max_length=255, blank=True, default=""
    )
    is_active = models.BooleanField(verbose_name="启用", default=True)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    def clean(self):
        try:
            ipaddress.ip_network(self.cidr, strict=False)
        except ValueError:
            from django.core.exceptions import ValidationError
            raise ValidationError({"cidr": f"无效的 CIDR 格式: {self.cidr}"})

    def save(self, *args, **kwargs):
        self.clean()
        # 标准化 CIDR 格式
        net = ipaddress.ip_network(self.cidr, strict=False)
        self.cidr = str(net)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.cidr

    def contains(self, ip_str: str) -> bool:
        """检查 IP 是否在此段内"""
        try:
            ip = ipaddress.ip_address(ip_str)
            return ip in ipaddress.ip_network(self.cidr, strict=False)
        except ValueError:
            return False
