from django.db import models
from django.utils.text import slugify


class SourcePreset(models.Model):
    """IP/域名 来源预设"""

    class Meta:
        verbose_name = "来源预设"
        verbose_name_plural = "来源预设"
        ordering = ["name"]

    name = models.CharField(verbose_name="名称", max_length=64, unique=True)
    slug = models.SlugField(verbose_name="标识", max_length=64, unique=True, blank=True)
    is_manual = models.BooleanField(verbose_name="手动来源", default=False,
                                    help_text="手动输入 vs 自动同步")
    description = models.CharField(verbose_name="说明", max_length=255, blank=True, default="")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    """标签"""

    class Meta:
        verbose_name = "标签"
        verbose_name_plural = "标签"

    name = models.CharField(verbose_name="名称", max_length=64, unique=True)
    slug = models.SlugField(verbose_name="标识", max_length=64, unique=True, blank=True)
    color = models.CharField(verbose_name="颜色", max_length=7, default="#3B82F6")
    description = models.CharField(verbose_name="说明", max_length=255, blank=True, default="")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class MaliciousIP(models.Model):
    """恶意 IP 地址"""

    class Meta:
        verbose_name = "恶意 IP"
        verbose_name_plural = "恶意 IP"
        indexes = [
            models.Index(fields=["ip_address"]),
            models.Index(fields=["source"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_at"]),
        ]

    ip_address = models.GenericIPAddressField(
        verbose_name="IP 地址", blank=True, null=True, unique=True
    )
    cidr = models.CharField(
        verbose_name="CIDR", max_length=43, blank=True, null=True, unique=True
    )
    range_start = models.GenericIPAddressField(
        verbose_name="范围起始", blank=True, null=True
    )
    range_end = models.GenericIPAddressField(
        verbose_name="范围结束", blank=True, null=True
    )
    source = models.CharField(
        verbose_name="来源", max_length=64, default="manual", db_index=True
    )
    category = models.CharField(
        verbose_name="分类", max_length=64, blank=True, default=""
    )
    confidence = models.IntegerField(verbose_name="置信度", default=0)
    is_active = models.BooleanField(verbose_name="是否活跃", default=True)
    remark = models.TextField(verbose_name="备注", blank=True, default="")
    tags = models.ManyToManyField(Tag, verbose_name="标签", blank=True)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    def __str__(self):
        if self.ip_address:
            return str(self.ip_address)
        if self.cidr:
            return self.cidr
        if self.range_start and self.range_end:
            return f"{self.range_start}-{self.range_end}"
        return f"MaliciousIP #{self.pk}"
