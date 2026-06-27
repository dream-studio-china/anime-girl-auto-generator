"""
IP Quality Detection Helper
============================
检测当前出口 IP 是否为住宅 IP，评估适合 X/Twitter 发布的质量。

用法:
    python .bootstrap/scripts/ip_check.py                    # 快速检测
    python .bootstrap/scripts/ip_check.py --detail            # 详细信息
    python .bootstrap/scripts/ip_check.py --json              # JSON 输出

数据源 (优先级):
    1. ip-api.com  (free, proxy/hosting/mobile 检测)
    2. ipinfo.io   (free, ASN 类型判断)
    3. ifconfig.me (fallback, 仅 IP)

质量分级:
    ✅ residential  — 住宅 IP，最佳
    ⚠️ mobile       — 移动网络，可用
    ⚠️ business     — 商业宽带，通常 OK
    ❌ hosting      — 数据中心/VPS，高风险
    ❌ proxy/vpn    — 代理/VPN，极高风险
"""

import json
import sys
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

AGENT_ROOT = Path(__file__).resolve().parent.parent

# 已知的 VPS/数据中心 ASN 关键字符串 (ip-api org 字段)
VPS_KEYWORDS = [
    "digitalocean", "amazon", "aws", "google cloud", "gcp",
    "microsoft", "azure", "vultr", "linode", "hetzner",
    "ovh", "alibaba", "tencent", "oracle cloud",
    "choopa", "psychz", "buyvm", "ramnode", "hosthatch",
    "contabo", "netcup", "scaleway", "upcloud",
]


def _curl_get(url: str, timeout: int = 10) -> str:
    """简单 HTTP GET，不依赖第三方库。"""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "bootstrap-ip-check/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        return ""


def detect_ip() -> str:
    """获取当前出口 IP。"""
    # 试用多个 echo 服务
    for svc in [
        "https://ifconfig.me/ip",
        "https://api.ipify.org",
        "https://icanhazip.com",
    ]:
        ip = _curl_get(svc, timeout=5).strip()
        if ip and "." in ip:
            return ip
    # fallback: use shell
    try:
        result = subprocess.run(["curl", "-s", "https://ifconfig.me"],
                              capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except Exception:
        return "unknown"


def check_ip_api(ip: str) -> dict:
    """
    ip-api.com 免费 API (45 req/min).
    返回: status, country, city, isp, org, proxy, hosting, mobile
    """
    url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,city,isp,org,as,proxy,hosting,mobile,query"
    try:
        data = json.loads(_curl_get(url, timeout=5))
        if data.get("status") == "success":
            return {
                "source": "ip-api.com",
                "ip": data.get("query", ip),
                "country": data.get("country", ""),
                "city": data.get("city", ""),
                "isp": data.get("isp", ""),
                "org": data.get("org", ""),
                "as_info": data.get("as", ""),
                "is_proxy": data.get("proxy", False),
                "is_hosting": data.get("hosting", False),
                "is_mobile": data.get("mobile", False),
            }
    except (json.JSONDecodeError, urllib.error.URLError):
        pass
    return {"source": "ip-api.com", "error": "failed"}


def classify_ip(info: dict) -> dict:
    """综合判断 IP 质量等级。"""
    org = (info.get("org", "") + " " + info.get("isp", "")).lower()
    as_info = info.get("as_info", "").lower()
    is_proxy = info.get("is_proxy", False)
    is_hosting = info.get("is_hosting", False)
    is_mobile = info.get("is_mobile", False)

    # 确定等级
    if is_proxy:
        grade = "proxy"
        label = "❌ 代理/VPN — 极高风险，X 极易封禁"
    elif is_hosting:
        grade = "hosting"
        label = "❌ 数据中心/VPS — X 可能限流或标记异常"
    else:
        # 用关键词进一步判断
        vps_hit = any(kw in org or kw in as_info for kw in VPS_KEYWORDS)
        if vps_hit:
            grade = "hosting"
            label = "❌ 数据中心/VPS — 检测到已知 VPS 服务商"
        elif is_mobile:
            grade = "mobile"
            label = "⚠️ 移动网络 — 可用但 IP 可能频繁变更"
        elif any(kw in org for kw in ["business", "corporate", "enterprise"]):
            grade = "business"
            label = "⚠️ 商业宽带 — 通常 OK，但非最佳"
        else:
            grade = "residential"
            label = "✅ 住宅 IP — 最佳，安全发布"

    return {"grade": grade, "label": label}


def run_check(detail: bool = False) -> dict:
    """完整检测流程。"""
    result = {
        "time": datetime.now().isoformat(),
        "ip": "unknown",
        "grade": "unknown",
        "label": "",
        "details": {},
    }

    ip = detect_ip()
    if ip == "unknown":
        result["grade"] = "error"
        result["label"] = "❌ 无法检测 IP — 检查网络连接"
        return result

    result["ip"] = ip

    info = check_ip_api(ip)
    if "error" not in info:
        classification = classify_ip(info)
        result["grade"] = classification["grade"]
        result["label"] = classification["label"]

        if detail:
            result["details"] = info
    else:
        result["grade"] = "unknown"
        result["label"] = "⚠️ IP 信息查询失败 (API 限流?)"

    return result


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="IP Quality Detection")
    parser.add_argument("--detail", action="store_true", help="显示详细信息")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    args = parser.parse_args()

    result = run_check(detail=args.detail)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"""
╔══════════════════════════════════════════╗
║        Bootstrap IP Quality Check       ║
╠══════════════════════════════════════════╣
║  IP:  {result['ip']:<32} ║
║  等级: {result['label']:<32} ║
╚══════════════════════════════════════════╝
        """.strip())

        if result["grade"] in ("hosting", "proxy"):
            print("\n💡 建议:")
            print("  - 当前 IP 不适合直接发布到 X")
            print("  - 可考虑使用住宅代理或切换网络")
            print("  - 或用此 IP 仅做生成，发布走其他网络")
        elif result["grade"] in ("mobile", "business"):
            print("\n💡 注意: IP 可用但非最佳，建议用住宅宽带")

        if args.detail and result.get("details"):
            print("\n详细信息:")
            for k, v in result["details"].items():
                print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
