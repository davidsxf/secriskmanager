from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView, View

from .models import SourceFeed, SourceRecord


class SourceFeedListView(LoginRequiredMixin, ListView):
    model = SourceFeed
    template_name = "sync/_list.html"
    context_object_name = "feeds"
    paginate_by = 50


class SourceFeedCreateView(LoginRequiredMixin, CreateView):
    model = SourceFeed
    template_name = "sync/_form.html"
    fields = [
        "name", "slug", "feed_type", "url", "format", "auth_type",
        "auth_key", "auth_header_template", "is_active", "interval_minutes",
        "retry_count", "timeout_seconds", "confidence_base",
        "category_default", "filter_private", "description",
    ]
    success_url = reverse_lazy("sync:list")

    def form_valid(self, form):
        messages.success(self.request, "情报源添加成功")
        return super().form_valid(form)


class SourceFeedUpdateView(LoginRequiredMixin, UpdateView):
    model = SourceFeed
    template_name = "sync/_form.html"
    fields = [
        "name", "slug", "feed_type", "url", "format", "auth_type",
        "auth_key", "auth_header_template", "is_active", "interval_minutes",
        "retry_count", "timeout_seconds", "confidence_base",
        "category_default", "filter_private", "description",
    ]
    success_url = reverse_lazy("sync:list")

    def form_valid(self, form):
        messages.success(self.request, "情报源更新成功")
        return super().form_valid(form)


class SourceFeedToggleView(LoginRequiredMixin, View):
    def post(self, request, pk):
        feed = SourceFeed.objects.get(pk=pk)
        feed.is_active = not feed.is_active
        feed.save()
        status = "启用" if feed.is_active else "停用"
        messages.success(request, f"情报源「{feed.name}」已{status}")
        return redirect("sync:list")


class SourceFeedSyncView(LoginRequiredMixin, View):
    def post(self, request, pk):
        feed = SourceFeed.objects.get(pk=pk)
        return redirect("sync:sync_preview", pk=pk)


class SourceFeedDeleteView(LoginRequiredMixin, DeleteView):
    model = SourceFeed
    success_url = reverse_lazy("sync:list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "情报源已删除")
        return super().delete(request, *args, **kwargs)
