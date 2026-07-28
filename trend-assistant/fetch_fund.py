# -*- coding: utf-8 -*-
"""
趋势助手 - 基金数据抓取
主接口: pingzhongdata (天天基金网基金详情数据)
备用接口: fundgz (实时估值JSONP)
"""

import json
import re
import time
from datetime import datetime
import requests
from config import FUND_CODES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://fund.eastmoney.com/",
}


def fetch_fund(fund_code):
    """获取单只基金数据，依次尝试多个接口"""

    # 方案1: pingzhongdata (最可靠)
    result = _fetch_from_pingzhongdata(fund_code)
    if result:
        return result

    # 方案2: fundgz 实时估值
    result = _fetch_from_fundgz(fund_code)
    if result:
        return result

    print(f"  [!] 基金 {fund_code} 所有接口均失败")
    return None


def _fetch_from_pingzhongdata(fund_code):
    """从 pingzhongdata 接口获取基金历史净值数据"""
    url = f"http://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
    try:
        resp = requests.get(url, timeout=15, headers=HEADERS)
        if resp.status_code != 200 or len(resp.text) < 100:
            return None

        # 提取基金名称
        name_match = re.search(r'var fS_name\s*=\s*"(.+?)"', resp.text)
        name = name_match.group(1) if name_match else fund_code

        # 提取净值趋势数据
        # 格式: var Data_netWorthTrend = [{"x":1234567890000,"y":1.234,"equityReturn":0.82,...}]
        trend_match = re.search(r'var Data_netWorthTrend\s*=\s*(\[.+?\]);', resp.text)
        if trend_match:
            trend_data = json.loads(trend_match.group(1))
            if trend_data:
                latest = trend_data[-1]
                net_value = float(latest.get("y", 0))
                change_pct = float(latest.get("equityReturn", 0))
                # 时间戳是毫秒
                ts = latest.get("x", 0)
                if ts:
                    update_time = datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
                else:
                    update_time = ""

                return {
                    "code": fund_code,
                    "name": name,
                    "net_value": net_value,
                    "est_value": net_value,  # 历史数据无估算值，用实际净值
                    "est_change_pct": change_pct,
                    "update_time": update_time,
                    "source": "pingzhongdata",
                }
    except Exception as e:
        print(f"  [!] pingzhongdata 接口失败 {fund_code}: {e}")
    return None


def _fetch_from_fundgz(fund_code):
    """从 fundgz 接口获取实时估值"""
    ts = int(time.time() * 1000)
    url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js?rt={ts}"
    try:
        resp = requests.get(url, timeout=10, headers=HEADERS)
        match = re.search(r'jsonpgz\((.+)\);', resp.text)
        if match:
            data = json.loads(match.group(1))
            return {
                "code": data.get("fundcode", fund_code),
                "name": data.get("name", ""),
                "net_value": float(data.get("dwjz", 0)),
                "est_value": float(data.get("gsz", 0)),
                "est_change_pct": float(data.get("gszzl", 0)),
                "update_time": data.get("gztime", ""),
                "source": "fundgz",
            }
    except Exception as e:
        print(f"  [!] fundgz 接口失败 {fund_code}: {e}")
    return None


def fetch_all_funds():
    """获取所有配置的基金数据"""
    funds = []
    for code in FUND_CODES:
        print(f"  获取基金 {code}...")
        fund = fetch_fund(code)
        if fund:
            funds.append(fund)
            print(f"    {fund['name']} | 净值 {fund['net_value']:.4f} | 涨跌 {fund['est_change_pct']:+.2f}%")
    return funds


if __name__ == "__main__":
    funds = fetch_all_funds()
    for f in funds:
        print(f"  {f['name']} ({f['code']}) | 净值 {f['net_value']:.4f} | {f['est_change_pct']:+.2f}% | {f.get('source','')}")
