"""数据库备份命令"""
import shutil
from datetime import datetime
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "备份 SQLite 数据库到备份目录"

    def add_arguments(self, parser):
        parser.add_argument("--output", "-o", help="备份文件路径，默认 backups/db_YYYYMMDD_HHMMSS.sqlite3")
        parser.add_argument("--list", action="store_true", help="列出所有备份")

    def handle(self, *args, **options):
        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        if options["list"]:
            self.list_backups(backup_dir)
            return

        # 获取数据库路径
        db_path = settings.DATABASES["default"]["NAME"]
        if isinstance(db_path, Path):
            db_path = str(db_path)
        db_path = Path(db_path)

        if not db_path.exists():
            self.stderr.write(f"数据库文件不存在: {db_path}")
            return

        # 确定输出路径
        if options["output"]:
            out_path = Path(options["output"])
        else:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = backup_dir / f"db_{ts}.sqlite3"

        # 执行备份
        shutil.copy2(str(db_path), str(out_path))
        size_mb = out_path.stat().st_size / 1024 / 1024
        self.stdout.write(f"备份完成: {out_path} ({size_mb:.1f} MB)")

    def list_backups(self, backup_dir):
        backups = sorted(backup_dir.glob("db_*.sqlite3"), reverse=True)
        if not backups:
            self.stdout.write("暂无备份")
            return
        self.stdout.write(f"共 {len(backups)} 个备份:")
        for b in backups:
            ts = datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            size = b.stat().st_size / 1024 / 1024
            self.stdout.write(f"  {b.name}  ({size:.1f} MB)  {ts}")
