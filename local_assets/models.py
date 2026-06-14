from django.db import models


class LocalAsset(models.Model):
    """本地局域网资产"""

    class Meta:
        verbose_name = "本地资产"
        verbose_name_plural = "本地资产"
        indexes = [
            models.Index(fields=["ip_address"]),
            models.Index(fields=["person_name"]),
            models.Index(fields=["department"]),
            models.Index(fields=["mac_address"]),
        ]

    DEVICE_TYPE_CHOICES = [
        ("computer", "电脑"),
        ("printer", "打印机"),
        ("router", "路由器"),
        ("server", "服务器"),
        ("other", "其他"),
    ]

    ip_address = models.GenericIPAddressField(
        verbose_name="IP 地址", unique=True
    )
    mac_address = models.CharField(
        verbose_name="MAC 地址", max_length=17, blank=True, default="",
        help_text="格式: xx:xx:xx:xx:xx:xx"
    )
    hostname = models.CharField(
        verbose_name="主机名", max_length=128, blank=True, default=""
    )
    person_name = models.CharField(
        verbose_name="姓名", max_length=64, blank=True, default=""
    )
    department = models.CharField(
        verbose_name="部门", max_length=128, blank=True, default=""
    )
    device_type = models.CharField(
        verbose_name="设备类型", max_length=32,
        choices=DEVICE_TYPE_CHOICES, default="computer"
    )
    remark = models.TextField(verbose_name="备注", blank=True, default="")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    def __str__(self):
        name = self.person_name or self.hostname or str(self.ip_address)
        return f"{self.ip_address} - {name}"
