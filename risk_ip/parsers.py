import ipaddress
from typing import Iterator


def parse_ip_line(line: str) -> dict | None:
    """解析单行 IP 数据，返回标准结构或 None（跳过）"""
    line = line.strip()
    if not line or line.startswith("#") or line.startswith(";"):
        return None

    # 去掉行尾注释（Spamhaus 格式: "1.1.1.0/24 ; SBL12345"）
    if ";" in line:
        line = line.split(";", 1)[0].strip()

    # CIDR
    if "/" in line:
        try:
            network = ipaddress.ip_network(line, strict=False)
            if network.is_private:
                return None
            return {"type": "cidr", "cidr": str(network)}
        except ValueError:
            return None

    # 范围
    if "-" in line:
        parts = line.split("-", 1)
        try:
            ip_start = ipaddress.ip_address(parts[0].strip())
            ip_end = ipaddress.ip_address(parts[1].strip())
            return {"type": "range", "range_start": str(ip_start), "range_end": str(ip_end)}
        except ValueError:
            return None

    # 单 IP
    try:
        ip = ipaddress.ip_address(line)
        if ip.is_private:
            return None
        return {"type": "single", "ip": str(ip)}
    except ValueError:
        return None


def parse_conf_file(content: str) -> list[dict]:
    """解析 .conf 文件全部内容，返回解析结果列表"""
    results = []
    for line in content.splitlines():
        parsed = parse_ip_line(line)
        if parsed:
            results.append(parsed)
    return results
