from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, View

from .models import AllowedIP


class AllowedIPListView(LoginRequiredMixin, ListView):
    model = AllowedIP
    template_name = "accounts/allowed_ip_list.html"
    context_object_name = "allowed_ips"


class AllowedIPCreateView(LoginRequiredMixin, CreateView):
    model = AllowedIP
    template_name = "accounts/allowed_ip_form.html"
    fields = ["cidr", "description"]
    success_url = reverse_lazy("accounts:allowed_ip_list")

    def form_valid(self, form):
        messages.success(self.request, f"IP 段 {form.instance.cidr} 已添加")
        return super().form_valid(form)


class AllowedIPToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        entry = AllowedIP.objects.get(pk=pk)
        entry.is_active = not entry.is_active
        entry.save(update_fields=["is_active"])
        status = "启用" if entry.is_active else "停用"
        messages.success(request, f"IP 段 {entry.cidr} 已{status}")
        return redirect("accounts:allowed_ip_list")


class AllowedIPDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        entry = AllowedIP.objects.get(pk=pk)
        cidr = entry.cidr
        entry.delete()
        messages.success(request, f"IP 段 {cidr} 已删除")
        return redirect("accounts:allowed_ip_list")
