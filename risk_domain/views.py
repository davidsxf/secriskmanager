from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, FormView, ListView, TemplateView, UpdateView, View

from .exporters import export_txt_file
from .forms import MaliciousDomainDiffForm, MaliciousDomainForm, MaliciousDomainImportForm
from .models import MaliciousDomain
from .parsers import parse_txt_file


class MaliciousDomainListView(LoginRequiredMixin, ListView):
    model = MaliciousDomain
    template_name = "risk_domain/_list.html"
    context_object_name = "domains"
    paginate_by = 50
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = MaliciousDomain.objects.all()
        q = self.request.GET.get("q")
        source = self.request.GET.get("source")
        category = self.request.GET.get("category")
        active = self.request.GET.get("is_active")
        batch = self.request.GET.get("batch")

        if q:
            qs = qs.filter(Q(domain__icontains=q) | Q(remark__icontains=q))
        if source:
            qs = qs.filter(source=source)
        if category:
            qs = qs.filter(category=category)
        if active in ("1", "0"):
            qs = qs.filter(is_active=(active == "1"))
        if batch:
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
        ctx["source_choices"] = (
            MaliciousDomain.objects.values_list("source", flat=True).distinct().order_by("source")
        )
        ctx["category_choices"] = (
            MaliciousDomain.objects.values_list("category", flat=True).distinct().order_by("category")
        )
        # 最后三批次
        dates = MaliciousDomain.objects.dates("created_at", "day", order="DESC")
        ctx["batch_dates"] = list(dates[:3])
        # 排序状态
        sort = self.request.GET.get("sort", "-created_at")
        ctx["current_sort"] = sort
        ctx["next_sort"] = {}
        for col in ["source", "category", "created_at"]:
            ctx["next_sort"][col] = f"-{col}" if sort == col else col
        ctx.update(self.request.GET.dict())
        return ctx


class MaliciousDomainCreateView(LoginRequiredMixin, CreateView):
    model = MaliciousDomain
    form_class = MaliciousDomainForm
    template_name = "risk_domain/_form.html"
    success_url = reverse_lazy("risk_domain:list")

    def form_valid(self, form):
        messages.success(self.request, "恶意域名添加成功")
        return super().form_valid(form)


class MaliciousDomainUpdateView(LoginRequiredMixin, UpdateView):
    model = MaliciousDomain
    form_class = MaliciousDomainForm
    template_name = "risk_domain/_form.html"
    success_url = reverse_lazy("risk_domain:list")

    def form_valid(self, form):
        messages.success(self.request, "恶意域名更新成功")
        return super().form_valid(form)


