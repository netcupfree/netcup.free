#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Netcup Voucher Code Synchronization Script
Automatically fetches verified coupons from the netcup.free API (or fallback to pages API)
and generates multi-language Markdown documents for GitHub.
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
import urllib.request

API_URL = os.getenv("WEBSITE_API_URL", "https://netcup.free/api/coupons")
FALLBACK_API_URL = "https://netcup.free/api/wp-json/pages?id=1"
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://netcup.free")
REF_CODE = os.getenv("AFF_REF_CODE", "257842")

TAG_DEFINITIONS = [
    ("5e", "discount", "5 Euro General Voucher (Save 5 €)", "5 Euro 通用优惠券 (立减 5 欧元)", "5 Euro Universalgutschein (5 € Rabatt)", "Save 5€ directly on your first Netcup registration order"),
    ("rs500", "rs", "Root Server 500 G12.5 (5 € Discount)", "Root Server 500 G12.5 (立减 5 欧元)", "Root Server 500 G12.5 (5 € Rabatt)", "Dedicated AMD EPYC 9645 starter dedicated server"),
    ("rs1", "rs", "Root Server 1000 G12.5 (2 Months Free)", "Root Server 1000 G12.5 (免费 2 个月)", "Root Server 1000 G12.5 (2 Monate gratis)", "Dedicated CPU cores & high performance guarantee"),
    ("rs2", "rs", "Root Server 2000 G12.5 (1 Month Free)", "Root Server 2000 G12.5 (免费 1 个月)", "Root Server 2000 G12.5 (1 Monat gratis)", "High performance production environment for apps"),
    ("rs4", "rs", "Root Server 4000 G12.5 (5 € Discount)", "Root Server 4000 G12.5 (立减 5 欧元)", "Root Server 4000 G12.5 (5 € Rabatt)", "Extreme computing power with large NVMe storage"),
    ("rs8", "rs", "Root Server 8000 G12.5 (1 Month Free)", "Root Server 8000 G12.5 (免费 1 个月)", "Root Server 8000 G12.5 (1 Monat gratis)", "Flagship multi-core dedicated server specs"),
    ("vps500", "vps", "VPS 500 G12.5 (5 € Discount)", "VPS 500 G12.5 (立减 5 欧元)", "VPS 500 G12.5 (5 € Rabatt)", "Best budget starter VPS for personal websites"),
    ("vps1", "vps", "VPS 1000 G12.5 (1 Month Free)", "VPS 1000 G12.5 (免费 1 个月)", "VPS 1000 G12.5 (1 Monat gratis)", "Best value VPS for web applications"),
    ("vps2", "vps", "VPS 2000 G12.5 (1 Month Free)", "VPS 2000 G12.5 (免费 1 个月)", "VPS 2000 G12.5 (1 Monat gratis)", "Balanced resource allocation for dev testing"),
    ("vps4", "vps", "VPS 4000 G12.5 (1 Month Free)", "VPS 4000 G12.5 (免费 1 个月)", "VPS 4000 G12.5 (1 Monat gratis)", "Multi-core & large memory for high traffic websites"),
    ("vps8", "vps", "VPS 8000 G12.5 (1 Month Free)", "VPS 8000 G12.5 (免费 1 个月)", "VPS 8000 G12.5 (1 Monat gratis)", "Large specification VPS for resource-intensive workloads"),
    ("w2", "hosting", "Webhosting 2000 (30% Lifetime Off)", "Webhosting 2000 (永久 30% 优惠)", "Webhosting 2000 (30% Dauerhaft Rabatt)", "Managed shared web hosting with included free domain"),
    ("w4", "hosting", "Webhosting 4000 (30% Lifetime Off)", "Webhosting 4000 (永久 30% 优惠)", "Webhosting 4000 (30% Dauerhaft Rabatt)", "Advanced web hosting with large storage capacity"),
    ("w8", "hosting", "Webhosting 8000 (30% Lifetime Off)", "Webhosting 8000 (永久 30% 优惠)", "Webhosting 8000 (30% Dauerhaft Rabatt)", "Flagship managed web hosting for enterprise workloads"),
]

