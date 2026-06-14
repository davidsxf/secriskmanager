"""预置 14 个开源威胁情报源"""
from django.db import migrations

FEEDS = [
    {
        "name": "Spamhaus DROP",
        "slug": "spamhaus_drop",
        "feed_type": "ip",
        "url": "https://www.spamhaus.org/drop/drop.txt",
        "format": "text",
        "auth_type": "none",
        "interval_minutes": 1440,
        "confidence_base": 90,
        "category_default": "spamhaus",
        "description": "Spamhaus DROP (Don't Route Or Peer) 列表，权威的恶意 IP 黑名单，CIDR 格式，附带 SBL 编号。每日更新。",
    },
    {
        "name": "Spamhaus EDROP",
        "slug": "spamhaus_edrop",
        "feed_type": "ip",
        "url": "https://www.spamhaus.org/drop/edrop.txt",
        "format": "text",
        "auth_type": "none",
        "interval_minutes": 1440,
        "confidence_base": 85,
        "category_default": "spamhaus",
        "description": "Spamhaus EDROP 扩展列表，DROP 的补充。",
    },
    {
        "name": "Blocklist.de ALL",
        "slug": "blocklist_de_all",
        "feed_type": "ip",
        "url": "https://lists.blocklist.de/lists/all.txt",
        "format": "text",
        "auth_type": "none",
        "interval_minutes": 30,
        "confidence_base": 60,
        "category_default": "blocklist_de",
        "description": "Blocklist.de 全部攻击 IP（最近 48 小时），含 SSH/Mail/Apache 等子分类。每 30 分钟更新。",
    },
    {
        "name": "Blocklist.de SSH",
        "slug": "blocklist_de_ssh",
        "feed_type": "ip",
        "url": "https://lists.blocklist.de/lists/ssh.txt",
        "format": "text",
        "auth_type": "none",
        "interval_minutes": 30,
        "confidence_base": 65,
        "category_default": "ssh_bruteforce",
        "description": "Blocklist.de SSH 暴力破解攻击 IP。",
    },
    {
        "name": "Greensnow",
        "slug": "greensnow",
        "feed_type": "ip",
        "url": "https://blocklist.greensnow.co/greensnow.txt",
        "format": "text",
        "auth_type": "none",
        "interval_minutes": 1440,
        "confidence_base": 70,
        "category_default": "scanner",
        "description": "Greensnow 恶意扫描/攻击 IP 黑名单。每日更新。",
    },
    {
        "name": "Tor Exit Nodes",
        "slug": "tor_exit_nodes",
        "feed_type": "ip",
        "url": "https://check.torproject.org/torbulkexitlist",
        "format": "text",
        "auth_type": "none",
        "interval_minutes": 120,
        "confidence_base": 50,
        "category_default": "tor",
        "description": "Tor 出口节点列表。每 2 小时更新。",
    },
    {
        "name": "Feodo Tracker (IPs)",
        "slug": "feodo_tracker",
        "feed_type": "ip",
        "url": "https://feodotracker.abuse.ch/downloads/ipblocklist.txt",
        "format": "text",
        "auth_type": "none",
        "interval_minutes": 5,
        "confidence_base": 85,
        "category_default": "botnet_c2",
        "description": "Feodo Tracker Botnet C2 IP 列表（Dridex/Emotet/TrickBot）。每 5 分钟更新。",
    },
    {
        "name": "SSL Blacklist",
        "slug": "ssl_blacklist",
        "feed_type": "ip",
        "url": "https://sslbl.abuse.ch/blacklist/sslblacklist.csv",
        "format": "csv",
        "auth_type": "none",
        "interval_minutes": 5,
        "confidence_base": 80,
        "category_default": "ssl_malware",
        "description": "abuse.ch SSL Blacklist — 恶意 SSL 证书关联的 IP。每 5 分钟更新。",
    },
    {
        "name": "AbuseIPDB Blacklist",
        "slug": "abuseipdb",
        "feed_type": "ip",
        "url": "https://api.abuseipdb.com/api/v2/blacklist",
        "format": "text",
        "auth_type": "api_key",
        "interval_minutes": 1440,
        "confidence_base": 75,
        "category_default": "abuseipdb",
        "description": "AbuseIPDB 黑名单。需注册免费 API Key 并填入 auth_key 字段。每日更新。",
    },
    {
        "name": "AlienVault OTX",
        "slug": "alienvault_otx",
        "feed_type": "mixed",
        "url": "https://otx.alienvault.com/api/v1/indicators/export",
        "format": "json",
        "auth_type": "api_key",
        "interval_minutes": 1440,
        "confidence_base": 70,
        "category_default": "alienvault",
        "description": "AlienVault OTX (Open Threat Exchange) — IP+域名 威胁情报。需注册免费 API Key。",
    },
    {
        "name": "ThreatFox",
        "slug": "threatfox",
        "feed_type": "mixed",
        "url": "https://threatfox-api.abuse.ch/v2/files/exports/",
        "format": "json",
        "auth_type": "api_key",
        "interval_minutes": 5,
        "confidence_base": 85,
        "category_default": "threatfox",
        "description": "ThreatFox (abuse.ch) — 恶意软件 IOC 共享平台。需注册免费 Auth-Key。每 5 分钟更新。",
    },
    {
        "name": "FireHOL Level 1",
        "slug": "firehol_level1",
        "feed_type": "ip",
        "url": "https://raw.githubusercontent.com/ktsaou/blocklist-ipsets/master/firehol_level1.netset",
        "format": "text",
        "auth_type": "none",
        "interval_minutes": 1440,
        "confidence_base": 80,
        "category_default": "firehol",
        "description": "FireHOL Level 1 — 精选聚合 IP 黑名单，低误报率。每日更新。",
    },
    {
        "name": "FireHOL Level 2",
        "slug": "firehol_level2",
        "feed_type": "ip",
        "url": "https://raw.githubusercontent.com/ktsaou/blocklist-ipsets/master/firehol_level2.netset",
        "format": "text",
        "auth_type": "none",
        "interval_minutes": 1440,
        "confidence_base": 65,
        "category_default": "firehol",
        "description": "FireHOL Level 2 — 包含 Level 1 及更多来源的聚合 IP 黑名单。每日更新。",
    },
    {
        "name": "FireHOL WebServer",
        "slug": "firehol_webserver",
        "feed_type": "ip",
        "url": "https://raw.githubusercontent.com/ktsaou/blocklist-ipsets/master/firehol_webserver.netset",
        "format": "text",
        "auth_type": "none",
        "interval_minutes": 1440,
        "confidence_base": 70,
        "category_default": "web_attack",
        "description": "FireHOL WebServer — Web 攻击相关 IP 黑名单。每日更新。",
    },
]


def add_default_feeds(apps, schema_editor):
    SourceFeed = apps.get_model("sync", "SourceFeed")
    for data in FEEDS:
        SourceFeed.objects.get_or_create(
            slug=data["slug"],
            defaults={
                "name": data["name"],
                "feed_type": data["feed_type"],
                "url": data["url"],
                "format": data["format"],
                "auth_type": data["auth_type"],
                "interval_minutes": data["interval_minutes"],
                "confidence_base": data["confidence_base"],
                "category_default": data["category_default"],
                "description": data["description"],
                "is_active": False,  # 默认不启用，用户手动开启
            },
        )


def remove_default_feeds(apps, schema_editor):
    SourceFeed = apps.get_model("sync", "SourceFeed")
    SourceFeed.objects.filter(slug__in=[f["slug"] for f in FEEDS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("sync", "0002_taskprogress"),
    ]

    operations = [
        migrations.RunPython(add_default_feeds, remove_default_feeds),
    ]
