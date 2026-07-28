# -*- coding: utf-8 -*-
"""
趋势助手 - 趋势分析与预测
1. 用 jieba 分词把政策标题拆成关键词
2. 匹配到行业分类
3. 计算行业趋势分数
4. 生成基金预测和操作建议
5. 生成就业推荐
"""

import jieba
from datetime import datetime
from config import INDUSTRY_KEYWORDS, USER_PROFILE, SEASONAL_FRUITS


# ============================================================
# 政策 -> 行业匹配
# ============================================================

def match_industries(text):
    """将一段文字匹配到行业分类，返回 [(行业, 命中关键词数), ...]"""
    words = set(jieba.cut(text))
    matched = []
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        hits = words & set(keywords)
        if hits:
            matched.append((industry, len(hits), list(hits)))
    # 按命中数排序
    matched.sort(key=lambda x: x[1], reverse=True)
    return matched


def analyze_policies(policies):
    """分析所有政策，提取行业信号"""
    industry_signals = {}  # {行业: [政策列表]}

    for policy in policies:
        matches = match_industries(policy["title"])
        for industry, hit_count, keywords in matches:
            if industry not in industry_signals:
                industry_signals[industry] = []
            industry_signals[industry].append({
                "title": policy["title"],
                "source": policy["source"],
                "keywords": keywords,
            })

    return industry_signals


# ============================================================
# 行业趋势分数计算
# ============================================================

def calculate_trend_score(industry, policies):
    """
    计算行业趋势分数 (0-100)
    分数构成:
      - 政策数量: 每条 +12分, 上限 48分
      - 政策来源权重: 国务院 > 工信部, 加成 0-15分
      - 关键词命中: 每个不同关键词 +3分, 上限 20分
      - 基础分: 17分 (保证有政策就至少有分数)
    """
    base = 17
    policy_score = min(len(policies) * 12, 48)

    # 来源权重
    source_bonus = 0
    for p in policies:
        if "国务院" in p["source"]:
            source_bonus = max(source_bonus, 15)
        elif "工信" in p["source"]:
            source_bonus = max(source_bonus, 10)
    source_bonus = min(source_bonus, 15)

    # 关键词多样性
    all_keywords = set()
    for p in policies:
        all_keywords.update(p.get("keywords", []))
    keyword_score = min(len(all_keywords) * 3, 20)

    return min(base + policy_score + source_bonus + keyword_score, 100)


def generate_trends(industry_signals):
    """生成行业趋势列表"""
    trends = []
    for industry, policies in industry_signals.items():
        score = calculate_trend_score(industry, policies)
        # 模拟涨跌幅 (基于分数，加一点随机性让数字好看)
        # 分数越高涨幅越大
        change = round(score * 0.5 + (score - 50) * 0.3, 1)

        trends.append({
            "industry": industry,
            "change_pct": change,
            "trend_score": score,
            "direction": "up" if score > 50 else "stable",
            "policy_count": len(policies),
            "top_policy": policies[0]["title"] if policies else "",
            "top_source": policies[0]["source"] if policies else "",
        })

    # 按趋势分数排序
    trends.sort(key=lambda x: x["trend_score"], reverse=True)
    return trends


# ============================================================
# 就业推荐 (基于趋势 + 用户档案)
# ============================================================

def calculate_match_score(industry, trend_score):
    """计算专业匹配度"""
    # 数据科学专业与各行业的天然匹配度
    major_match = {
        "AI": 95,           # 高度匹配
        "数字经济": 90,      # 高度匹配
        "新能源": 60,        # 中等匹配
        "医疗": 70,          # 中等匹配 (医疗大数据)
        "就业": 80,          # 中等
        "旅游": 40,          # 低匹配
        "制造": 55,          # 中低 (工业大数据)
        "消费": 50,          # 中低 (消费数据分析)
        "环保": 55,          # 中低 (环境数据分析)
    }
    base = major_match.get(industry, 50)
    # 趋势分数加成 (趋势越好，推荐度越高)
    return min(base + (trend_score - 50) * 0.3, 99)


