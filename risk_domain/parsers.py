def parse_domain_line(line: str) -> dict | None:
    """解析单行域名数据，返回标准结构或 None（跳过）"""
    line = line.strip()
    if not line or line.startswith("#") or line.startswith("//"):
        return None

    prefix_at = False
    if line.startswith("@"):
        prefix_at = True
        line = line[1:]

    # 去除协议前缀
    if line.startswith(("http://", "https://")):
        from urllib.parse import urlparse
        parsed = urlparse(line)
        line = parsed.hostname or line

    # 去除路径
    if "/" in line:
        line = line.split("/")[0]

    if not line or "." not in line:
        return None

    return {"domain": line.lower(), "prefix_at": prefix_at}


def parse_txt_file(content: str) -> list[dict]:
    """解析 .txt 文件全部内容，返回解析结果列表"""
    results = []
    for line in content.splitlines():
        parsed = parse_domain_line(line)
        if parsed:
            results.append(parsed)
    return results
