from django.db import models


class MaliciousDomain(models.Model):
    """恶意域名"""

    class Meta:
        verbose_name = "恶意域名"
        verbose_name_plural = "恶意域名"
        indexes = [
            models.Index(fields=["domain"]),
            models.Index(fields=["source"]),
            models.Index(fields=["is_active"]),
        ]

    domain = models.CharField(
        verbose_name="域名", max_length=255, unique=True, db_index=True
    )
    prefix_at = models.BooleanField(
        verbose_name="@ 前缀", default=False,
        help_text="是否带 @ 前缀（匹配子域名）"
    )
    source = models.CharField(
        verbose_name="来源", max_length=64, default="manual", db_index=True
    )
    category = models.CharField(
        verbose_name="分类", max_length=64, blank=True, default=""
    )
    is_active = models.BooleanField(verbose_name="是否活跃", default=True)
    remark = models.TextField(verbose_name="备注", blank=True, default="")
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    def __str__(self):
        prefix = "@" if self.prefix_at else ""
        return f"{prefix}{self.domain}"
