from django.urls import path

from . import views
from . import task_views
from . import sync_preview
from . import backup_views

app_name = "sync"

urlpatterns = [
    path("", views.SourceFeedListView.as_view(), name="list"),
    path("create/", views.SourceFeedCreateView.as_view(), name="create"),
    path("<int:pk>/update/", views.SourceFeedUpdateView.as_view(), name="update"),
    path("<int:pk>/toggle/", views.SourceFeedToggleView.as_view(), name="toggle"),
    path("<int:pk>/sync/", views.SourceFeedSyncView.as_view(), name="sync"),
    path("<int:pk>/sync-preview/", sync_preview.FeedSyncPreviewView.as_view(), name="sync_preview"),
    path("<int:pk>/delete/", views.SourceFeedDeleteView.as_view(), name="delete"),
    path("sync-progress/<int:task_id>/", sync_preview.FeedSyncProgressView.as_view(), name="sync_progress"),
    path("import-progress/<int:task_id>/", sync_preview.FeedSyncProgressView.as_view(), name="import_progress"),
    path("task/<int:task_id>/sync-result/", sync_preview.FeedSyncResultView.as_view(), name="sync_result"),
    path("sync-import/", sync_preview.FeedSyncImportView.as_view(), name="sync_import"),
    # 备份恢复
    path("backup/", backup_views.BackupListView.as_view(), name="backup_list"),
    path("backup/create/", backup_views.BackupCreateView.as_view(), name="backup_create"),
    path("backup/<str:filename>/restore/", backup_views.BackupRestoreView.as_view(), name="backup_restore"),
    path("backup/<str:filename>/download/", backup_views.BackupDownloadView.as_view(), name="backup_download"),
    path("backup/<str:filename>/delete/", backup_views.BackupDeleteView.as_view(), name="backup_delete"),
    # 异步任务进度
    path("task/<int:task_id>/status/", task_views.task_status, name="task_status"),
    path("task/<int:task_id>/cancel/", task_views.task_cancel, name="task_cancel"),
    path("task/<int:task_id>/retry/", task_views.task_retry, name="task_retry"),
]
