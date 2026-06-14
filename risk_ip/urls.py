from django.urls import path

from . import views

app_name = "risk_ip"

urlpatterns = [
    path("", views.MaliciousIPListView.as_view(), name="list"),
    path("create/", views.MaliciousIPCreateView.as_view(), name="create"),
    path("<int:pk>/update/", views.MaliciousIPUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.MaliciousIPDeleteView.as_view(), name="delete"),
    path("bulk-delete/", views.MaliciousIPBulkDeleteView.as_view(), name="bulk_delete"),
    path("import/", views.MaliciousIPImportView.as_view(), name="import"),
    path("import/preview/", views.MaliciousIPImportPreviewView.as_view(), name="import_preview"),
    path("import/confirm/", views.MaliciousIPImportConfirmView.as_view(), name="import_confirm"),
    path("import/progress/<int:task_id>/", views.MaliciousIPImportProgressView.as_view(), name="import_progress"),
    path("export/", views.MaliciousIPExportView.as_view(), name="export"),
    path("diff/", views.MaliciousIPDiffView.as_view(), name="diff"),
    path("diff/import-a/", views.DiffAImportView.as_view(), name="diff_import_a"),
    path("diff/export-b/", views.DiffBExportView.as_view(), name="diff_export_b"),
    path("lookup/", views.MaliciousIPLookupView.as_view(), name="lookup"),
    # 标签管理
    path("tags/", views.TagListView.as_view(), name="tag_list"),
    path("tags/create/", views.TagCreateView.as_view(), name="tag_create"),
    path("tags/<int:pk>/delete/", views.TagDeleteView.as_view(), name="tag_delete"),
    # 来源管理
    path("sources/", views.SourcePresetListView.as_view(), name="source_list"),
    path("sources/create/", views.SourcePresetCreateView.as_view(), name="source_create"),
    path("sources/<int:pk>/update/", views.SourcePresetUpdateView.as_view(), name="source_update"),
    path("sources/<int:pk>/delete/", views.SourcePresetDeleteView.as_view(), name="source_delete"),
    # 批量操作
    path("bulk-tag/", views.BulkTagView.as_view(), name="bulk_tag"),
]
