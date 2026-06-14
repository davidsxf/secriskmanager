import io
import ipaddress

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from .exporters import export_conf_file
from .forms import (
    MaliciousIPDiffForm,
    MaliciousIPForm,
    MaliciousIPImportForm,
    MaliciousIPLookupForm,
)
from .models import MaliciousIP, SourcePreset, Tag
from .parsers import parse_conf_file


class MaliciousIPListView(LoginRequiredMixin, ListView):
    model = MaliciousIP
    template_name = "risk_ip/_list.html"
    context_object_name = "ips"
    paginate_by = 50
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = MaliciousIP.objects.all()
        q = self.request.GET.get("q")
        source = self.request.GET.get("source")
        category = self.request.GET.get("category")
        active = self.request.GET.get("is_active")
        tag_slug = self.request.GET.get("tag")

        if q:
            qs = qs.filter(
                Q(ip_address__icontains=q)
                | Q(cidr__icontains=q)
                | Q(remark__icontains=q)
            )
        if source:
            qs = qs.filter(source=source)
        if category:
            qs = qs.filter(category=category)
        if active in ("1", "0"):
            qs = qs.filter(is_active=(active == "1"))
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)
        batch = self.request.GET.get("batch")
        if batch:
            from django.utils import timezone
            from datetime import datetime
            try:
                dt = datetime.strptime(batch, "%Y-%m-%d").date()
                qs = qs.filter(created_at__date=dt)
            except ValueError:
                pass
        # 排序
        sort = self.request.GET.get("sort", "-created_at")
        allowed = ["source", "-source", "category", "-category", "created_at", "-created_at"]
        qs = qs.order_by(sort if sort in allowed else "-created_at")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["source_choices"] = SourcePreset.objects.all()
        ctx["category_choices"] = (
            MaliciousIP.objects.values_list("category", flat=True)
            .distinct()
            .order_by("category")
        )
        from risk_ip.models import Tag
        ctx["tag_choices"] = Tag.objects.all().order_by("name")

        # 最后三批次筛选（同一天算一批次）
        dates = (
            MaliciousIP.objects
            .dates("created_at", "day", order="DESC")
        )
        ctx["batch_dates"] = list(dates[:3])
        # 排序状态
        sort = self.request.GET.get("sort", "-created_at")
        ctx["current_sort"] = sort
        ctx["next_sort"] = {}
        for col in ["source", "category", "created_at"]:
            ctx["next_sort"][col] = f"-{col}" if sort == col else col
        ctx.update(self.request.GET.dict())
        return ctx


class MaliciousIPCreateView(LoginRequiredMixin, CreateView):
    model = MaliciousIP
    form_class = MaliciousIPForm
    template_name = "risk_ip/_form.html"
    success_url = reverse_lazy("risk_ip:list")

    def form_valid(self, form):
        messages.success(self.request, "恶意 IP 添加成功")
        return super().form_valid(form)


class MaliciousIPUpdateView(LoginRequiredMixin, UpdateView):
    model = MaliciousIP
    form_class = MaliciousIPForm
    template_name = "risk_ip/_form.html"
    success_url = reverse_lazy("risk_ip:list")

    def form_valid(self, form):
        messages.success(self.request, "恶意 IP 更新成功")
        return super().form_valid(form)


