from .models import LocalAsset


def export_conf_file(queryset=None) -> str:
    """将资产导出为 ipmacdesc.conf 格式"""
    if queryset is None:
        queryset = LocalAsset.objects.all()

    lines = []
    for obj in queryset:
        mac = obj.mac_address if obj.mac_address else "0"
        name = obj.person_name or obj.hostname or "-"
        lines.append(f"{obj.ip_address} {mac} 0 NULL {name}")
    return "\n".join(lines) + "\n"
