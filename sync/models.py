from django.db import models


class SourceFeed(models.Model):
    """威胁情报源注册表"""

    class Meta:
        verbose_name = "情报源"
        verbose_name_plural = "情报源"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["last_sync_at"]),
        ]

    FEED_TYPE_CHOICES = [
        ("ip", "IP"),
        ("domain", "域名"),
        ("mixed", "混合"),
    ]
    AUTH_TYPE_CHOICES = [
        ("none", "无需认证"),
        ("api_key", "API Key"),
        ("header", "自定义 Header"),
    ]
    FORMAT_CHOICES = [
        ("text", "纯文本"),
        ("csv", "CSV"),
        ("json", "JSON"),
        ("misp", "MISP"),
    ]

    name = models.CharField(verbose_name="名称", max_length=64)
    slug = models.SlugField(verbose_name="标识", max_length=64, unique=True)
    feed_type = models.CharField(
        verbose_name="数据类型", max_length=16, choices=FEED_TYPE_CHOICES
    )
    url = models.URLField(verbose_name="下载地址", max_length=500)
    format = models.CharField(
        verbose_name="数据格式", max_length=32, choices=FORMAT_CHOICES, default="text"
    )
    auth_type = models.CharField(
        verbose_name="认证方式", max_length=16,
        choices=AUTH_TYPE_CHOICES, default="none"
    )
    auth_key = models.CharField(
        verbose_name="API Key", max_length=256, blank=True, default=""
    )
    auth_header_template = models.CharField(
        verbose_name="Header 模板", max_length=256, blank=True, default=""
    )
    is_active = models.BooleanField(verbose_name="启用", default=True)
    interval_minutes = models.IntegerField(
        verbose_name="同步间隔(分钟)", default=1440
    )
    retry_count = models.IntegerField(verbose_name="重试次数", default=3)
    timeout_seconds = models.IntegerField(verbose_name="超时(秒)", default=30)
    confidence_base = models.IntegerField(verbose_name="基础置信度", default=50)
    category_default = models.CharField(
        verbose_name="默认分类", max_length=64, blank=True, default=""
    )
    filter_private = models.BooleanField(verbose_name="过滤私有地址", default=True)
    description = models.TextField(verbose_name="说明", blank=True, default="")
    last_sync_at = models.DateTimeField(
        verbose_name="最后同步时间", blank=True, null=True
    )
    last_sync_status = models.CharField(
        verbose_name="最后同步状态", max_length=16,
        choices=[
            ("never", "未同步"),
            ("success", "成功"),
            ("failed", "失败"),
            ("partial", "部分成功"),
        ],
        default="never",
    )
    last_sync_count = models.IntegerField(verbose_name="上次同步数", default=0)
    total_sync_count = models.IntegerField(verbose_name="累计同步数", default=0)
    consecutive_failures = models.IntegerField(verbose_name="连续失败", default=0)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    def __str__(self):
        return self.name


class SourceRecord(models.Model):
    """同步记录"""

    class Meta:
        verbose_name = "同步记录"
        verbose_name_plural = "同步记录"
        indexes = [
            models.Index(fields=["source"]),
            models.Index(fields=["started_at"]),
        ]

    source = models.ForeignKey(
        SourceFeed, on_delete=models.CASCADE, verbose_name="情报源"
    )
    sync_type = models.CharField(
        verbose_name="同步类型", max_length=32,
        choices=[("ip", "IP"), ("domain", "域名")]
    )
    total_count = models.IntegerField(verbose_name="总数", default=0)
    new_count = models.IntegerField(verbose_name="新增", default=0)
    status = models.CharField(
        verbose_name="状态", max_length=16,
        choices=[
            ("success", "成功"),
            ("failed", "失败"),
            ("partial", "部分成功"),
        ]
    )
    message = models.TextField(verbose_name="消息", blank=True, default="")
    started_at = models.DateTimeField(verbose_name="开始时间", auto_now_add=True)
    finished_at = models.DateTimeField(verbose_name="结束时间", blank=True, null=True)

    def __str__(self):
        return f"{self.source.name} @ {self.started_at}"


class TaskProgress(models.Model):
    """异步任务进度跟踪"""

    class Meta:
        verbose_name = "任务进度"
        verbose_name_plural = "任务进度"

    STATUS_CHOICES = [
        ("pending", "等待中"),
        ("running", "运行中"),
        ("completed", "已完成"),
        ("failed", "失败"),
        ("cancelled", "已取消"),
    ]

    task_type = models.CharField(verbose_name="任务类型", max_length=64)
    status = models.CharField(
        verbose_name="状态", max_length=16, choices=STATUS_CHOICES, default="pending"
    )
    progress = models.IntegerField(verbose_name="进度", default=0)
    total = models.IntegerField(verbose_name="总数", default=0)
    current_item = models.CharField(verbose_name="当前条目", max_length=255, blank=True, default="")
    message = models.TextField(verbose_name="消息", blank=True, default="")
    cancel_flag = models.BooleanField(verbose_name="取消标志", default=False)
    result = models.JSONField(verbose_name="结果摘要", blank=True, null=True, default=dict)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)

    def __str__(self):
        return f"{self.task_type} [{self.status}] {self.progress}/{self.total}"

    def cancel(self):
        self.cancel_flag = True
        self.save(update_fields=["cancel_flag"])