CATEGORY_MAPPING_EN = {
    "discount": "General Discounts (€5.00 Voucher)",
    "rs": "Root Servers (RS G12.5 - Dedicated AMD EPYC Cores)",
    "vps": "VPS (Virtual Private Servers - G12.5)",
    "hosting": "Web Hosting (Shared SSD Hosting + Free Domain)"
}

CATEGORY_MAPPING_ZH = {
    "discount": "通用折扣券 (新人立减 5 欧元)",
    "rs": "Root Server 独立核心服务器 (G12.5 代独享核心)",
    "vps": "VPS 云服务器 (G12.5 代 AMD EPYC 9645)",
    "hosting": "Webhosting 虚拟主机 (免税 + 赠免费顶级域名)"
}

CATEGORY_MAPPING_DE = {
    "discount": "Allgemeine Gutscheine (5 € Neukundengutschein)",
    "rs": "Root Server (RS G12.5 - Dedizierte CPU)",
    "vps": "vServer (VPS G12.5)",
    "hosting": "Webhosting (Inklusivdomain & SSD)"
}

def get_current_time_display(last_sync_str=None):
    dt = None
    if last_sync_str:
        try:
            clean = str(last_sync_str).strip()
            # Handle UTC strings like 2026-09-11T05:00:06.697Z
            if clean.endswith('Z'):
                clean = clean[:-1] + '+00:00'
            elif ' ' in clean and not 'T' in clean:
                clean = clean.replace(' ', 'T') + '+00:00'
            parsed = datetime.fromisoformat(clean)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            dt = parsed
        except Exception as e:
            print(f"Failed to parse last_sync_str '{last_sync_str}': {e}")
            dt = None

    if not dt:
        dt = datetime.now(timezone.utc)

    utc_time = dt.astimezone(timezone.utc)
    bj_time = dt.astimezone(timezone(timedelta(hours=8)))
    de_time = dt.astimezone(timezone(timedelta(hours=2))) # CEST / MESZ

    return {
        "en": f"`{utc_time.strftime('%Y-%m-%d %H:%M:%S UTC')}` | `{bj_time.strftime('%H:%M:%S CST (UTC+8)')}` | `{de_time.strftime('%H:%M:%S CEST (UTC+2)')}`",
        "zh": f"`{bj_time.strftime('%Y-%m-%d %H:%M:%S 北京时间 (UTC+8)')}` | `{de_time.strftime('%H:%M:%S 德国时间 (UTC+2)')}`",
        "de": f"`{de_time.strftime('%Y-%m-%d %H:%M:%S MESZ (Deutschland)')}` | `{utc_time.strftime('%H:%M:%S UTC')}`"
    }

