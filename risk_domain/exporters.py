from .models import MaliciousDomain


def export_txt_file(queryset=None) -> str:
    """将 MaliciousDomain 查询集导出为 .txt 格式"""
    if queryset is None:
        queryset = MaliciousDomain.objects.filter(is_active=True)

    lines = [
        "# 域名组导出 - SecRiskManager",
        "# 生成时间: Auto",
        f"# 共 {queryset.count()} 条",
        "",
    ]

    for obj in queryset:
        prefix = "@" if obj.prefix_at else ""
        lines.append(f"{prefix}{obj.domain}")

    return "\n".join(lines) + "\n"
