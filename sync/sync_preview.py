"""威胁情报源同步：异步下载 → 预览比对 → 确认导入"""
import json
import threading
import requests
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView, View

from .models import SourceFeed, TaskProgress
from risk_ip.models import MaliciousIP, SourcePreset, Tag
from risk_ip.parsers import parse_conf_file as parse_ip_file
from risk_domain.models import MaliciousDomain
from risk_domain.parsers import parse_txt_file


def _download_feed(feed):
    """下载情报源数据，返回 (content_text, error_str)"""
    headers = {"User-Agent": "SecRiskManager/1.0"}
    if feed.auth_type == "api_key":
        url = feed.url.replace("{key}", feed.auth_key)
        headers["Authorization"] = f"Bearer {feed.auth_key}"
    elif feed.auth_type == "header":
        url = feed.url
        template = feed.auth_header_template
        if "{key}" in template:
            headers["Authorization"] = template.replace("{key}", feed.auth_key)
    else:
        url = feed.url
    try:
        resp = requests.get(url, headers=headers, timeout=feed.timeout_seconds or 60)
        resp.raise_for_status()
        return resp.content.decode("utf-8", errors="replace"), None
    except requests.exceptions.RequestException as e:
        return None, str(e)


def _run_sync_preview(task_id, feed_id):
    """后台线程：下载 → 解析 → 比对 → 保存结果"""
    feed = SourceFeed.objects.get(pk=feed_id)
    task = TaskProgress.objects.get(pk=task_id)
    task.status = "running"
    task.save(update_fields=["status"])

    # 1. 下载
    task.message = "正在下载..."
    task.save(update_fields=["message"])
    content, error = _download_feed(feed)
    if error:
        task.status = "failed"
        task.message = f"下载失败: {error}"
        task.save(update_fields=["status", "message"])
        feed.last_sync_status = "failed"
        feed.consecutive_failures += 1
        if feed.consecutive_failures >= 3:
            feed.is_active = False
        feed.save(update_fields=["last_sync_status", "consecutive_failures", "is_active"])
        return

    if not content or not content.strip():
        task.status = "failed"
        task.message = "下载内容为空"
        task.save(update_fields=["status", "message"])
        return

    # 2. 解析
    task.message = "正在解析数据..."
    task.total = 0
    task.save(update_fields=["message", "total"])
    entries = _parse_feed_content(feed, content)
    task.total = len(entries)
    task.save(update_fields=["total"])

    # 3. 比对
    task.message = f"正在比对系统库（共 {len(entries)} 条）..."
    task.save(update_fields=["message"])

    if feed.feed_type in ("ip", "mixed"):
        existing_ips = set(
            MaliciousIP.objects.filter(ip_address__isnull=False)
            .values_list("ip_address", flat=True)
        )
        existing_cidrs = set(
            MaliciousIP.objects.filter(cidr__isnull=False)
            .values_list("cidr", flat=True)
        )
        existing_ranges = set(
            MaliciousIP.objects.filter(range_start__isnull=False)
            .values_list("range_start", "range_end")
        )
        new_items = []
        for i, e in enumerate(entries):
            if TaskProgress.objects.get(pk=task_id).cancel_flag:
                task.status = "cancelled"
                task.save(update_fields=["status"])
                return
            exists = False
            if e["type"] == "single":
                exists = e["ip"] in existing_ips
            elif e["type"] == "cidr":
                exists = e["cidr"] in existing_cidrs
            elif e["type"] == "range":
                exists = (e["range_start"], e["range_end"]) in existing_ranges
            if not exists:
                val = e.get("ip") or e.get("cidr") or f"{e.get('range_start')}-{e.get('range_end')}"
                new_items.append({"type": e["type"], "value": val})
            task.progress = i + 1
            if i % 1000 == 0:
                task.save(update_fields=["progress"])

    elif feed.feed_type == "domain":
        existing_domains = set(MaliciousDomain.objects.values_list("domain", flat=True))
        new_items = []
        for i, e in enumerate(entries):
            if e["domain"] not in existing_domains:
                new_items.append({"type": "domain", "value": e["domain"]})
            task.progress = i + 1
            if i % 1000 == 0:
                task.save(update_fields=["progress"])

    task.progress = task.total
    task.status = "completed"
    task.message = f"比对完成：文件 {task.total} 条，库中已有 {task.total - len(new_items)} 条，待新增 {len(new_items)} 条"
    task.result = {
        "total": task.total,
        "exists": task.total - len(new_items),
        "new_count": len(new_items),
        "new_items": new_items[:5000],  # 最多保留 5000 条预览
        "feed_id": feed.pk,
        "feed_name": feed.name,
        "source_slug": feed.slug,
    }
    task.save(update_fields=["status", "message", "progress", "result"])

    # 更新 feed 状态
    feed.last_sync_status = "success"
    feed.consecutive_failures = 0
    feed.save(update_fields=["last_sync_status", "consecutive_failures"])


def _parse_feed_content(feed, content):
    if feed.feed_type in ("ip", "mixed"):
        return parse_ip_file(content)
    elif feed.feed_type == "domain":
        return parse_txt_file(content)
    return []