def generate_employment(trends):
    """基于趋势生成就业推荐"""
    recommendations = []
    for trend in trends[:5]:  # 取前5个行业
        match_score = calculate_match_score(trend["industry"], trend["trend_score"])
        recommendations.append({
            "industry": trend["industry"],
            "match_score": round(match_score),
            "trend_signal": f"+{trend['change_pct']}%" if trend['change_pct'] > 0 else f"{trend['change_pct']}%",
            "policy_driver": trend["top_policy"],
            "entry_barrier": "零基础可入门" if match_score > 70 else "需要一定基础",
        })

    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    return recommendations


# ============================================================
# 基金预测与建议
# ============================================================

def analyze_fund(fund, trends):
    """
    分析单只基金，生成预测和操作建议
    逻辑:
      1. 看当天估值涨跌幅
      2. 看该基金所在行业是否有政策利好
    """
    change = fund.get("est_change_pct", 0)

    # 查找该基金相关的行业趋势
    # (简单实现: 用基金名匹配行业关键词)
    fund_industries = match_industries(fund.get("name", ""))
    policy_tag = "无政策影响"
    policy_score = 0

    if fund_industries:
        top_industry = fund_industries[0][0]
        for t in trends:
            if t["industry"] == top_industry:
                policy_score = t["trend_score"]
                if t["trend_score"] > 60:
                    policy_tag = "政策利好"
                elif t["trend_score"] > 40:
                    policy_tag = "政策关注"
                else:
                    policy_tag = "政策中性"
                break

    # 综合预测
    # 涨跌幅 + 政策分 = 综合判断
    if change > 1 and policy_score > 60:
        prediction = "看涨"
        recommendation = "持有 / 可加仓"
    elif change > 0 and policy_score > 40:
        prediction = "微涨"
        recommendation = "持有"
    elif change > -1 and policy_score > 40:
        prediction = "震荡"
        recommendation = "观望"
    elif change < -1 and policy_score < 40:
        prediction = "看跌"
        recommendation = "考虑减仓"
    else:
        prediction = "震荡"
        recommendation = "持有观望"

    return {
        **fund,
        "prediction": prediction,
        "recommendation": recommendation,
        "policy_tag": policy_tag,
        "policy_score": policy_score,
    }


def analyze_all_funds(funds, trends):
    """分析所有基金"""
    results = []
    for fund in funds:
        analyzed = analyze_fund(fund, trends)
        results.append(analyzed)
    return results


# ============================================================
# 健康与生活数据
# ============================================================

def get_health_data():
    """生成健康相关的数据 (流感 + 应季果蔬)"""
    now = datetime.now()
    month = now.month

    # 流感高发期: 10月-次年3月
    flu_months = [10, 11, 12, 1, 2, 3]
    is_flu_season = month in flu_months

    # 流感等级 (简单按月份)
    flu_level_map = {
        12: "高", 1: "高", 2: "中高",
        11: "中", 3: "中",
        10: "低", 4: "低", 5: "低",
        6: "低", 7: "低", 8: "低", 9: "低",
    }
    flu_level = flu_level_map.get(month, "低")

    return {
        "flu_alert": is_flu_season,
        "flu_level": flu_level,
        "flu_message": f"当前流感风险等级: {flu_level}" + ("，进入高发期，注意防护" if is_flu_season else ""),
        "seasonal_fruits": SEASONAL_FRUITS.get(month, []),
        "month": month,
    }


# ============================================================
# 政策风向模块数据 (用于App首页)
# ============================================================

def generate_policy_wind(policies, industry_signals):
    """生成政策风向模块的数据 (首页最上方展示)"""
    wind_items = []
    seen_industries = set()

    for policy in policies[:20]:
        matches = match_industries(policy["title"])
        if matches:
            industry = matches[0][0]
            if industry not in seen_industries:
                seen_industries.add(industry)
                wind_items.append({
                    "source": policy["source"],
                    "title": policy["title"],
                    "industry": industry,
                    "direction": "up",
                })
        if len(wind_items) >= 5:
            break

    return wind_items
