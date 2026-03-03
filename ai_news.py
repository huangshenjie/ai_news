import requests
import json
import os
import feedparser
from tavily import TavilyClient
from datetime import datetime, timedelta, timezone

# =========================================================
# 🔴 核心配置区
# =========================================================
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
BOCHA_API_KEY = os.environ.get("BOCHA_API_KEY")

WECOM_WEBHOOK_URL = os.environ.get("WECOM_WEBHOOK_URL")
FEISHU_WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL")

def get_beijing_time():
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=8)

# ---------------------------------------------------------
# 🌍 数据源 A: Tavily (恢复最大抓取量 25)
# ---------------------------------------------------------
def get_tavily_data(query=None):
    print("1. 正在全网搜索 (Tavily)...")
    if not TAVILY_API_KEY:
        return []
    if not query:
        query = "AI artificial intelligence breaking news"
        
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    try:
        response = tavily.search(query=query, search_depth="advanced", max_results=25, days=1)
        results = response.get('results', [])
        print(f"✅ Tavily 获取成功: {len(results)} 条")
        return results
    except Exception as e:
        print(f"❌ Tavily 搜索失败: {e}")
        return []

# ---------------------------------------------------------
# 🇨🇳 数据源 B: 博查 Bocha (恢复最大抓取量 25)
# ---------------------------------------------------------
def get_bocha_data(query=None):
    print("2. 正在尝试博查搜索 (Bocha)...")
    if not BOCHA_API_KEY:
        return [] 
    if not query:
        query = "AI大模型 商业化 落地应用"
        
    url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {BOCHA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"query": query, "freshness": "oneDay", "count": 25}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            web_pages = data.get('data', {}).get('webPages', {})
            items_list = web_pages.get('value', [])
            results = []
            for item in items_list:
                if len(item.get('name', '')) > 6:
                    results.append({"title": item.get('name'), "url": item.get('url'), "content": item.get('snippet')})
            print(f"✅ Bocha 获取成功: {len(results)} 条")
            return results
        else:
            return []
    except Exception as e:
        return []

# ---------------------------------------------------------
# 🛡️ 数据源 C: RSS 
# ---------------------------------------------------------
def get_rss_data(rss_sources=None):
    print("3. 正在获取 RSS 深度资讯...")
    if not rss_sources:
        rss_sources = ["https://36kr.com/feed"]
    results = []
    try:
        for rss_url in rss_sources:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:15]:
                results.append({"title": entry.title, "url": entry.link, "content": entry.summary[:200] if hasattr(entry, 'summary') else entry.title})
        print(f"✅ RSS 获取成功: {len(results)} 条")
        return results
    except Exception as e:
        return []

def get_realtime_news(tavily_query=None, bocha_query=None, rss_urls=None):
    all_news = []
    all_news.extend(get_tavily_data(tavily_query))
    all_news.extend(get_bocha_data(bocha_query))
    all_news.extend(get_rss_data(rss_urls))
    
    seen_urls = set()
    unique_news = []
    for news in all_news:
        url = news.get('url', '')
        if url and url not in seen_urls:
            unique_news.append(news)
            seen_urls.add(url)
    print(f"✅ 去重后待处理素材: {len(unique_news)} 条")
    return unique_news

# ---------------------------------------------------------
# 🧠 DeepSeek 思考与清洗 (完美融合三大模块，解决排版乱码)
# ---------------------------------------------------------
def call_deepseek(prompt):
    print("4. 正在调用 DeepSeek 进行深度推演...")
    if not DEEPSEEK_API_KEY: return None
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False, "temperature": 0.7, "max_tokens": 8000
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        if response.status_code == 200: return response.json()['choices'][0]['message']['content']
        else: return None
    except Exception: return None

def ai_process_content(news_data, industry_focus="人工智能", report_title="AI 全球实战内参"):
    if not news_data: return None
    beijing_date = get_beijing_time().strftime('%Y-%m-%d')
    data_str = json.dumps(news_data[:80], ensure_ascii=False)

    prompt = f"""
    你是一名**极度务实**的【{industry_focus}】商业战略顾问兼套利专家。这里有 {len(news_data)} 条原始资讯。
    请撰写一份《{report_title}》。

    **❌ 致命红线（违反直接任务失败）：**
    1. **排版乱码防范：** 绝对禁止在输出中使用“$”符号！如果你要表示美元，请直接使用中文“美元”（例如：800美元）。否则会导致前端渲染直接崩溃！
    2. **禁止偷懒：** 必须按 1 到 20 的编号，完整输出 20 条资讯。少一条都不行。
    3. **不要废话：** 严禁出现“受限于篇幅”等字眼。

    **✅ 任务要求：**
    
    **模块一：核心情报 (必须满 20 条，按 S/A/B 分级)**
    * 提取与【{industry_focus}】最相关的情报。
    * **格式：** 编号. **[标签] 标题** -> 🔗 [来源](url) -> 💡 **解读：** (商业影响)。

    **模块二：💰 信息差套利与变现专区 (新增核心)**
    * 提取出 **2-3 个可以直接执行的信息差套利方案**。
    * **1. 跨国/平台套利：** 发现国内外时间差，或平台规则红利。
    * **2. 卖铲子逻辑：** 别人淘金我们卖什么周边服务。
    * **3. 落地执行动作：** 第一步干什么，第二步干什么。

    **模块三：🔭 深度战略研判 (宏观大局)**
    * **1. ⚡ 到底发生了什么？** (背后的商业博弈)
    * **2. 💰 钱流向了哪里？** (赛道吸金逻辑)
    * **3. 👉 我们该怎么干？** (长线建议)
    * **4. 🛑 终极预判** (风险避坑)

    **🔥 输出格式模板：**

    ### 🚀 {report_title} ({beijing_date})
    > 🧠 智能驱动：DeepSeek V3 | 🎯 聚焦赛道：{industry_focus}
    
    #### ⭐ 核心情报内参 (Top 20)
    1. **[政策] 示例标题**
       🔗 [来源媒体](url)
       💡 **解读：** ...
    ... (强制写满 20 条)

    ---
    #### 💰 信息差套利与变现专区
    **套利项目一：[项目名称]**
    * **逻辑拆解：** ...
    * **卖铲子切入点：** ...
    * **极简落地动作：** ...
    
    **套利项目二：[项目名称]**
    ...

    ---
    #### 🔭 深度战略研判
    **1. ⚡ 到底发生了什么？**
    ...
    **2. 💰 钱流向了哪里？**
    ...
    **3. 👉 我们该怎么干？**
    ...
    **4. 🛑 终极预判与避坑：**
    ...
    
    **原始数据投喂：**
    {data_str}
    """
    return call_deepseek(prompt)