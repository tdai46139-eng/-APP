# -*- coding: utf-8 -*-
"""
趋势助手 - 政策数据抓取
从 gov.cn 和 miit.gov.cn 抓取最新政策标题
"""

import requests
from bs4 import BeautifulSoup
from config import POLICY_SOURCES

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def fetch_policy_list(url, source_name):
    """从单个网址抓取政策列表"""
    policies = []
    try:
        resp = requests.get(url, timeout=15, headers=HEADERS)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")

        # 通用策略：找所有带文字的 <a> 标签
        for link in soup.find_all("a", href=True):
            title = link.get_text(strip=True)
            # 过滤：标题长度 > 8，排除导航/页脚链接
            if len(title) < 8:
                continue
            if title.startswith(("http", "javascript", "#")):
                continue
            # 排除非政策文字（页脚、导航、备案等）
            skip_words = [
                "更多", "返回", "首页", "登录", "注册", "搜索", "下一页", "上一页",
                "ICP", "备案", "安备", "客户端", "微博", "微信", "网站地图",
                "版权", "copyright", "联系我们", "关于我们", "意见箱", "无障碍",
                "国务院客户端", "中国政府网", "扫码", "下载",
            ]
            if any(w in title for w in skip_words):
                continue
            # 排除备案类网址
            if "beian" in link["href"].lower():
                continue

            href = link["href"]
            # 补全相对路径
            if href.startswith("/"):
                base = "/".join(url.split("/")[:3])
                href = base + href

            policies.append({
                "source": source_name,
                "title": title,
                "url": href,
            })
    except Exception as e:
        print(f"  [!] 抓取失败 {url}: {e}")

    return policies


def fetch_all_policies():
    """抓取所有政策源的最新政策"""
    all_policies = []
    seen_titles = set()  # 去重

    for source_key, source_info in POLICY_SOURCES.items():
        print(f"  抓取 {source_info['name']}...")
        for url in source_info["urls"]:
            policies = fetch_policy_list(url, source_info["name"])
            for p in policies:
                if p["title"] not in seen_titles:
                    seen_titles.add(p["title"])
                    all_policies.append(p)

    print(f"  共抓取 {len(all_policies)} 条政策")
    return all_policies


if __name__ == "__main__":
    # 单独运行此文件可以测试抓取
    policies = fetch_all_policies()
    for p in policies[:10]:
        print(f"  [{p['source']}] {p['title']}")
