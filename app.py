import streamlit as st
import requests
import json
import os
import feedparser
from tavily import TavilyClient
from datetime import datetime, timedelta, timezone

# =========================================================
# 🔴 核心配置区 (请确保环境变量已配置)
# =========================================================
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
BOCHA_API_KEY = os.environ.get("BOCHA_API_KEY")

def get_beijing_time():
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=8)

# =========================================================
# 🕷️ 数据抓取引擎 (根据赛道动态调整)
# =========================================================
def get_realtime_news(industry):
    if industry == "自媒体":
        query_tavily = "自媒体 流量变现 短视频 爆款"
        query_bocha = "自媒体搞钱 抖音 小红书 变现实操"
    elif industry == "跨境电商":
        query_tavily = "TikTok e-commerce dropshipping Shopify"
        query_bocha = "跨境电商 TikTok带货 独立站 选品"
    else: # 默认人工智能
        query_tavily = "AI artificial intelligence breaking news"
        query_bocha = "大模型商业化 落地应用 AI变现"

    all_news = []
    
    if TAVILY_API_KEY:
        try:
            tavily = TavilyClient(api_key=TAVILY_API_KEY)
            all_news.extend(tavily.search(query=query_tavily, search_depth="advanced", max_results=15, days=1).get('results', []))
        except: pass
        
    if BOCHA_API_KEY:
        url = "https://api.bochaai.com/v1/web-search"
        headers = {"Authorization": f"Bearer {BOCHA_API_KEY}", "Content-Type": "application/json"}
        try:
            res = requests.post(url, json={"query": query_bocha, "freshness": "oneDay", "count": 15}, headers=headers, timeout=10)
            items = res.json().get('data', {}).get('webPages', {}).get('value', [])
            all_news.extend([{"title": i.get('name'), "url": i.get('url'), "content": i.get('snippet')} for i in items if len(i.get('name', '')) > 6])
        except: pass

    try:
        for url in ["https://36kr.com/feed", "https://www.ithome.com/rss/"]:
            for entry in feedparser.parse(url).entries[:10]:
                all_news.append({"title": entry.title, "url": entry.link, "content": entry.summary[:200] if hasattr(entry, 'summary') else entry.title})
    except: pass

    unique_news, seen = [], set()
    for news in all_news:
        if news.get('url') and news['url'] not in seen:
            unique_news.append(news)
            seen.add(news['url'])
    return unique_news

# =========================================================
# 🧠 AI 处理引擎 (包含智能重试与优雅降级机制)
# =========================================================
def ai_process_content(news_data, industry):
    if not news_data: return "⚠️ 未抓取到有效数据，请检查网络或 API 余额。"
    
    def build_prompt(data_slice):
        data_str = json.dumps(data_slice, ensure_ascii=False)
        return f"""
        你是一名极其冷酷、务实的商业战略顾问。
        请基于原始数据，撰写一份针对【{industry}】赛道的《散户搞钱与避坑内参》。

        ❌ 致命红线：
        1. 绝对禁止使用“$”符号，用中文“美元”代替。
        2. 必须且只能输出纯文本内容，不要有任何代码块包裹。

        ✅ 任务要求：
        第一部分：⭐ 核心情报内参 (强制写满 10 条)
        * 提取最相关的 10 条情报。
        * ⚠️ 绝对红线（截流标记）：在第 3 条情报写完后，必须、立刻、单独空一行输出这串字符：“===PAYWALL===”，然后再继续写第 4 条！

        第二部分：🔭 深度战略研判 (宏观大局)
        包含：1. 到底发生了什么？ 2. 钱流向了哪里？ 3. 我们该怎么干？

        第三部分：💰 普通人无门槛搞钱专区 (3个落地案例)
        强制零成本、无代码、只做C端变现。包含：🎯 核心逻辑、🛠️ 工具与平台、👣 极简落地动作。

        第四部分：🛑 散户入局的 3 个致命避坑指南
        包含：🕳️ 陷阱表象、🩸 致命逻辑、🛡️ 破局自保。
        
        原始数据：{data_str}
        """

    if not
