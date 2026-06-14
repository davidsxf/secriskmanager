from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.views.generic import TemplateView

from local_assets.models import LocalAsset
from risk_domain.models import MaliciousDomain
from risk_ip.models import MaliciousIP


class DashboardIndexView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # 统计卡片
        ctx["ip_total"] = MaliciousIP.objects.count()
        ctx["ip_active"] = MaliciousIP.objects.filter(is_active=True).count()
        ctx["domain_total"] = MaliciousDomain.objects.count()
        ctx["domain_active"] = MaliciousDomain.objects.filter(is_active=True).count()
        ctx["asset_total"] = LocalAsset.objects.count()

        # IP 分类分布（带百分比）
        ip_total_active = MaliciousIP.objects.filter(is_active=True).count() or 1
        ip_categories_raw = (
            MaliciousIP.objects.values("category")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        ctx["ip_categories"] = [
            {**c, "pct": round(c["count"] / ip_total_active * 100)}
            for c in ip_categories_raw
        ]

        # IP 来源分布
        ctx["ip_sources"] = (
            MaliciousIP.objects.values("source")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        # 域名分类分布
        ctx["domain_categories"] = (
            MaliciousDomain.objects.values("category")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        # 近期新增 IP（最近 7 条）
        ctx["recent_ips"] = MaliciousIP.objects.order_by("-created_at")[:7]

        # 近期新增域名
        ctx["recent_domains"] = MaliciousDomain.objects.order_by("-created_at")[:7]

        # 设备类型分布
        ctx["device_types"] = (
            LocalAsset.objects.values("device_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return ctx
