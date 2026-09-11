#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Netcup Voucher Code Synchronization Script
Automatically fetches verified coupons from the netcup.free API
and generates multi-language Markdown documents for GitHub.
"""

import json
import os
import sys
import time
import urllib.request

# Environment variables with sensible defaults
API_URL = os.getenv("WEBSITE_API_URL", "https://netcup.free/api/coupons")
WEBSITE_URL = os.getenv("WEBSITE_URL", "https://netcup.free")
REF_CODE = os.getenv("AFF_REF_CODE", "257842")

CATEGORY_MAPPING_EN = {
    "discount": "General Discounts (€5.00 Voucher)",
    "rs": "Root Servers (RS G12 - Dedicated CPU)",
    "vps": "VPS (Virtual Private Servers - G12)",
    "hosting": "Web Hosting (Shared SSD Hosting)"
}

CATEGORY_MAPPING_ZH = {
    "discount": "通用折扣券 (新人立减 5 欧元)",
    "rs": "Root Server 独立核心服务器 (G12 代)",
    "vps": "VPS 云服务器 (G12 代)",
    "hosting": "Webhosting 虚拟主机 (免税 + 免费域名)"
}

CATEGORY_MAPPING_DE = {
    "discount": "Allgemeine Gutscheine (5 € Neukundengutschein)",
    "rs": "Root Server (RS G12 - Dedizierte CPU)",
    "vps": "vServer (VPS G12)",
    "hosting": "Webhosting (Inklusivdomain & SSD)"
}

def fetch_coupons():
    print(f"Fetching coupons from API: {API_URL}")
    req = urllib.request.Request(
        API_URL, 
        headers={
            'User-Agent': 'NetcupFree-SyncBot/1.0 (GitHub Actions Automated Sync)'
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            if response.status != 200:
                print(f"Error: API returned HTTP status {response.status}")
                return None
            data = response.read().decode('utf-8')
            return json.loads(data)
    except Exception as e:
        print(f"Failed to fetch data from API: {e}")
        return None

def write_english_readme(coupons, last_updated):
    md = [
        "🌐 **Select Language:** English | [简体中文](README_ZH.md) | [Deutsch](README_DE.md)\n",
        "# ⚡ Verified Netcup Coupons & Voucher Codes",
        "> 🏷️ Real-time curated and verified Netcup voucher codes. Automatically synchronized and checked every few hours.\n",
        f"⏰ **Last Updated:** `{last_updated}`\n",
        "## 🛒 How to Redeem",
        f"- 🇩🇪 **German Checkout:** [https://www.netcup.com/de/checkout/warenkorb](https://www.netcup.com/de/checkout/warenkorb?ref={REF_CODE})",
        f"- 🇬🇧 **English Checkout:** [https://www.netcup.com/en/checkout/cart](https://www.netcup.com/en/checkout/cart?ref={REF_CODE})",
        f"- 🌐 **Live Website:** Visit [{WEBSITE_URL.replace('https://', '')}]({WEBSITE_URL}) for real-time coupon verification, stock monitoring, and hardware benchmarks.\n",
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
                md.append(f"  - [`{code}`]({direct_url}) *(Click code to apply directly)*")
        md.append("")

    # Technical specifications
    md.extend([
        "## 🚀 Hardware Specifications (Netcup G12 Generation)",
        "Netcup G12 instances feature AMD EPYC 9645 enterprise processors with DDR5 ECC memory and enterprise NVMe storage.\n",
        "### Root Server G12 (Dedicated AMD EPYC 9645 Cores)",
        "| Plan | CPU / vCores | RAM (DDR5 ECC) | NVMe Storage | Traffic | Link |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| RS 1000 G12 | 4 Dedicated Cores | 8 GB | 256 GB | Unlimited | [View Plan](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |",
        f"| RS 2000 G12 | 8 Dedicated Cores | 16 GB | 512 GB | Unlimited | [View Plan](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |",
        f"| RS 4000 G12 | 12 Dedicated Cores | 32 GB | 1024 GB | Unlimited | [View Plan](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |",
        f"| RS 8000 G12 | 16 Dedicated Cores | 64 GB | 2048 GB | Unlimited | [View Plan](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |\n",
        "### VPS G12 (High Performance Shared Cores)",
        "| Plan | vCores | RAM (DDR5 ECC) | NVMe Storage | Port Speed | Link |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| VPS 1000 G12 | 4 vCores | 8 GB | 256 GB | 1 Gbps | [View Plan](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |",
        f"| VPS 2000 G12 | 8 vCores | 16 GB | 512 GB | 1 Gbps | [View Plan](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |",
        f"| VPS 4000 G12 | 12 vCores | 32 GB | 1024 GB | 1 Gbps | [View Plan](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |",
        f"| VPS 8000 G12 | 16 vCores | 64 GB | 2048 GB | 1 Gbps | [View Plan](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |\n",
        "## ❓ FAQ",
        "**Q: Are these voucher codes free?**  ",
        "A: Yes, absolutely 100% free. You can use any valid code during checkout.\n",
        "**Q: Can I combine multiple vouchers?**  ",
        "A: Netcup allows only one coupon code per single order.\n",
        "**Q: What if all codes are taken?**  ",
        f"A: New vouchers are added regularly. Visit [{WEBSITE_URL.replace('https://', '')}]({WEBSITE_URL}) to fetch newly generated codes.\n",
        "---\n",
        "*(This repository is maintained and synchronized automatically upon coupon changes. Vouchers are single-use!)*\n"
    ])

    with open("README.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("Generated README.md successfully.")

def write_chinese_readme(coupons, last_updated):
    md = [
        "🌐 **语言切换:** [English](README.md) | 简体中文 | [Deutsch](README_DE.md)\n",
        "# ⚡ Netcup 优惠码与折扣券实时集合",
        "> 🏷️ 自动化实时校验与更新的 Netcup 优惠码集合，涵盖 Root Server、VPS 以及虚拟主机。\n",
        f"⏰ **最后更新时间:** `{last_updated}`\n",
        "## 🛒 快速兑换通道",
        f"- 🇩🇪 **德语结账购物车:** [netcup.com/de/checkout/warenkorb](https://www.netcup.com/de/checkout/warenkorb?ref={REF_CODE})",
        f"- 🇬🇧 **英语结账购物车:** [netcup.com/en/checkout/cart](https://www.netcup.com/en/checkout/cart?ref={REF_CODE})",
        f"- 🌐 **在线实时验证站:** 访问 [{WEBSITE_URL.replace('https://', '')}]({WEBSITE_URL}) 查看实时库存检测、测速与综合对比工具。\n",
        "## 🎟️ 当前可用优惠码\n"
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
            title = item.get("title", "")
            desc = item.get("desc", "")
            md.append(f"- **{title}**" + (f" - *{desc}*" if desc else ""))
            for code in codes:
                direct_url = f"https://www.netcup.com/en/checkout/cart?gutschein={code}&ref={REF_CODE}"
                md.append(f"  - [`{code}`]({direct_url}) *(点击自动填入购物车)*")
        md.append("")

    md.extend([
        "## 🚀 硬件配置参数表 (Netcup G12 代 AMD EPYC 9645)",
        "Netcup 最新 G12 代服务器全系搭载 AMD 顶级 EPYC 9645 处理器与高速 NVMe 固态硬盘：\n",
        "### Root Server G12 (独享独立核心 - 强劲算力保证)",
        "| 型号规格 | 独立 CPU 核心 | 内存 (DDR5 ECC) | NVMe 存储 | 流量限制 | 官方直达 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| RS 1000 G12 | 4 独享核心 | 8 GB | 256 GB | 无限流量 | [立即查看](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |",
        f"| RS 2000 G12 | 8 独享核心 | 16 GB | 512 GB | 无限流量 | [立即查看](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |",
        f"| RS 4000 G12 | 12 独享核心 | 32 GB | 1024 GB | 无限流量 | [立即查看](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |",
        f"| RS 8000 G12 | 16 独享核心 | 64 GB | 2048 GB | 无限流量 | [立即查看](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |\n",
        "### VPS G12 (超高性价比共享核心)",
        "| 型号规格 | 共享核心 | 内存 (DDR5 ECC) | NVMe 存储 | 端口速率 | 官方直达 |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| VPS 1000 G12 | 4 核心 | 8 GB | 256 GB | 1 Gbps | [立即查看](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |",
        f"| VPS 2000 G12 | 8 核心 | 16 GB | 512 GB | 1 Gbps | [立即查看](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |",
        f"| VPS 4000 G12 | 12 核心 | 32 GB | 1024 GB | 1 Gbps | [立即查看](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |",
        f"| VPS 8000 G12 | 16 核心 | 64 GB | 2048 GB | 1 Gbps | [立即查看](https://www.netcup.com/en/checkout/cart?ref={REF_CODE}) |\n",
        "## ❓ 常见问题 (FAQ)",
        "**Q: 优惠码是一次性的吗？**  ",
        "A: 是的，Netcup 官方发放的优惠码每个均为一次性使用，先到先得。本仓库会自动替换已被领取的失效券。\n",
        "**Q: 现有老客户可以使用吗？**  ",
        "A: 除 5 欧元新人通用券仅限首单外，RS、VPS 和 Webhosting 的免费月份或 30% 终身折扣券新老客户均可使用。\n",
        "**Q: 如果页面上的券都被用完了怎么办？**  ",
        f"A: 爬虫每隔数小时会自动补充，您也可以直接访问 [{WEBSITE_URL.replace('https://', '')}]({WEBSITE_URL}) 获取最新鲜出炉的有效码。\n",
        "---\n",
        "*(本 README 优惠码变动时自动同步。优惠码均为一次性使用，请尽快兑换！)*\n"
    ])

    with open("README_ZH.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("Generated README_ZH.md successfully.")

def write_german_readme(coupons, last_updated):
    md = [
        "🌐 **Sprache auswählen:** [English](README.md) | [简体中文](README_ZH.md) | Deutsch\n",
        "# ⚡ Verifizierte Netcup Gutscheine & Rabattcodes",
        "> 🏷️ Eine kuratierte Liste von aktiven Netcup Gutscheincodes. Automatisch geprüft und regelmäßig synchronisiert.\n",
        f"⏰ **Zuletzt aktualisiert:** `{last_updated}`\n",
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
            title = item.get("title", "")
            desc = item.get("desc", "")
            md.append(f"- **{title}**" + (f" - *{desc}*" if desc else ""))
            for code in codes:
                direct_url = f"https://www.netcup.com/de/checkout/warenkorb?gutschein={code}&ref={REF_CODE}"
                md.append(f"  - [`{code}`]({direct_url}) *(Klicken zum Einlösen)*")
        md.append("")

    md.extend([
        "## 🚀 Technische Spezifikationen (Netcup G12 Generation)",
        "### Root Server G12 (Dedizierte AMD EPYC 9645 Kerne)",
        "| Tarif | CPU / Kerne | RAM (DDR5 ECC) | NVMe Speicher | Traffic | Link |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
        f"| RS 1000 G12 | 4 Dedizierte Kerne | 8 GB | 256 GB | Flatrate | [Details ansehen](https://www.netcup.com/de/checkout/warenkorb?ref={REF_CODE}) |",
        f"| RS 2000 G12 | 8 Dedizierte Kerne | 16 GB | 512 GB | Flatrate | [Details ansehen](https://www.netcup.com/de/checkout/warenkorb?ref={REF_CODE}) |",
        f"| RS 4000 G12 | 12 Dedizierte Kerne | 32 GB | 1024 GB | Flatrate | [Details ansehen](https://www.netcup.com/de/checkout/warenkorb?ref={REF_CODE}) |",
        f"| RS 8000 G12 | 16 Dedizierte Kerne | 64 GB | 2048 GB | Flatrate | [Details ansehen](https://www.netcup.com/de/checkout/warenkorb?ref={REF_CODE}) |\n",
        "## ❓ Häufig gestellte Fragen (FAQs)",
        "**Q: Sind die Gutscheine kostenlos?**  ",
        "A: Ja, vollkommen kostenlos. Sie können die Codes direkt im Warenkorb eingeben.\n",
        "**Q: Können Gutscheine kombiniert werden?**  ",
        "A: Nein, pro Bestellung kann immer nur ein Gutschein eingelöst werden.\n",
        "---\n",
        "*(Dieses README wird automatisch aktualisiert. Alle Gutscheine sind Einmalgutscheine!)*\n"
    ])

    with open("README_DE.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print("Generated README_DE.md successfully.")

def main():
    data = fetch_coupons()
    if not data or not data.get("success"):
        print("Failed to retrieve valid coupon data from API.")
        sys.exit(1)

    coupons = data.get("coupons", [])
    last_updated = data.get("last_sync_display", time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()))

    print(f"Total coupon groups: {len(coupons)}")
    write_english_readme(coupons, last_updated)
    write_chinese_readme(coupons, last_updated)
    write_german_readme(coupons, last_updated)
    print("All README files generated successfully.")

if __name__ == "__main__":
    main()
