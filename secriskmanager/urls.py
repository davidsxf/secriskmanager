from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("risk-ip/", include("risk_ip.urls")),
    path("risk-domain/", include("risk_domain.urls")),
    path("assets/", include("local_assets.urls")),
    path("feeds/", include("sync.urls")),
    path("import-export/", TemplateView.as_view(template_name="import_export_center.html"), name="import_export_center"),
    path("", include("dashboard.urls")),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
