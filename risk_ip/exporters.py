from .models import MaliciousIP


def export_conf_file(queryset=None) -> str:
    """将 MaliciousIP 查询集导出为 .conf 格式文本"""
    if queryset is None:
        queryset = MaliciousIP.objects.filter(is_active=True)

    lines = [
        "# 差异导出: 系统风险库中存在但设备尚未配置",
        "# 生成时间: Auto",
        f"# 共 {queryset.count()} 条",
        "",
    ]

    for obj in queryset:
        if obj.ip_address:
            lines.append(obj.ip_address)
        elif obj.cidr:
            lines.append(obj.cidr)
        elif obj.range_start and obj.range_end:
            lines.append(f"{obj.range_start}-{obj.range_end}")

    return "\n".join(lines) + "\n"
