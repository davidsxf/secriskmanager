def parse_asset_line(line: str) -> dict | None:
    """解析 ipmacdesc.conf 一行"""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    parts = line.split(None, 4)  # 最多分 5 段
    if len(parts) < 2:
        return None
    ip = parts[0]
    mac = parts[1] if parts[1] != "0" else ""
    # 格式1: <IP> <MAC> 0 NULL <person_name>  (5段)
    # 格式2: <IP> 0 NULL <person_name>         (4段, MAC为空)
    # 格式3: <IP> <person_name>                (2段, 仅IP+姓名)
    if len(parts) >= 5:
        person_name = parts[4]
    elif len(parts) >= 4:
        person_name = parts[3]
    elif len(parts) >= 2:
        person_name = parts[1]
        mac = ""
    else:
        person_name = ""
    return {"ip": ip, "mac": mac, "person_name": person_name}


def parse_conf_file(content: str) -> list[dict]:
    results = []
    for line in content.splitlines():
        parsed = parse_asset_line(line)
        if parsed:
            results.append(parsed)
    return results