class MaliciousIPDeleteView(LoginRequiredMixin, DeleteView):
    model = MaliciousIP
    template_name = "risk_ip/_confirm_delete.html"
    success_url = reverse_lazy("risk_ip:list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "恶意 IP 已删除")
        return super().delete(request, *args, **kwargs)


class MaliciousIPBulkDeleteView(LoginRequiredMixin, View):
    def post(self, request):
        ids = request.POST.getlist("selected_ids")
        count = MaliciousIP.objects.filter(pk__in=ids).delete()[0]
        messages.success(request, f"批量删除完成，共删除 {count} 条")
        return redirect("risk_ip:list")


class MaliciousIPImportView(LoginRequiredMixin, FormView):
    form_class = MaliciousIPImportForm
    template_name = "risk_ip/_import.html"
    success_url = reverse_lazy("risk_ip:list")

    def form_valid(self, form):
        ip_file = form.cleaned_data["ip_file"]
        source = form.cleaned_data["source"]
        content = ip_file.read()

        for enc in ("utf-8", "gbk"):
            try:
                content = content.decode(enc)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        else:
            messages.error(self.request, "无法解码文件编码（支持 UTF-8 / GBK）")
            return self.form_invalid(form)

        # 解析并预览统计
        from risk_ip.parsers import parse_conf_file
        results = parse_conf_file(content)
        total = len(results)

        # 统计库中已存在数量
        exist_count = 0
        for item in results:
            if item["type"] == "single":
                if MaliciousIP.objects.filter(ip_address=item["ip"]).exists():
                    exist_count += 1
            elif item["type"] == "cidr":
                if MaliciousIP.objects.filter(cidr=item["cidr"]).exists():
                    exist_count += 1
            elif item["type"] == "range":
                if MaliciousIP.objects.filter(
                    range_start=item["range_start"],
                    range_end=item["range_end"],
                ).exists():
                    exist_count += 1

        # 存到 session 供确认导入使用
        self.request.session["import_preview"] = {
            "content": content,
            "source": source,
            "total": total,
            "exist_count": exist_count,
            "new_count": total - exist_count,
        }

        return redirect("risk_ip:import_preview")


class MaliciousIPImportPreviewView(LoginRequiredMixin, TemplateView):
    template_name = "risk_ip/_import_preview.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        preview = self.request.session.get("import_preview", {})
        ctx.update(preview)
        return ctx


class MaliciousIPImportConfirmView(LoginRequiredMixin, View):
    def post(self, request):
        preview = request.session.get("import_preview", {})
        content = preview.get("content", "")
        source = preview.get("source", "manual")

        if not content:
            messages.error(request, "请先上传文件")
            return redirect("risk_ip:import")

        from sync.models import TaskProgress
        from sync.task_views import _run_ip_import_with_source
        import threading

        task = TaskProgress.objects.create(task_type="ip_import", status="pending", total=0)
        t = threading.Thread(
            target=_run_ip_import_with_source,
            args=(task.pk, content, source),
            daemon=True,
        )
        t.start()

        # 清除 session 预览数据
        del request.session["import_preview"]

        return redirect("risk_ip:import_progress", task_id=task.pk)


class MaliciousIPExportView(LoginRequiredMixin, View):
    def get(self, request):
        content = export_conf_file()
        return HttpResponse(
            content,
            content_type="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": 'attachment; filename="IPGroup_export.conf"'
            },
        )

    def post(self, request):
        """导出选中的 IP"""
        import json
        ids = request.POST.getlist("selected_ids")
        if not ids:
            messages.error(request, "请先勾选要导出的 IP")
            return redirect("risk_ip:list")
        qs = MaliciousIP.objects.filter(pk__in=ids)
        content = export_conf_file(qs)
        return HttpResponse(
            content,
            content_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="IPGroup_selected.conf"'},
        )


