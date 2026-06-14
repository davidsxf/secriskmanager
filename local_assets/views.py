import re

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, FormView, ListView, TemplateView, UpdateView, View

from .exporters import export_conf_file
from .forms import LocalAssetBindCommandForm, LocalAssetForm, LocalAssetImportForm
from .models import LocalAsset
from .parsers import parse_conf_file


class LocalAssetListView(LoginRequiredMixin, ListView):
    model = LocalAsset
    template_name = "local_assets/_list.html"
    context_object_name = "assets"
    paginate_by = 50
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = LocalAsset.objects.all()
        q = self.request.GET.get("q")
        dept = self.request.GET.get("department")
        dt = self.request.GET.get("device_type")
        if q:
            qs = qs.filter(
                Q(ip_address__icontains=q) | Q(mac_address__icontains=q)
                | Q(person_name__icontains=q) | Q(department__icontains=q)
                | Q(hostname__icontains=q) | Q(remark__icontains=q)
            )
        if dept:
            qs = qs.filter(department=dept)
        if dt:
            qs = qs.filter(device_type=dt)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["dept_choices"] = LocalAsset.objects.values_list("department", flat=True).distinct().order_by("department")
        ctx["device_type_choices"] = LocalAsset.objects.values_list("device_type", flat=True).distinct()
        ctx.update(self.request.GET.dict())
        return ctx


class LocalAssetCreateView(LoginRequiredMixin, CreateView):
    model = LocalAsset
    form_class = LocalAssetForm
    template_name = "local_assets/_form.html"
    success_url = reverse_lazy("local_assets:list")

    def form_valid(self, form):
        mac = form.cleaned_data.get("mac_address", "")
        if mac:
            form.instance.mac_address = mac.replace("-", ":").lower()
        messages.success(self.request, "资产添加成功")
        return super().form_valid(form)


class LocalAssetUpdateView(LoginRequiredMixin, UpdateView):
    model = LocalAsset
    form_class = LocalAssetForm
    template_name = "local_assets/_form.html"
    success_url = reverse_lazy("local_assets:list")

    def form_valid(self, form):
        mac = form.cleaned_data.get("mac_address", "")
        if mac:
            form.instance.mac_address = mac.replace("-", ":").lower()
        messages.success(self.request, "资产更新成功")
        return super().form_valid(form)


class LocalAssetDeleteView(LoginRequiredMixin, DeleteView):
    model = LocalAsset
    template_name = "local_assets/_confirm_delete.html"
    success_url = reverse_lazy("local_assets:list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "资产已删除")
        return super().delete(request, *args, **kwargs)


class LocalAssetBulkDeleteView(LoginRequiredMixin, View):
    def post(self, request):
        ids = request.POST.getlist("selected_ids")
        count = LocalAsset.objects.filter(pk__in=ids).delete()[0]
        messages.success(request, f"批量删除完成，共删除 {count} 条")
        return redirect("local_assets:list")


class LocalAssetImportView(LoginRequiredMixin, FormView):
    form_class = LocalAssetImportForm
    template_name = "local_assets/_import.html"
    success_url = reverse_lazy("local_assets:list")

    def form_valid(self, form):
        conf = form.cleaned_data["conf_file"]
        content = conf.read()
        for enc in ("utf-8", "gbk"):
            try:
                content = content.decode(enc)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        else:
            messages.error(self.request, "无法解码文件编码")
            return self.form_invalid(form)

        results = parse_conf_file(content)
        new_count = 0
        update_count = 0
        for item in results:
            mac = item.get("mac", "")
            if mac:
                mac = mac.replace("-", ":").lower()
            name = item.get("person_name", "")
            obj, created = LocalAsset.objects.update_or_create(
                ip_address=item["ip"],
                defaults={
                    "mac_address": mac,
                    "person_name": name,
                },
            )
            if created:
                new_count += 1
            else:
                update_count += 1

        messages.success(self.request, f"导入完成：新增 {new_count} 条，更新 {update_count} 条")
        return super().form_valid(form)


class LocalAssetExportView(LoginRequiredMixin, View):
    def get(self, request):
        content = export_conf_file()
        return HttpResponse(
            content,
            content_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="ipmacdesc.conf"'},
        )


class LocalAssetBindCommandView(LoginRequiredMixin, TemplateView):
    template_name = "local_assets/_bind_command.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = LocalAssetBindCommandForm()
        ctx["commands"] = None
        q = self.request.GET.get("q", "")
        assets = LocalAsset.objects.all()
        if q:
            assets = assets.filter(
                Q(ip_address__icontains=q) | Q(mac_address__icontains=q)
                | Q(person_name__icontains=q) | Q(hostname__icontains=q)
            )
        ctx["asset_list"] = assets[:100]
        return ctx

    def post(self, request):
        form = LocalAssetBindCommandForm(request.POST)
        ctx = self.get_context_data()
        ctx["form"] = form
        if form.is_valid():
            vlan = form.cleaned_data["vlan"]
            ids = request.POST.get("selected_ids", "")
            pk_list = [int(x) for x in ids.split(",") if x.strip()]
            assets = LocalAsset.objects.filter(pk__in=pk_list)
            commands = []
            for a in assets:
                mac = a.mac_address
                if not mac or mac == "0":
                    commands.append(f"# {a.ip_address} — MAC 缺失，跳过")
                    continue
                mac_clean = mac.replace(":", "").replace("-", "").lower()
                mac_formatted = f"{mac_clean[:4]}-{mac_clean[4:8]}-{mac_clean[8:]}"
                commands.append(f"user-bind static ip-address {a.ip_address} mac-address {mac_formatted} vlan {vlan}")
            ctx["commands"] = commands
            ctx["asset_count"] = len(assets)
        return self.render_to_response(ctx)
