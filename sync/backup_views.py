"""数据库备份恢复 Web 界面"""
import shutil
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.shortcuts import redirect
from django.views.generic import ListView, View


def _backup_dir():
    d = Path(settings.BASE_DIR) / "backups"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _list_backups():
    backups = []
    for f in sorted(_backup_dir().glob("db_*.sqlite3"), reverse=True):
        backups.append({
            "filename": f.name,
            "size_mb": f.stat().st_size / 1024 / 1024,
            "mtime": datetime.fromtimestamp(f.stat().st_mtime),
        })
    return backups


class BackupListView(LoginRequiredMixin, ListView):
    template_name = "sync/backup_list.html"
    context_object_name = "backups"

    def get_queryset(self):
        # 获取当前数据库大小
        db_path = settings.DATABASES["default"]["NAME"]
        db_size = Path(db_path).stat().st_size / 1024 / 1024 if Path(db_path).exists() else 0
        self.db_size = db_size
        return _list_backups()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["db_size_mb"] = f"{self.db_size:.1f}"
        return ctx


class BackupCreateView(LoginRequiredMixin, View):
    def post(self, request):
        db_path = settings.DATABASES["default"]["NAME"]
        if isinstance(db_path, Path):
            db_path = str(db_path)

        if not Path(db_path).exists():
            messages.error(request, "数据库文件不存在")
            return redirect("sync:backup_list")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = _backup_dir() / f"db_{ts}.sqlite3"
        shutil.copy2(str(db_path), str(out_path))
        size_mb = out_path.stat().st_size / 1024 / 1024
        messages.success(request, f"备份完成: {out_path.name} ({size_mb:.1f} MB)")
        return redirect("sync:backup_list")


class BackupRestoreView(LoginRequiredMixin, View):
    def post(self, request, filename):
        src = _backup_dir() / filename
        if not src.exists():
            raise Http404("备份文件不存在")

        db_path = settings.DATABASES["default"]["NAME"]
        if isinstance(db_path, Path):
            db_path = str(db_path)
        db_path = Path(db_path)

        # 恢复前自动备份当前数据库
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if db_path.exists():
            shutil.copy2(str(db_path), str(_backup_dir() / f"pre_restore_{ts}.sqlite3"))

        shutil.copy2(str(src), str(db_path))
        messages.success(request, f"已从 {filename} 恢复数据库")
        return redirect("sync:backup_list")


class BackupDownloadView(LoginRequiredMixin, View):
    def get(self, request, filename):
        src = _backup_dir() / filename
        if not src.exists():
            raise Http404("备份文件不存在")
        return FileResponse(open(src, "rb"), as_attachment=True, filename=filename)


class BackupDeleteView(LoginRequiredMixin, View):
    def post(self, request, filename):
        src = _backup_dir() / filename
        if src.exists():
            src.unlink()
            messages.success(request, f"已删除备份: {filename}")
        return redirect("sync:backup_list")