class MaliciousIPDiffView(LoginRequiredMixin, TemplateView):
    template_name = "risk_ip/_diff.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = MaliciousIPDiffForm()
        ctx["diff_a"] = None
        ctx["diff_b"] = None
        from risk_ip.models import SourcePreset, Tag
        ctx["source_choices"] = SourcePreset.objects.all().order_by("name")
        ctx["tag_choices"] = Tag.objects.all().order_by("name")
        return ctx

    def post(self, request):
        form = MaliciousIPDiffForm(request.POST, request.FILES)
        ctx = self.get_context_data()
        ctx["form"] = form

        if form.is_valid():
            conf_file = form.cleaned_data["conf_file"]
            content = conf_file.read()
            for enc in ("utf-8", "gbk"):
                try:
                    content = content.decode(enc)
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            else:
                messages.error(request, "无法解码文件编码")
                return self.render_to_response(ctx)

            device_entries = parse_conf_file(content)

            system_ips = set()
            for obj in MaliciousIP.objects.filter(is_active=True):
                if obj.ip_address:
                    system_ips.add(("single", obj.ip_address))
                elif obj.cidr:
                    system_ips.add(("cidr", obj.cidr))
                elif obj.range_start and obj.range_end:
                    system_ips.add(("range", f"{obj.range_start}-{obj.range_end}"))

            device_set = set()
            for e in device_entries:
                if e["type"] == "single":
                    device_set.add(("single", e["ip"]))
                elif e["type"] == "cidr":
                    device_set.add(("cidr", e["cidr"]))
                elif e["type"] == "range":
                    device_set.add(("range", f"{e['range_start']}-{e['range_end']}"))

            diff_a_set = device_set - system_ips
            diff_b_set = system_ips - device_set

            ctx["diff_a"] = [val for _, val in sorted(diff_a_set)]
            ctx["diff_b"] = [val for _, val in sorted(diff_b_set)]
            ctx["stats"] = {
                "total_device": len(device_entries),
                "total_system": MaliciousIP.objects.filter(is_active=True).count(),
                "diff_a_count": len(diff_a_set),
                "diff_b_count": len(diff_b_set),
                "matched": len(device_set & system_ips),
            }

            # 保存差异数据到 session
            diff_a_json = [{"type": t, "value": v} for t, v in sorted(diff_a_set)]
            request.session["diff_a_data"] = diff_a_json
            request.session["diff_b_data"] = [v for _, v in sorted(diff_b_set)]

        return self.render_to_response(ctx)


class MaliciousIPLookupView(LoginRequiredMixin, FormView):
    form_class = MaliciousIPLookupForm
    template_name = "risk_ip/_lookup.html"

    def form_valid(self, form):
        query = form.cleaned_data["query"].strip()
        ctx = self.get_context_data()
        ctx["form"] = form
        ctx["results"] = []
        ctx["query"] = query

        # 精确匹配
        qs = MaliciousIP.objects.filter(is_active=True)
        try:
            ip = ipaddress.ip_address(query)
            matched = qs.filter(
                Q(ip_address=str(ip))
                | Q(range_start__lte=str(ip), range_end__gte=str(ip))
            )
            # 也匹配 CIDR
            for obj in qs.exclude(cidr__isnull=True).exclude(cidr=""):
                try:
                    net = ipaddress.ip_network(obj.cidr, strict=False)
                    if ip in net:
                        matched = matched | MaliciousIP.objects.filter(pk=obj.pk)
                except ValueError:
                    pass
            ctx["results"] = matched.distinct()
        except ValueError:
            pass

        if not ctx["results"]:
            messages.info(self.request, f'未找到与 "{query}" 匹配的风险 IP')
        return self.render_to_response(ctx)


class DiffAImportView(LoginRequiredMixin, View):
    """将差异 A（设备有·系统无）批量导入系统"""

    def post(self, request):
        source = request.POST.get("source", "manual")
        tag_ids = request.POST.getlist("tags")
        items = request.session.get("diff_a_data", [])

        if not items:
            messages.error(request, "没有差异数据，请先上传比对文件")
            return redirect("risk_ip:diff")

        from risk_ip.models import Tag
        selected_tags = Tag.objects.filter(pk__in=tag_ids)

        new_count = 0
        for item in items:
            typ = item["type"]
            val = item["value"]
            defaults = {"source": source, "confidence": 50}
            if typ == "single":
                obj, created = MaliciousIP.objects.get_or_create(ip_address=val, defaults=defaults)
            elif typ == "cidr":
                obj, created = MaliciousIP.objects.get_or_create(cidr=val, defaults=defaults)
            elif typ == "range":
                parts = val.split("-", 1)
                obj, created = MaliciousIP.objects.get_or_create(
                    range_start=parts[0], range_end=parts[1], defaults=defaults
                )
            else:
                continue

            if created:
                new_count += 1
            # 添加标签
            for tag in selected_tags:
                obj.tags.add(tag)

        msg = f"差异 A 导入完成：新增 {new_count} 条，来源: {source}"
        if selected_tags:
            tag_names = [t.name for t in selected_tags]
            msg += f"，标签: {', '.join(tag_names)}"
        messages.success(request, msg)
        return redirect("risk_ip:diff")


