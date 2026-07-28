# -*- coding: utf-8 -*-
"""
趋势助手 - 主程序
这是整个数据管道的入口，运行它会:
  1. 抓取政策数据 (gov.cn + miit.gov.cn)
  2. 抓取基金数据 (天天基金 API)
  3. 分析趋势 + 生成预测
  4. 保存到 data.json

本地测试:  python main.py
GitHub Actions 每天自动运行此文件
"""

import json
from datetime import datetime

from config import OUTPUT_FILE, USER_PROFILE
from fetch_policy import fetch_all_policies
from fetch_fund import fetch_all_funds
from analyze_trend import (
    analyze_policies,
    generate_trends,
    generate_employment,
    analyze_all_funds,
    get_health_data,
    generate_policy_wind,
)


def main():
    now = datetime.now()
    print("=" * 55)
    print(f"  趋势助手数据更新")
    print(f"  {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 55)

    # ---- 第1步: 抓取政策数据 ----
    print("\n[1/5] 抓取政策数据...")
    policies = fetch_all_policies()

    # ---- 第2步: 抓取基金数据 ----
    print("\n[2/5] 抓取基金数据...")
    funds = fetch_all_funds()

    # ---- 第3步: 分析趋势 ----
    print("\n[3/5] 分析趋势...")
    industry_signals = analyze_policies(policies)
    trends = generate_trends(industry_signals)
    print(f"  生成 {len(trends)} 个行业趋势信号")
    for t in trends[:5]:
        print(f"    {t['industry']}: 趋势分 {t['trend_score']} | 涨幅 {t['change_pct']:+.1f}% | 政策 {t['policy_count']}条")

    # ---- 第4步: 生成推荐 ----
    print("\n[4/5] 生成推荐...")
    employment = generate_employment(trends)
    print(f"  生成 {len(employment)} 条就业推荐")
    for e in employment[:3]:
        print(f"    {e['industry']}: 匹配度 {e['match_score']}% | {e['entry_barrier']}")

    fund_analysis = analyze_all_funds(funds, trends)
    print(f"  分析 {len(fund_analysis)} 只基金")
    for f in fund_analysis:
        print(f"    {f['name']}: {f['prediction']} | {f['recommendation']} | {f['policy_tag']}")

    health = get_health_data()
    policy_wind = generate_policy_wind(policies, industry_signals)

    # ---- 第5步: 保存数据 ----
    print(f"\n[5/5] 保存数据到 {OUTPUT_FILE}...")

    output = {
        "update_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "update_timestamp": int(now.timestamp()),
        "user_profile": USER_PROFILE,

        # 政策风向 (首页顶部)
        "policy_wind": policy_wind,

        # 行业趋势 (首页中部)
        "trends": trends,

        # 就业推荐 (首页底部)
        "employment": employment,

        # 基金数据 (基金页)
        "funds": fund_analysis,

        # 健康与生活 (养生页)
        "health": health,

        # 原始政策列表 (备用)
        "policies_raw": policies[:15],
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  数据已保存! 文件大小: {len(json.dumps(output, ensure_ascii=False))} 字符")
    print("\n" + "=" * 55)
    print("  更新完成!")
    print("=" * 55)


if __name__ == "__main__":
    main()
