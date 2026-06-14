from django.urls import path

from . import views

app_name = "risk_domain"

urlpatterns = [
    path("", views.MaliciousDomainListView.as_view(), name="list"),
    path("create/", views.MaliciousDomainCreateView.as_view(), name="create"),
    path("<int:pk>/update/", views.MaliciousDomainUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.MaliciousDomainDeleteView.as_view(), name="delete"),
    path("bulk-delete/", views.MaliciousDomainBulkDeleteView.as_view(), name="bulk_delete"),
    path("import/", views.MaliciousDomainImportView.as_view(), name="import"),
    path("export/", views.MaliciousDomainExportView.as_view(), name="export"),
    path("diff/", views.MaliciousDomainDiffView.as_view(), name="diff"),
    path("diff/import-a/", views.DomainDiffAImportView.as_view(), name="diff_import_a"),
    path("diff/export-b/", views.DomainDiffBExportView.as_view(), name="diff_export_b"),
]
