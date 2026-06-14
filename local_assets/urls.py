from django.urls import path

from . import views

app_name = "local_assets"

urlpatterns = [
    path("", views.LocalAssetListView.as_view(), name="list"),
    path("create/", views.LocalAssetCreateView.as_view(), name="create"),
    path("<int:pk>/update/", views.LocalAssetUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.LocalAssetDeleteView.as_view(), name="delete"),
    path("bulk-delete/", views.LocalAssetBulkDeleteView.as_view(), name="bulk_delete"),
    path("import/", views.LocalAssetImportView.as_view(), name="import"),
    path("export/", views.LocalAssetExportView.as_view(), name="export"),
    path("bind-command/", views.LocalAssetBindCommandView.as_view(), name="bind_command"),
    path("bind-command/preview/", views.LocalAssetBindCommandView.as_view(), name="bind_command_preview"),
    path("bind-command/download/", views.LocalAssetBindCommandView.as_view(), name="bind_command_download"),
]