class DiffBExportView(LoginRequiredMixin, View):
    """导出差异 B（系统有·设备无）为 .conf 文件"""

    def post(self, request):
        items = request.session.get("diff_b_data", [])

        if not items:
            messages.error(request, "没有差异数据，请先上传比对文件")
            return redirect("risk_ip:diff")

        lines = ["# 差异导出: 系统存在但设备未配置", f"# 共 {len(items)} 条", ""]
        lines.extend(items)
        content = "\n".join(lines) + "\n"

        return HttpResponse(
            content,
            content_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="IPGroup_diff_B.conf"'},
        )


class MaliciousIPImportProgressView(LoginRequiredMixin, DetailView):
    template_name = "risk_ip/_import_progress.html"
    context_object_name = "task"

    def get_object(self, queryset=None):
        from sync.models import TaskProgress
        return TaskProgress.objects.get(pk=self.kwargs["task_id"])


# ─── 来源管理 ───────────────────────────────────────────────

class SourcePresetListView(LoginRequiredMixin, ListView):
    model = SourcePreset
    template_name = "risk_ip/source_list.html"
    context_object_name = "sources"


class SourcePresetCreateView(LoginRequiredMixin, CreateView):
    model = SourcePreset
    template_name = "risk_ip/source_form.html"
    fields = ["name", "is_manual", "description"]
    success_url = reverse_lazy("risk_ip:source_list")

    def form_valid(self, form):
        messages.success(self.request, f'来源 "{form.instance.name}" 创建成功')
        return super().form_valid(form)


class SourcePresetUpdateView(LoginRequiredMixin, UpdateView):
    model = SourcePreset
    template_name = "risk_ip/source_form.html"
    fields = ["name", "is_manual", "description"]
    success_url = reverse_lazy("risk_ip:source_list")

    def form_valid(self, form):
        messages.success(self.request, f'来源 "{form.instance.name}" 已更新')
        return super().form_valid(form)


class SourcePresetDeleteView(LoginRequiredMixin, DeleteView):
    model = SourcePreset
    template_name = "risk_ip/source_confirm_delete.html"
    success_url = reverse_lazy("risk_ip:source_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "来源已删除")
        return super().delete(request, *args, **kwargs)


class TagListView(LoginRequiredMixin, ListView):
    model = Tag
    template_name = "risk_ip/tag_list.html"
    context_object_name = "tags"
    ordering = ["name"]


class TagCreateView(LoginRequiredMixin, CreateView):
    model = Tag
    template_name = "risk_ip/tag_form.html"
    fields = ["name", "color", "description"]
    success_url = reverse_lazy("risk_ip:tag_list")

    def form_valid(self, form):
        messages.success(self.request, f'标签 "{form.instance.name}" 创建成功')
        return super().form_valid(form)


class TagDeleteView(LoginRequiredMixin, DeleteView):
    model = Tag
    template_name = "risk_ip/tag_confirm_delete.html"
    success_url = reverse_lazy("risk_ip:tag_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "标签已删除")
        return super().delete(request, *args, **kwargs)


class BulkTagView(LoginRequiredMixin, View):
    def post(self, request):
        action = request.POST.get("action")  # "add" or "remove"
        tag_id = request.POST.get("tag_id")
        ip_ids = request.POST.getlist("selected_ids")

        try:
            tag = Tag.objects.get(pk=tag_id)
        except Tag.DoesNotExist:
            messages.error(request, "请选择标签")
            return redirect("risk_ip:list")

        ips = MaliciousIP.objects.filter(pk__in=ip_ids)
        count = ips.count()

        if action == "add":
            for ip in ips:
                ip.tags.add(tag)
            messages.success(request, f'已为 {count} 个 IP 添加标签 "{tag.name}"')
        elif action == "remove":
            for ip in ips:
                ip.tags.remove(tag)
            messages.success(request, f'已从 {count} 个 IP 移除标签 "{tag.name}"')

        return redirect("risk_ip:list")
