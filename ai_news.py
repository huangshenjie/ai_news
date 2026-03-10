import requests
import json
import os
import feedparser
from tavily import TavilyClient
from datetime import datetime, timedelta, timezone

# =========================================================
# 🔴 核心配置区 (环境变量或直接替换字符串)
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
# 🌍 数据源 A: Tavily (全网英文/前沿搜索)
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
# 🇨🇳 数据源 B: 博查 Bocha (国内商业落地搜索)
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
# 🛡️ 数据源 C: RSS (硬核科技资讯源)
# ---------------------------------------------------------
def get_rss_data(rss_sources=None):
    print("3. 正在获取 RSS 深度资讯...")
    if not rss_sources:
        rss_sources = ["https://36kr.com/feed", "https://www.ithome.com/rss/"]
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
# 🧠 DeepSeek 思考与清洗 (终极防偷懒引擎)
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
    你是一名极其冷酷、务实的【{industry_focus}】商业战略顾问兼“草根变现专家”。
    这里有 {len(news_data)} 条原始资讯。请撰写一份《{report_title}》。

    ❌ 致命红线（违反直接任务失败）：
    1. 排版乱码防范：绝对禁止在输出中使用“$”符号！使用中文“美元”代替。
    2. 严禁偷懒与敷衍：每一个模块必须极其详尽！如果出现一笔带过、字数过少、或者结构缺失，你将被直接淘汰。
    3. 严禁高大上词汇：第二和第三部分，必须基于“无资金、无技术背景、无人脉”的草根视角。严禁提“买算力、做大模型微调、企业级融资”等废话。

    ✅ 任务要求与排版顺序：

    第一部分：🔭 深度战略研判 (宏观大局，绝对不准敷衍)
    * 必须深度剖析，强迫自己给出具体的逻辑链条。
    * 包含三个维度，每个维度必须有具体事实支撑：
      1. ⚡ 到底发生了什么？ (提炼出今天资讯背后最核心的商业博弈)
      2. 💰 钱流向了哪里？ (明确指出当前热钱正在涌入的具体细分赛道)
      3. 👉 我们该怎么干？ (给出未来1-3个月的战术定向)

    第二部分：💰 普通人无门槛搞钱专区 (必须且只能是 3 个实操案例)
    * 基于今天的资讯，给出 3 个小白能立马干的搞钱案例。
    * 每个案例必须包含：
      - 🎯 核心逻辑：一句话解释怎么套利。
      - 🛠️ 工具与接单平台：具体用什么免费工具，去哪个平台卖。
      - 👣 极简落地动作：第一步、第二步、第三步（必须包含具体定价和交付标准）。

    第三部分：🛑 散户入局 AI 的 3 个致命避坑指南 (严禁说正确的废话)
    * 必须且只能输出 3 个具体的避坑指南。
    * 直击普通人做AI最容易踩的坑（比如盲目报课、买高价API套壳、重资产投入等）。
    * 每个指南必须严格遵循以下三段式结构：
      - 🕳️ 陷阱表象：(新手在市面上看到了什么诱惑)
      - 🩸 致命逻辑：(为什么按照表象去做一定会亏钱)
      - 🛡️ 破局自保：(正确的替代做法是什么)

    🔥 输出格式模板 (必须严格按此格式输出)：

    ### 🚀 {report_title} ({beijing_date})
    > 🧠 智能驱动：DeepSeek V3 | 🎯 聚焦赛道：{industry_focus}
    
    #### 🔭 一、 深度战略研判
    **1. ⚡ 到底发生了什么？**
    (在此处输出深度分析，不少于80字...)

    **2. 💰 钱流向了哪里？**
    (在此处输出资金动向研判，不少于80字...)

    **3. 👉 我们该怎么干？**
    (在此处输出宏观战术指南，不少于80字...)

    ---
    #### 💰 二、 普通人无门槛搞钱专区 (3个落地案例)
    **案例一：[填入大白话项目名称]**
    * 🎯 **核心逻辑**：...
    * 🛠️ **工具与平台**：使用 [工具名称]，在 [接单平台] 获客。
    * 👣 **极简落地动作**： 
      - 第一步：...
      - 第二步：...
      - 第三步：定价与交付...
    
    **案例二：[填入大白话项目名称]**
    (重复上述结构...)

    **案例三：[填入大白话项目名称]**
    (重复上述结构...)

    ---
    #### 🛑 三、 散户入局 AI 的 3 个致命避坑指南
    **避坑一：[填入具体的坑位名称，如：警惕“一键生成数字人”高价课]**
    * 🕳️ **陷阱表象**：...
    * 🩸 **致命逻辑**：...
    * 🛡️ **破局自保**：...

    **避坑二：[填入具体的坑位名称]**
    (重复上述结构...)

    **避坑三：[填入具体的坑位名称]**
    (重复上述结构...)
    
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
    bocha_q = "大模型商业化 算力 DeepSeek落地应用 AI变现 避坑"
    rss_sources = ["https://36kr.com/feed", "https://www.ithome.com/rss/"]
    
    industry = "人工智能"
    title = "AI 散户搞钱与避坑内参"

    # 1. 抓取数据
    raw_news = get_realtime_news(tavily_query=tavily_q, bocha_query=bocha_q, rss_urls=rss_sources)
    
    if raw_news:
        # 2. AI 处理并强制生成战略、喂饭实操与避坑指南
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