def fetch_coupons_from_main_api():
    print(f"Trying primary API: {API_URL}")
    req = urllib.request.Request(API_URL, headers={'User-Agent': 'NetcupFree-SyncBot/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data.get("success") and data.get("coupons"):
                    return data
    except Exception as e:
        print(f"Primary API not reachable or 404: {e}")
    return None

def fetch_coupons_from_pages_api():
    print(f"Falling back to pages API: {FALLBACK_API_URL}")
    req = urllib.request.Request(FALLBACK_API_URL, headers={'User-Agent': 'NetcupFree-SyncBot/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                page_data = json.loads(response.read().decode('utf-8'))
                html = page_data.get('content', {}).get('raw', '')
                if not html:
                    return None
                
                # Parse HTML content into structured coupons
                parsed_coupons = []
                for tag_id, cat, title_en, title_zh, title_de, desc in TAG_DEFINITIONS:
                    # Look for codes between current tag and next tag or end of HTML
                    tag_match = re.search(r'id=["\']' + re.escape(tag_id) + r'["\']([\s\S]*?)(?:<div\s+id=|$)', html, re.IGNORECASE)
                    codes = []
                    if tag_match:
                        raw_codes = re.findall(r'\b\d+nc\d+\b', tag_match.group(1))
                        # Deduplicate while preserving order
                        seen = set()
                        for c in raw_codes:
                            if c not in seen:
                                seen.add(c)
                                codes.append(c)
                    
                    parsed_coupons.append({
                        "id": tag_id,
                        "tag": tag_id.upper(),
                        "category": cat,
                        "title": title_en,
                        "title_zh": title_zh,
                        "title_de": title_de,
                        "desc": desc,
                        "codes": codes
                    })
                
                return {
                    "success": True,
                    "coupons": parsed_coupons,
                    "last_sync_display": None
                }
    except Exception as e:
        print(f"Pages API fallback failed: {e}")
        return None

def write_english_readme(coupons, time_display_str):
    md = [
        "🌐 **Select Language:** English | [简体中文](README_ZH.md) | [Deutsch](README_DE.md)\n",
        "# ⚡ Verified Netcup Coupons & Voucher Codes",
        "> 🏷️ Curated and real-time verified Netcup voucher codes. Synchronized directly with [netcup.free](https://netcup.free).\n",
        f"⏰ **Last Updated:** {time_display_str}\n",
        "## 🛒 How to Redeem",
        f"- 🇩🇪 **German Checkout:** [https://www.netcup.com/de/checkout/warenkorb](https://www.netcup.com/de/checkout/warenkorb?ref={REF_CODE})",
        f"- 🇬🇧 **English Checkout:** [https://www.netcup.com/en/checkout/cart](https://www.netcup.com/en/checkout/cart?ref={REF_CODE})",
        f"- 🌐 **Live Website:** Visit [{WEBSITE_URL.replace('https://', '')}]({WEBSITE_URL}) for real-time coupon verification, instant copy, and server benchmarks.\n",
        "## 🎟️ Available Voucher Codes\n"
    ]

    for cat_key, cat_name in CATEGORY_MAPPING_EN.items():
        items = [c for c in coupons if c.get("category") == cat_key]
        if not items or not any(item.get("codes") for item in items):
            continue
        md.append(f"### {cat_name}\n")
        for item in items:
            codes = item.get("codes", [])
            if not codes:
                continue
            title = item.get("title", "")
            desc = item.get("desc", "")
            md.append(f"- **{title}**" + (f" - *{desc}*" if desc else ""))
            for code in codes:
                direct_url = f"https://www.netcup.com/en/checkout/cart?gutschein={code}&ref={REF_CODE}"
                md.append(f"  - [`{code}`]({direct_url}) *(Click code to redeem directly)*")
        md.append("")

    md.extend([
        "## 🚀 Hardware Specifications (Netcup G12.5 Generation)",
        "Netcup G12.5 instances feature AMD EPYC™ 9645 enterprise processors with DDR5 ECC memory, enterprise NVMe/SSD storage, and 2.5 Gbps bandwidth.\n",
        "### Root Server G12.5 (Dedicated AMD EPYC™ 9645 Cores)",
        "| Plan | CPU / vCores | RAM (DDR5 ECC) | NVMe Storage | Bandwidth | 0% VAT Price (12m) | 19% VAT Price | Direct Link |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| RS 500 G12.5 | 2 Dedicated Cores | 4 GB | 64 GB | 2.5 Gbps | €10.86/mo | €12.92/mo | [View Plan](https://www.netcup.com/en/server/root-server/rs-500-g12.5-iv-24m-eu#rs-500-g12.5-iv-12m-eu) |",
        f"| RS 1000 G12.5 | 4 Dedicated Cores | 8 GB | 128 GB | 2.5 Gbps | €18.26/mo | €21.73/mo | [View Plan](https://www.netcup.com/en/server/root-server/rs-1000-g12.5-iv-24m-eu#rs-1000-g12.5-iv-12m-eu) |",
        f"| RS 2000 G12.5 | 8 Dedicated Cores | 16 GB | 256 GB | 2.5 Gbps | €34.20/mo | €40.70/mo | [View Plan](https://www.netcup.com/en/server/root-server/rs-2000-g12.5-iv-24m-eu#rs-2000-g12.5-iv-12m-eu) |",
        f"| RS 4000 G12.5 | 12 Dedicated Cores | 32 GB | 512 GB | 2.5 Gbps | €65.40/mo | €77.83/mo | [View Plan](https://www.netcup.com/en/server/root-server/rs-4000-g12.5-iv-24m-eu#rs-4000-g12.5-iv-12m-eu) |",
        f"| RS 8000 G12.5 | 16 Dedicated Cores | 64 GB | 1024 GB (1 TB) | 2.5 Gbps | €124.72/mo | €148.42/mo | [View Plan](https://www.netcup.com/en/server/root-server/rs-8000-g12.5-iv-24m-eu#rs-8000-g12.5-iv-12m-eu) |\n",
        "> 📌 ***Root Server Traffic Policy:*** *If traffic exceeds 3 TB within the last 24 hours, a temporary throttling to 300 Mbit/s will be applied. The throttling is lifted as soon as this condition no longer applies.*\n",
        "### VPS G12.5 (High Performance Cloud Cores, AMD EPYC™ 9645)",
        "| Plan | vCores | RAM (DDR5 ECC) | SSD Storage | Bandwidth | 0% VAT Price (12m) | 19% VAT Price | Direct Link |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| VPS 500 G12.5 | 2 vCores | 4 GB | 64 GB | 2.5 Gbps | €6.94/mo | €8.26/mo | [View Plan](https://www.netcup.com/en/server/vps/vps-500-g12.5-iv-24m-eu#vps-500-g12.5-iv-12m-eu) |",
        f"| VPS 1000 G12.5 | 4 vCores | 8 GB | 128 GB | 2.5 Gbps | €12.18/mo | €14.49/mo | [View Plan](https://www.netcup.com/en/server/vps/vps-1000-g12.5-iv-24m-eu#vps-1000-g12.5-iv-12m-eu) |",
        f"| VPS 2000 G12.5 | 8 vCores | 16 GB | 256 GB | 2.5 Gbps | €22.62/mo | €26.92/mo | [View Plan](https://www.netcup.com/en/server/vps/vps-2000-g12.5-iv-24m-eu#vps-2000-g12.5-iv-12m-eu) |",
        f"| VPS 4000 G12.5 | 12 vCores | 32 GB | 512 GB | 2.5 Gbps | €38.11/mo | €45.35/mo | [View Plan](https://www.netcup.com/en/server/vps/vps-4000-g12.5-iv-24m-eu#vps-4000-g12.5-iv-12m-eu) |",
        f"| VPS 8000 G12.5 | 16 vCores | 64 GB | 1024 GB (1 TB) | 2.5 Gbps | €56.39/mo | €67.10/mo | [View Plan](https://www.netcup.com/en/server/vps/vps-8000-g12.5-iv-24m-eu#vps-8000-g12.5-iv-12m-eu) |\n",
        "> 📌 ***VPS Traffic Policy:*** *If traffic exceeds 2 TB within the last 24 hours, a temporary throttling to 200 Mbit/s will be applied. The throttling is lifted as soon as this condition no longer applies.*\n",
        "## ❓ FAQ",
        "**Q: Are these voucher codes free?**  ",
        "A: Yes, absolutely 100% free. Simply click on a code to copy and apply it to your cart.\n",
        "**Q: Can I combine multiple vouchers?**  ",
        "A: Netcup allows only one coupon code per single order.\n",
        "**Q: What if all codes are taken?**  ",
        f"A: New vouchers are added automatically. Visit [{WEBSITE_URL.replace('https://', '')}]({WEBSITE_URL}) to fetch newly generated codes.\n",
        "---\n",
        "*(This repository is synchronized in real-time with netcup.free. Vouchers are single-use!)*\n"
    ])

    with open("README.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("README.md written successfully.")

def write_chinese_readme(coupons, time_display_str):
    md = [
        "🌐 **语言切换:** [English](README.md) | 简体中文 | [Deutsch](README_DE.md)\n",
        "# ⚡ Netcup 优惠码与折扣券实时集合",
        "> 🏷️ 经过自动实时验证的 Netcup 优惠码集合，与 [netcup.free](https://netcup.free) 网站保持完全同步更新。\n",
        f"⏰ **最后更新时间:** {time_display_str}\n",
        "## 🛒 快捷兑换通道",
        f"- 🇩🇪 **德语结账购物车:** [netcup.com/de/checkout/warenkorb](https://www.netcup.com/de/checkout/warenkorb?ref={REF_CODE})",
        f"- 🇬🇧 **英语结账购物车:** [netcup.com/en/checkout/cart](https://www.netcup.com/en/checkout/cart?ref={REF_CODE})",
        f"- 🌐 **在线实时网站:** 访问 [{WEBSITE_URL.replace('https://', '')}]({WEBSITE_URL}) 查看实时库存检测、测速与综合对比工具。\n",
        "## 🎟️ 当前可用优惠券\n"
    ]

    for cat_key, cat_name in CATEGORY_MAPPING_ZH.items():
        items = [c for c in coupons if c.get("category") == cat_key]
        if not items or not any(item.get("codes") for item in items):
            continue
        md.append(f"### {cat_name}\n")
        for item in items:
            codes = item.get("codes", [])
            if not codes:
                continue
            title = item.get("title_zh") or item.get("title") or ""
            desc = item.get("desc", "")
            md.append(f"- **{title}**" + (f" - *{desc}*" if desc else ""))
            for code in codes:
                direct_url = f"https://www.netcup.com/en/checkout/cart?gutschein={code}&ref={REF_CODE}"
                md.append(f"  - [`{code}`]({direct_url}) *(点击自动填入购物车)*")
        md.append("")

    md.extend([
        "## 🚀 硬件配置参数表 (Netcup G12.5 代 AMD EPYC™ 9645)",
        "Netcup 最新 G12.5 代全系产品均搭载 AMD 顶级 EPYC™ 9645 处理器、DDR5 ECC 内存与高速 NVMe/SSD 固态硬盘，且 VPS 与 Root Server 均提供高达 2.5 Gbps 高速带宽：\n",
        "### Root Server G12.5 (独享独立核心 - 强劲算力保证)",
        "| 型号规格 | 独立 CPU 核心 | 内存 (DDR5 ECC) | NVMe 存储 | 免税价格(12月合约) | 含税价格(19% VAT) | 官方直达 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| RS 500 G12.5 | 2 独享核心 | 4 GB | 64 GB | €10.86/月 | €12.92/月 | [立即查看](https://www.netcup.com/en/server/root-server/rs-500-g12.5-iv-24m-eu#rs-500-g12.5-iv-12m-eu) |",
        f"| RS 1000 G12.5 | 4 独享核心 | 8 GB | 128 GB | €18.26/月 | €21.73/月 | [立即查看](https://www.netcup.com/en/server/root-server/rs-1000-g12.5-iv-24m-eu#rs-1000-g12.5-iv-12m-eu) |",
        f"| RS 2000 G12.5 | 8 独享核心 | 16 GB | 256 GB | €34.20/月 | €40.70/月 | [立即查看](https://www.netcup.com/en/server/root-server/rs-2000-g12.5-iv-24m-eu#rs-2000-g12.5-iv-12m-eu) |",
        f"| RS 4000 G12.5 | 12 独享核心 | 32 GB | 512 GB | €65.40/月 | €77.83/月 | [立即查看](https://www.netcup.com/en/server/root-server/rs-4000-g12.5-iv-24m-eu#rs-4000-g12.5-iv-12m-eu) |",
        f"| RS 8000 G12.5 | 16 独享核心 | 64 GB | 1024 GB (1 TB) | €124.72/月 | €148.42/月 | [立即查看](https://www.netcup.com/en/server/root-server/rs-8000-g12.5-iv-24m-eu#rs-8000-g12.5-iv-12m-eu) |\n",
        "> 📌 **Root Server 流量规则：** 若在过去的 24 小时内累计流量超过 3 TB，将临时限速至 300 Mbit/s。一旦过去 24 小时内的累计流量低于该阈值，限速将自动解除恢复（If traffic exceeds 3 TB within the last 24 hours, a temporary throttling to 300 Mbit/s will be applied. The throttling is lifted as soon as this condition no longer applies.）。\n",
        "### VPS G12.5 (超高性价比共享核心)",
        "| 型号规格 | 共享核心 | 内存 (DDR5 ECC) | SSD 存储 | 免税价格(12月合约) | 含税价格(19% VAT) | 官方直达 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| VPS 500 G12.5 | 2 核心 | 4 GB | 64 GB | €6.94/月 | €8.26/月 | [立即查看](https://www.netcup.com/en/server/vps/vps-500-g12.5-iv-24m-eu#vps-500-g12.5-iv-12m-eu) |",
        f"| VPS 1000 G12.5 | 4 核心 | 8 GB | 128 GB | €12.18/月 | €14.49/月 | [立即查看](https://www.netcup.com/en/server/vps/vps-1000-g12.5-iv-24m-eu#vps-1000-g12.5-iv-12m-eu) |",
        f"| VPS 2000 G12.5 | 8 核心 | 16 GB | 256 GB | €22.62/月 | €26.92/月 | [立即查看](https://www.netcup.com/en/server/vps/vps-2000-g12.5-iv-24m-eu#vps-2000-g12.5-iv-12m-eu) |",
        f"| VPS 4000 G12.5 | 12 核心 | 32 GB | 512 GB | €38.11/月 | €45.35/月 | [立即查看](https://www.netcup.com/en/server/vps/vps-4000-g12.5-iv-24m-eu#vps-4000-g12.5-iv-12m-eu) |",
        f"| VPS 8000 G12.5 | 16 核心 | 64 GB | 1024 GB (1 TB) | €56.39/月 | €67.10/月 | [立即查看](https://www.netcup.com/en/server/vps/vps-8000-g12.5-iv-24m-eu#vps-8000-g12.5-iv-12m-eu) |\n",
        "> 📌 **VPS 流量规则：** 若在过去的 24 小时内累计流量超过 2 TB，将临时限速至 200 Mbit/s。一旦过去 24 小时内的累计流量低于该阈值，限速将自动解除恢复（If traffic exceeds 2 TB within the last 24 hours, a temporary throttling to 200 Mbit/s will be applied. The throttling is lifted as soon as this condition no longer applies.）。\n",
        "## ❓ 常见问题 (FAQ)",
        "**Q: 优惠码是一次性的吗？**  ",
        "A: 是的，Netcup 官方发放的优惠码每个均为一次性使用，先到先得。本仓库会自动替换已被领取的失效券。\n",
        "**Q: 现有老客户可以使用吗？**  ",
        "A: 除 5 欧元新人通用券仅限首单外，RS、VPS 和 Webhosting 的免费月份或 30% 终身折扣券新老客户均可使用。\n",
        "**Q: 如果页面上的券都被用完了怎么办？**  ",
        f"A: 爬虫会定期自动补充，您也可以直接访问 [{WEBSITE_URL.replace('https://', '')}]({WEBSITE_URL}) 获取最新鲜出炉的有效码。\n",
        "---\n",
        "*(本 README 与 netcup.free 网站自动保持同步。优惠码均为一次性使用，请尽快兑换！)*\n"
    ])

    with open("README_ZH.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("README_ZH.md written successfully.")

def write_german_readme(coupons, time_display_str):
    md = [
        "🌐 **Sprache auswählen:** [English](README.md) | [简体中文](README_ZH.md) | Deutsch\n",
        "# ⚡ Verifizierte Netcup Gutscheine & Rabattcodes",
        "> 🏷️ Eine kuratierte Liste von aktiven Netcup Gutscheincodes. Automatisch synchronisiert mit [netcup.free](https://netcup.free).\n",
        f"⏰ **Zuletzt aktualisiert:** {time_display_str}\n",
        "## 🛒 Gutschein einlösen",
        f"- 🇩🇪 **Deutscher Warenkorb:** [https://www.netcup.com/de/checkout/warenkorb](https://www.netcup.com/de/checkout/warenkorb?ref={REF_CODE})",
        f"- 🇬🇧 **Englischer Warenkorb:** [https://www.netcup.com/en/checkout/cart](https://www.netcup.com/en/checkout/cart?ref={REF_CODE})",
        f"- 🌐 **Live-Website:** Besuchen Sie [{WEBSITE_URL.replace('https://', '')}]({WEBSITE_URL}) für Echtzeit-Verifikation und Tarifvergleiche.\n",
        "## 🎟️ Verfügbare Gutscheincodes\n"
    ]

    for cat_key, cat_name in CATEGORY_MAPPING_DE.items():
        items = [c for c in coupons if c.get("category") == cat_key]
        if not items or not any(item.get("codes") for item in items):
            continue
        md.append(f"### {cat_name}\n")
        for item in items:
            codes = item.get("codes", [])
            if not codes:
                continue
            title = item.get("title_de") or item.get("title") or ""
            desc = item.get("desc", "")
            md.append(f"- **{title}**" + (f" - *{desc}*" if desc else ""))
            for code in codes:
                direct_url = f"https://www.netcup.com/de/checkout/warenkorb?gutschein={code}&ref={REF_CODE}"
                md.append(f"  - [`{code}`]({direct_url}) *(Klicken zum Einlösen)*")
        md.append("")

    md.extend([
        "## 🚀 Technische Spezifikationen (Netcup G12.5 Generation)",
        "Netcup G12.5-Instanzen verfügen über AMD EPYC™ 9645 Enterprise-Prozessoren mit DDR5 ECC-Arbeitsspeicher, schnellem NVMe/SSD-Speicher und 2,5 GBit/s Bandbreite.\n",
        "### Root Server G12.5 (Dedizierte AMD EPYC™ 9645 Kerne)",
        "| Tarif | CPU / Kerne | RAM (DDR5 ECC) | NVMe Speicher | Bandbreite | Preis exkl. MwSt. | Preis inkl. 19% MwSt. | Link |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| RS 500 G12.5 | 2 Dedizierte Kerne | 4 GB | 64 GB | 2,5 GBit/s | 10,86 €/Monat | 12,92 €/Monat | [Details ansehen](https://www.netcup.de/server/root-server/rs-500-g12.5-iv-24m-eu#rs-500-g12.5-iv-12m-eu) |",
        f"| RS 1000 G12.5 | 4 Dedizierte Kerne | 8 GB | 128 GB | 2,5 GBit/s | 18,26 €/Monat | 21,73 €/Monat | [Details ansehen](https://www.netcup.de/server/root-server/rs-1000-g12.5-iv-24m-eu#rs-1000-g12.5-iv-12m-eu) |",
        f"| RS 2000 G12.5 | 8 Dedizierte Kerne | 16 GB | 256 GB | 2,5 GBit/s | 34,20 €/Monat | 40,70 €/Monat | [Details ansehen](https://www.netcup.de/server/root-server/rs-2000-g12.5-iv-24m-eu#rs-2000-g12.5-iv-12m-eu) |",
        f"| RS 4000 G12.5 | 12 Dedizierte Kerne | 32 GB | 512 GB | 2,5 GBit/s | 65,40 €/Monat | 77,83 €/Monat | [Details ansehen](https://www.netcup.de/server/root-server/rs-4000-g12.5-iv-24m-eu#rs-4000-g12.5-iv-12m-eu) |",
        f"| RS 8000 G12.5 | 16 Dedizierte Kerne | 64 GB | 1024 GB (1 TB) | 2,5 GBit/s | 124,72 €/Monat | 148,42 €/Monat | [Details ansehen](https://www.netcup.de/server/root-server/rs-8000-g12.5-iv-24m-eu#rs-8000-g12.5-iv-12m-eu) |\n",
        "> 📌 ***Root Server Traffic-Regelung:*** *If traffic exceeds 3 TB within the last 24 hours, a temporary throttling to 300 Mbit/s will be applied. The throttling is lifted as soon as this condition no longer applies. (Überschreitet der Traffic innerhalb der letzten 24 Stunden 3 TB, wird vorübergehend auf 300 Mbit/s gedrosselt. Die Drosselung wird aufgehoben, sobald dies nicht mehr zutrifft.)*\n",
        "### VPS G12.5 (Leistungsstarke Shared Kerne, x86-Architektur)",
        "| Tarif | vCores | RAM (DDR5 ECC) | SSD Speicher | Bandbreite | Preis exkl. MwSt. | Preis inkl. 19% MwSt. | Link |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| VPS 500 G12.5 | 2 vCores | 4 GB | 64 GB | 2,5 GBit/s | 6,94 €/Monat | 8,26 €/Monat | [Details ansehen](https://www.netcup.de/server/vps/vps-500-g12.5-iv-24m-eu#vps-500-g12.5-iv-12m-eu) |",
        f"| VPS 1000 G12.5 | 4 vCores | 8 GB | 128 GB | 2,5 GBit/s | 12,18 €/Monat | 14,49 €/Monat | [Details ansehen](https://www.netcup.de/server/vps/vps-1000-g12.5-iv-24m-eu#vps-1000-g12.5-iv-12m-eu) |",
        f"| VPS 2000 G12.5 | 8 vCores | 16 GB | 256 GB | 2,5 GBit/s | 22,62 €/Monat | 26,92 €/Monat | [Details ansehen](https://www.netcup.de/server/vps/vps-2000-g12.5-iv-24m-eu#vps-2000-g12.5-iv-12m-eu) |",
        f"| VPS 4000 G12.5 | 12 vCores | 32 GB | 512 GB | 2,5 GBit/s | 38,11 €/Monat | 45,35 €/Monat | [Details ansehen](https://www.netcup.de/server/vps/vps-4000-g12.5-iv-24m-eu#vps-4000-g12.5-iv-12m-eu) |",
        f"| VPS 8000 G12.5 | 16 vCores | 64 GB | 1024 GB (1 TB) | 2,5 GBit/s | 56,39 €/Monat | 67,10 €/Monat | [Details ansehen](https://www.netcup.de/server/vps/vps-8000-g12.5-iv-24m-eu#vps-8000-g12.5-iv-12m-eu) |\n",
        "> 📌 ***VPS Traffic-Regelung:*** *If traffic exceeds 2 TB within the last 24 hours, a temporary throttling to 200 Mbit/s will be applied. The throttling is lifted as soon as this condition no longer applies. (Überschreitet der Traffic innerhalb der letzten 24 Stunden 2 TB, wird vorübergehend auf 200 Mbit/s gedrosselt. Die Drosselung wird aufgehoben, sobald dies nicht mehr zutrifft.)*\n",
        "## ❓ Häufig gestellte Fragen (FAQs)",
        "**Q: Sind die Gutscheine kostenlos?**  ",
        "A: Ja, vollkommen kostenlos. Sie können die Codes direkt im Warenkorb eingeben.\n",
        "**Q: Können Gutscheine kombiniert werden?**  ",
        "A: Nein, pro Bestellung kann immer nur ein Gutschein eingelöst werden.\n",
        "---\n",
        "*(Dieses README wird automatisch mit netcup.free synchronisiert. Alle Gutscheine sind Einmalgutscheine!)*\n"
    ])

    with open("README_DE.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("README_DE.md written successfully.")

def main():
    data = fetch_coupons_from_main_api()
    if not data or not data.get("coupons"):
        data = fetch_coupons_from_pages_api()

    if not data or not data.get("coupons"):
        print("Failed to retrieve coupon data from both primary and fallback APIs.")
        sys.exit(1)

    coupons = data.get("coupons", [])
    total_codes = sum(len(c.get("codes", [])) for c in coupons)
    last_sync_display = data.get("last_sync_display")
    print(f"API provided last_sync_display: {last_sync_display}")
    times = get_current_time_display(last_sync_display)

    write_english_readme(coupons, times["en"])
    write_chinese_readme(coupons, times["zh"])
    write_german_readme(coupons, times["de"])
    print("All README documents updated successfully.")

if __name__ == "__main__":
    main()