class MaliciousDomainDeleteView(LoginRequiredMixin, DeleteView):
    model = MaliciousDomain
    template_name = "risk_domain/_confirm_delete.html"
    success_url = reverse_lazy("risk_domain:list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "恶意域名已删除")
        return super().delete(request, *args, **kwargs)


class MaliciousDomainBulkDeleteView(LoginRequiredMixin, View):
    def post(self, request):
        ids = request.POST.getlist("selected_ids")
        count = MaliciousDomain.objects.filter(pk__in=ids).delete()[0]
        messages.success(request, f"批量删除完成，共删除 {count} 条")
        return redirect("risk_domain:list")


class MaliciousDomainImportView(LoginRequiredMixin, FormView):
    form_class = MaliciousDomainImportForm
    template_name = "risk_domain/_import.html"
    success_url = reverse_lazy("risk_domain:list")

    def form_valid(self, form):
        txt_file = form.cleaned_data["txt_file"]
        content = txt_file.read()
        for enc in ("utf-8", "gbk"):
            try:
                content = content.decode(enc)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        else:
            messages.error(self.request, "无法解码文件编码")
            return self.form_invalid(form)

        results = parse_txt_file(content)
        new_count = 0
        skip_count = 0
        for item in results:
            _, created = MaliciousDomain.objects.get_or_create(
                domain=item["domain"],
                defaults={
                    "prefix_at": item["prefix_at"],
                    "source": "file_import",
                    "category": "",
                },
            )
            if created:
                new_count += 1
            else:
                skip_count += 1
        messages.success(self.request, f"导入完成：新增 {new_count} 条，跳过 {skip_count} 条（已存在）")
        return super().form_valid(form)


class MaliciousDomainExportView(LoginRequiredMixin, View):
    def get(self, request):
        content = export_txt_file()
        return HttpResponse(
            content,
            content_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="URLGroup_DOMAIN_GROUP_export.txt"'},
        )

    def post(self, request):
        """导出选中的域名"""
        ids = request.POST.getlist("selected_ids")
        if not ids:
            messages.error(request, "请先勾选要导出的域名")
            return redirect("risk_domain:list")
        qs = MaliciousDomain.objects.filter(pk__in=ids)
        content = export_txt_file(qs)
        return HttpResponse(
            content,
            content_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="URLGroup_DOMAIN_GROUP_selected.txt"'},
        )


class MaliciousDomainDiffView(LoginRequiredMixin, TemplateView):
    template_name = "risk_domain/_diff.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = MaliciousDomainDiffForm()
        ctx["diff_a"] = None
        ctx["diff_b"] = None
        from risk_ip.models import SourcePreset, Tag
        ctx["source_choices"] = SourcePreset.objects.all().order_by("name")
        ctx["tag_choices"] = Tag.objects.all().order_by("name")
        return ctx

    def post(self, request):
        form = MaliciousDomainDiffForm(request.POST, request.FILES)
        ctx = self.get_context_data()
        ctx["form"] = form

        if form.is_valid():
            txt_file = form.cleaned_data["txt_file"]
            content = txt_file.read()
            for enc in ("utf-8", "gbk"):
                try:
                    content = content.decode(enc)
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            else:
                messages.error(request, "无法解码文件编码")
                return self.render_to_response(ctx)

            device_entries = parse_txt_file(content)
            system_domains = set(
                (obj.domain, obj.prefix_at)
                for obj in MaliciousDomain.objects.filter(is_active=True)
            )
            device_set = set((e["domain"], e["prefix_at"]) for e in device_entries)

            diff_a_set = device_set - system_domains
            diff_b_set = system_domains - device_set

            def fmt(entry_set):
                return [f"@{d}" if p else d for d, p in sorted(entry_set)]

            ctx["diff_a"] = fmt(diff_a_set)
            ctx["diff_b"] = fmt(diff_b_set)
            ctx["stats"] = {
                "total_device": len(device_entries),
                "total_system": MaliciousDomain.objects.filter(is_active=True).count(),
                "diff_a_count": len(diff_a_set),
                "diff_b_count": len(diff_b_set),
                "matched": len(device_set & system_domains),
            }

            # 保存差异数据到 session
            request.session["domain_diff_a"] = [
                {"domain": d, "prefix_at": p} for d, p in sorted(diff_a_set)
            ]
            request.session["domain_diff_b"] = fmt(diff_b_set)

        return self.render_to_response(ctx)


class DomainDiffAImportView(LoginRequiredMixin, View):
    """差异 A（设备有·系统无）批量导入域名"""

    def post(self, request):
        source = request.POST.get("source", "manual")
        tag_ids = request.POST.getlist("tags")
        items = request.session.get("domain_diff_a", [])

        if not items:
            messages.error(request, "没有差异数据，请先上传比对文件")
            return redirect("risk_domain:diff")

        from risk_ip.models import Tag
        selected_tags = Tag.objects.filter(pk__in=tag_ids)

        new_count = 0
        for item in items:
            obj, created = MaliciousDomain.objects.get_or_create(
                domain=item["domain"],
                defaults={"prefix_at": item["prefix_at"], "source": source},
            )
            if created:
                new_count += 1
                for tag in selected_tags:
                    obj.tags.add(tag)

        msg = f"差异 A 导入完成：新增 {new_count} 条，来源: {source}"
        if selected_tags:
            tag_names = [t.name for t in selected_tags]
            msg += f"，标签: {', '.join(tag_names)}"
        messages.success(request, msg)
        return redirect("risk_domain:diff")


class DomainDiffBExportView(LoginRequiredMixin, View):
    """差异 B（系统有·设备无）导出 .txt"""

    def post(self, request):
        items = request.session.get("domain_diff_b", [])
        if not items:
            messages.error(request, "没有差异数据，请先上传比对文件")
            return redirect("risk_domain:diff")

        content = "# 差异导出: 系统存在但设备未配置\n" + f"# 共 {len(items)} 条\n\n"
        content += "\n".join(items) + "\n"

        return HttpResponse(
            content,
            content_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="URLGroup_DOMAIN_GROUP_diff_B.txt"'},
        )