class FeedSyncPreviewView(LoginRequiredMixin, View):
    """启动异步同步"""

    def post(self, request, pk):
        feed = get_object_or_404(SourceFeed, pk=pk)
        task = TaskProgress.objects.create(
            task_type=f"sync_{feed.feed_type}",
            status="pending",
            message="准备中...",
        )
        t = threading.Thread(
            target=_run_sync_preview,
            args=(task.pk, feed.pk),
            daemon=True,
        )
        t.start()
        return redirect("sync:sync_progress", task_id=task.pk)


class FeedSyncProgressView(LoginRequiredMixin, TemplateView):
    """异步同步进度页面"""
    template_name = "sync/sync_progress.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["task"] = get_object_or_404(TaskProgress, pk=self.kwargs["task_id"])
        ctx["source_choices"] = SourcePreset.objects.all().order_by("name")
        ctx["tag_choices"] = Tag.objects.all().order_by("name")
        return ctx


class FeedSyncResultView(LoginRequiredMixin, View):
    """获取同步结果（JSON）"""

    def get(self, request, task_id):
        task = get_object_or_404(TaskProgress, pk=task_id)
        return JsonResponse({
            "status": task.status,
            "progress": task.progress,
            "total": task.total,
            "message": task.message,
            "result": task.result,
        })


class FeedSyncImportView(LoginRequiredMixin, View):
    """确认导入：启动异步批量导入"""

    def post(self, request):
        import threading
        task_id = request.POST.get("task_id")
        source = request.POST.get("source")
        tag_ids = request.POST.getlist("tags")

        preview_task = get_object_or_404(TaskProgress, pk=task_id)
        result = preview_task.result or {}
        items = result.get("new_items", [])

        if not items:
            messages.info(request, "没有需要导入的条目")
            return redirect("sync:list")

        # 创建导入任务
        import_task = TaskProgress.objects.create(
            task_type="sync_import",
            status="pending",
            total=len(items),
            message=f"准备导入 {len(items)} 条...",
        )
        t = threading.Thread(
            target=_run_sync_import,
            args=(import_task.pk, items, source, tag_ids, result.get("feed_id")),
            daemon=True,
        )
        t.start()
        return redirect("sync:import_progress", task_id=import_task.pk)


def _run_sync_import(task_id, items, source, tag_ids, feed_id):
    """后台线程：批量导入，带进度"""
    import_task = TaskProgress.objects.get(pk=task_id)
    import_task.status = "running"
    import_task.save(update_fields=["status"])

    try:
        selected_tags = Tag.objects.filter(pk__in=tag_ids) if tag_ids else []

        # 先收集所有已有 IP，用于判断
        existing_single = set(
            MaliciousIP.objects.filter(ip_address__isnull=False)
            .values_list("ip_address", flat=True)
        )
        existing_cidr = set(
            MaliciousIP.objects.filter(cidr__isnull=False)
            .values_list("cidr", flat=True)
        )

        to_create = []
        new_count = 0

        for i, item in enumerate(items):
            if TaskProgress.objects.get(pk=task_id).cancel_flag:
                import_task.status = "cancelled"
                import_task.save(update_fields=["status"])
                return

            typ, val = item["type"], item["value"]

            if typ == "single":
                if val not in existing_single:
                    to_create.append(MaliciousIP(ip_address=val, source=source, confidence=50))
                    new_count += 1
            elif typ == "cidr":
                if val not in existing_cidr:
                    to_create.append(MaliciousIP(cidr=val, source=source, confidence=50))
                    new_count += 1
            elif typ == "range":
                parts = val.split("-", 1)
                if not MaliciousIP.objects.filter(range_start=parts[0], range_end=parts[1]).exists():
                    to_create.append(MaliciousIP(range_start=parts[0], range_end=parts[1], source=source, confidence=50))
                    new_count += 1
            elif typ == "domain":
                MaliciousDomain.objects.get_or_create(
                    domain=val, defaults={"source": source, "prefix_at": False}
                )

            import_task.progress = i + 1
            import_task.current_item = val
            if i % 500 == 0:
                import_task.save(update_fields=["progress", "current_item"])

        # 批量创建
        BATCH_SIZE = 500
        created = 0
        for i in range(0, len(to_create), BATCH_SIZE):
            batch = MaliciousIP.objects.bulk_create(to_create[i:i + BATCH_SIZE], ignore_conflicts=True)
            created += len(batch)
            import_task.progress = min(import_task.progress + BATCH_SIZE, import_task.total)
            import_task.save(update_fields=["progress"])

        # 添加标签
        for ip in MaliciousIP.objects.filter(
            pk__in=[obj.pk for obj in MaliciousIP.objects.filter(
                ip_address__in=[x.ip_address for x in to_create if x.ip_address]
            )]
        ):
            for tag in selected_tags:
                ip.tags.add(tag)

        # 更新 feed 统计
        if feed_id:
            feed = SourceFeed.objects.get(pk=feed_id)
            feed.last_sync_count = created
            feed.total_sync_count = (feed.total_sync_count or 0) + created
            feed.save(update_fields=["last_sync_count", "total_sync_count"])

        import_task.status = "completed"
        import_task.message = f"导入完成：新增 {created} 条"
        import_task.result = {"new": created}
        import_task.progress = import_task.total
        import_task.save(update_fields=["status", "message", "result", "progress"])

    except Exception as e:
        import_task.status = "failed"
        import_task.message = str(e)
        import_task.save(update_fields=["status", "message"])
