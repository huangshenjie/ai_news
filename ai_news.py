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
# 🌍 数据源 A: Tavily
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
# 🇨🇳 数据源 B: 博查 Bocha
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
# 🧠 DeepSeek 思考与清洗 (重构 Prompt：彻底降维至普通人变现)
# ---------------------------------------------------------
def call_deepseek(prompt):
    print("4. 正在调用 DeepSeek 进行深度推演与降维翻译...")
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
    你是一名极度务实的【{industry_focus}】商业战略顾问兼“草根变现专家”。这里有 {len(news_data)} 条原始资讯。
    请撰写一份《{report_title}》。

    ❌ 致命红线（违反直接任务失败）：
    1. 排版乱码防范： 绝对禁止在输出中使用“$”符号！如果你要表示美元，请直接使用中文“美元”（例如：800美元）。
    2. 禁止偷懒： 模块一必须按编号完整输出 20 条资讯。少一条都不行。
    3. 严禁高大上词汇： 模块二中，绝对禁止出现“融资、算力、企业级部署、GPU矿机、合规、代运营”等普通人无法触碰的词汇。必须基于“无资金、无技术背景、无人脉”的绝对三无前提！

    ✅ 任务要求：
    
    模块一：⭐ 核心情报内参 (强制写满 Top 20)
    * 提取与【{industry_focus}】最相关的情报。
    * 格式： 编号. [标签] 标题 -> 🔗 [来源](url) -> 💡 解读： (商业影响)。

    模块二：💰 普通人无门槛搞钱专区 (喂饭级实操)
    * 必须且只能输出 3 条极度详细的搞钱路子。
    * 必须基于今天的资讯，将高阶技术降维成小白能干的体力活或信息差。
    * 每一条必须包含以下三个要素：
      1. 🎯 核心逻辑：(一句话解释普通人怎么利用免费AI工具套利)
      2. 🛠️ 工具与接单平台：(明确指出用什么免费工具生成，去小红书/闲鱼/淘宝/Fiverr等哪个具体平台获客卖钱)
      3. 👣 极简落地动作：(第一步点什么，第二步发什么，第三步怎么定价)

    模块三：🔭 深度战略研判 (宏观大局)
    * 1. ⚡ 到底发生了什么？ (背后的商业博弈)
    * 2. 💰 钱流向了哪里？ (赛道吸金逻辑)
    * 3. 👉 我们该怎么干？ (长线建议)
    * 4. 🛑 终极预判与避坑： (风险预判)

    🔥 输出格式模板：

    ### 🚀 {report_title} ({beijing_date})
    > 🧠 智能驱动：DeepSeek V3 | 🎯 聚焦赛道：{industry_focus}
    
    #### ⭐ 核心情报内参 (Top 20)
    1. [政策] 示例标题
       🔗 [来源媒体](url)
       💡 解读： ...
    ... (强制写满 20 条)

    ---
    #### 💰 普通人无门槛搞钱专区 (喂饭级实操)
    搞钱路子一：[大白话项目名称，例如：代写小红书AI爆款图文]
    * 🎯 核心逻辑： ...
    * 🛠️ 工具与平台： 使用 [工具名称]，在 [平台名称] 获客。
    * 👣 极简落地动作： 
      - 第一步：...
      - 第二步：...
      - 第三步：定价...
    
    搞钱路子二：[大白话项目名称]
    ...

    搞钱路子三：[大白话项目名称]
    ...

    ---
    #### 🔭 深度战略研判
    1. ⚡ 到底发生了什么？
    ...
    2. 💰 钱流向了哪里？
    ...
    3. 👉 我们该怎么干？
    ...
    4. 🛑 终极预判与避坑：
    ...
    
    原始数据投喂：
    {data_str}
    """

    return call_deepseek(prompt)

# =========================================================
# 🚀 自动化推送模块
# =========================================================

def send_to_wecom(content):
    print("5. 正在推送到企业微信...")
    if not WECOM_WEBHOOK_URL:
        print("⚠️ 未配置企业微信 Webhook，跳过")
        return
    headers = {"Content-Type": "application/json"}
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content}
    }
    try:
        requests.post(WECOM_WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        print("✅ 企业微信推送成功！")
    except Exception as e:
        print(f"❌ 企业微信推送失败: {e}")

def send_to_feishu(content):
    print("6. 正在推送到飞书...")
    if not FEISHU_WEBHOOK_URL:
        print("⚠️ 未配置飞书 Webhook，跳过")
        return
    headers = {"Content-Type": "application/json"}
    payload = {
        "msg_type": "interactive",
        "card": {
            "elements": [{
                "tag": "markdown",
                "content": content
            }]
        }
    }
    try:
        requests.post(FEISHU_WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        print("✅ 飞书推送成功！")
    except Exception as e:
        print(f"❌ 飞书推送失败: {e}")

if __name__ == "__main__":
    print("🕒 检测到自动化任务启动，开始执行每日例行抓取...")
    
    tavily_q = "AI startup funding open-source LLM AI infrastructure monetization generative AI"
    bocha_q = "大模型商业化 算力 DeepSeek落地应用 AI变现 融资"
    rss_sources = ["https://36kr.com/feed", "https://www.ithome.com/rss/"]
    
    industry = "人工智能"
    title = "AI 商业套利与实战内参"

    # 1. 抓取数据
    raw_news = get_realtime_news(tavily_query=tavily_q, bocha_query=bocha_q, rss_urls=rss_sources)
    
    if raw_news:
        # 2. AI 处理并强制生成喂饭级专区
        final_report = ai_process_content(raw_news, industry_focus=industry, report_title=title)
        
        if final_report:
            # 3. 分发到内部群聊
            send_to_wecom(final_report)
            send_to_feishu(final_report)
            print("🎉 每日自动化流程全部执行完毕！")
        else:
            print("❌ AI 报告生成失败，取消推送。")
    else:
        print("❌ 未抓取到有效数据，取消推送。")
