"""数据库恢复命令"""
import shutil
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "从备份文件恢复 SQLite 数据库"

    def add_arguments(self, parser):
        parser.add_argument("backup_file", nargs="?", help="备份文件路径")
        parser.add_argument("--list", action="store_true", help="列出所有备份")
        parser.add_argument("--force", action="store_true", help="强制恢复，不确认")

    def handle(self, *args, **options):
        backup_dir = Path(settings.BASE_DIR) / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        if options["list"]:
            self.list_backups(backup_dir)
            return

        # 获取目标数据库路径
        db_path = settings.DATABASES["default"]["NAME"]
        if isinstance(db_path, Path):
            db_path = str(db_path)
        db_path = Path(db_path)

        # 确定要恢复的备份文件
        if options["backup_file"]:
            src = Path(options["backup_file"])
            if not src.exists():
                src = backup_dir / options["backup_file"]
        else:
            # 默认使用最新的备份
            backups = sorted(backup_dir.glob("db_*.sqlite3"), reverse=True)
            if not backups:
                self.stderr.write("没有找到备份文件")
                return
            src = backups[0]

        if not src.exists():
            self.stderr.write(f"备份文件不存在: {src}")
            return

        size_mb = src.stat().st_size / 1024 / 1024
        self.stdout.write(f"将从备份恢复: {src.name} ({size_mb:.1f} MB)")

        if not options["force"]:
            confirm = input(f"确定要覆盖当前数据库 {db_path} 吗？(yes/no): ")
            if confirm.lower() not in ("yes", "y"):
                self.stdout.write("已取消")
                return

        # 恢复前先自动备份当前数据库
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        auto_backup = backup_dir / f"pre_restore_{ts}.sqlite3"
        if db_path.exists():
            shutil.copy2(str(db_path), str(auto_backup))
            self.stdout.write(f"已自动备份当前数据库: {auto_backup}")

        # 执行恢复
        shutil.copy2(str(src), str(db_path))
        self.stdout.write(f"恢复完成: {src.name} -> {db_path}")
        self.stdout.write("请重启应用使新数据库生效")

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
