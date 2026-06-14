import json
import threading
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from .models import TaskProgress
from risk_ip.models import MaliciousIP
from risk_ip.parsers import parse_conf_file as parse_ip_file
from risk_domain.models import MaliciousDomain
from risk_domain.parsers import parse_txt_file


def _run_ip_import_with_source(task_id, content, source_slug):
    """后台线程：批量导入 IP，先加载全量数据到内存，批量写入"""
    task = TaskProgress.objects.get(pk=task_id)
    task.status = "running"
    task.save(update_fields=["status"])

    try:
        results = parse_ip_file(content)
        task.total = len(results)
        task.save(update_fields=["total"])

        # 1. 一次性加载数据库中已有的 IP/CIDR/范围（3 次查询）
        existing_single = set(
            MaliciousIP.objects.filter(ip_address__isnull=False)
            .values_list("ip_address", flat=True)
        )
        existing_cidr = set(
            MaliciousIP.objects.filter(cidr__isnull=False)
            .values_list("cidr", flat=True)
        )
        existing_ranges = set(
            MaliciousIP.objects.filter(range_start__isnull=False)
            .values_list("range_start", "range_end")
        )

        # 2. 在内存中分类：新增 vs 更新
        to_create = []
        to_update_single = []
        to_update_cidr = []
        to_update_range = []

        for item in results:
            if TaskProgress.objects.get(pk=task_id).cancel_flag:
                task.status = "cancelled"
                task.message = "已取消"
                task.save(update_fields=["status", "message"])
                return

            if item["type"] == "single":
                ip = item["ip"]
                if ip in existing_single:
                    to_update_single.append(ip)
                else:
                    to_create.append(MaliciousIP(ip_address=ip, source=source_slug, confidence=50))
            elif item["type"] == "cidr":
                c = item["cidr"]
                if c in existing_cidr:
                    to_update_cidr.append(c)
                else:
                    to_create.append(MaliciousIP(cidr=c, source=source_slug, confidence=50))
            elif item["type"] == "range":
                rs, re = item["range_start"], item["range_end"]
                if (rs, re) in existing_ranges:
                    to_update_range.append((rs, re))
                else:
                    to_create.append(MaliciousIP(range_start=rs, range_end=re, source=source_slug, confidence=50))

            processed = len(to_create) + len(to_update_single) + len(to_update_cidr) + len(to_update_range)
            task.progress = processed
            task.current_item = item.get("ip") or item.get("cidr") or f"{item.get('range_start')}-{item.get('range_end')}"
            if processed % 1000 == 0:
                task.save(update_fields=["progress", "current_item"])

        # 3. 批量创建新记录
        BATCH_SIZE = 500
        created_count = 0
        for i in range(0, len(to_create), BATCH_SIZE):
            created = MaliciousIP.objects.bulk_create(to_create[i:i + BATCH_SIZE], ignore_conflicts=True)
            created_count += len(created)

        # 4. 批量更新来源
        updated_count = 0
        if to_update_single:
            n = MaliciousIP.objects.filter(ip_address__in=to_update_single).exclude(source=source_slug).update(source=source_slug)
            updated_count += n
        if to_update_cidr:
            n = MaliciousIP.objects.filter(cidr__in=to_update_cidr).exclude(source=source_slug).update(source=source_slug)
            updated_count += n
        if to_update_range:
            q = Q()
            for rs, re in to_update_range:
                q |= Q(range_start=rs, range_end=re)
            n = MaliciousIP.objects.filter(q).exclude(source=source_slug).update(source=source_slug)
            updated_count += n

        task.status = "completed"
        task.result = {"new": created_count, "updated": updated_count}
        task.message = f"导入完成：新增 {created_count} 条，更新来源 {updated_count} 条"
        task.progress = task.total
        task.save(update_fields=["status", "result", "message", "progress"])

    except Exception as e:
        task.status = "failed"
        task.message = str(e)
        task.save(update_fields=["status", "message"])


def _run_domain_import(task_id, content):
    """后台线程：导入域名文件"""
    task = TaskProgress.objects.get(pk=task_id)
    task.status = "running"
    task.save(update_fields=["status"])

    try:
        results = parse_txt_file(content)
        task.total = len(results)
        task.save(update_fields=["total"])

        new_count = 0
        skip_count = 0
        for i, item in enumerate(results):
            if TaskProgress.objects.get(pk=task_id).cancel_flag:
                task.status = "cancelled"
                task.save(update_fields=["status"])
                return

            _, created = MaliciousDomain.objects.get_or_create(
                domain=item["domain"],
                defaults={"prefix_at": item["prefix_at"], "source": "file_import"},
            )
            if created:
                new_count += 1
            else:
                skip_count += 1
            task.progress = i + 1
            task.current_item = item["domain"]
            task.save(update_fields=["progress", "current_item"])

        task.status = "completed"
        task.result = {"new": new_count, "skipped": skip_count}
        task.message = f"导入完成：新增 {new_count} 条，跳过 {skip_count} 条"
        task.save(update_fields=["status", "result", "message"])
    except Exception as e:
        task.status = "failed"
        task.message = str(e)
        task.save(update_fields=["status", "message"])


@login_required
def task_status(request, task_id):
    try:
        task = TaskProgress.objects.get(pk=task_id)
        return JsonResponse({
            "status": task.status,
            "progress": task.progress,
            "total": task.total,
            "current_item": task.current_item,
            "message": task.message,
            "result": task.result,
            "cancel_flag": task.cancel_flag,
        })
    except TaskProgress.DoesNotExist:
        return JsonResponse({"error": "not_found"}, status=404)


@login_required
@require_POST
def task_cancel(request, task_id):
    try:
        task = TaskProgress.objects.get(pk=task_id)
        task.cancel()
        return JsonResponse({"status": "cancelling"})
    except TaskProgress.DoesNotExist:
        return JsonResponse({"error": "not_found"}, status=404)


@login_required
@require_POST
def task_retry(request, task_id):
    try:
        task = TaskProgress.objects.get(pk=task_id)
        task.cancel_flag = False
        task.status = "pending"
        task.progress = 0
        task.message = ""
        task.save(update_fields=["cancel_flag", "status", "progress", "message"])
        return JsonResponse({"status": "retrying"})
    except TaskProgress.DoesNotExist:
        return JsonResponse({"error": "not_found"}, status=404)
