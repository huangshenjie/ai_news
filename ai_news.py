import requests
import json
import os
import feedparser
from tavily import TavilyClient
from datetime import datetime, timedelta, timezone

# =========================================================
# 🔴 核心配置区 (建议使用 Secrets，这里为了方便调试先留空)
# =========================================================
# 优先从环境变量读取，如果本地测试没配环境变量，就会使用后面的默认值
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "在此粘贴Tavily_Key")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-gvvsglcyhujlvprlryxtwduxvbgwfyzqngzqesyvwvucjnyw")
BOCHA_API_KEY = os.environ.get("BOCHA_API_KEY", "sk-2fae396b559249da8dab4fe7de1ae125") 

WECOM_WEBHOOK_URL = os.environ.get("WECOM_WEBHOOK_URL", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0")
FEISHU_WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL", "https://open.feishu.cn/open-apis/bot/v2/hook/54e2a16a-8409-46c7-bd62-a169bc3e063f")
# =========================================================

def get_beijing_time():
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=8)

# ---------------------------------------------------------
# 🌍 数据源 A: Tavily (国际/技术深度)
# ---------------------------------------------------------
def get_tavily_data():
    print("1. 正在全网搜索 (Tavily - 国际视野)...")
    if "在此粘贴" in TAVILY_API_KEY or not TAVILY_API_KEY:
        print("⚠️ Tavily Key 未配置，跳过")
        return []
        
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    # 增加搜索深度和数量
    query = "AI Artificial Intelligence news latest trends OpenAI DeepSeek Google Nvidia updates"
    try:
        response = tavily.search(query=query, search_depth="advanced", max_results=15, days=1)
        results = response.get('results', [])
        print(f"✅ Tavily 获取成功: {len(results)} 条")
        return results
    except Exception as e:
        print(f"❌ Tavily 搜索失败: {e}")
        return []

# ---------------------------------------------------------
# 🇨🇳 数据源 B: 博查 Bocha (国内/精准)
# ---------------------------------------------------------
def get_bocha_data():
    print("2. 正在尝试博查搜索 (Bocha - 国内视野)...")
    if "在此粘贴" in BOCHA_API_KEY or not BOCHA_API_KEY:
        print("⚠️ Bocha Key 未配置，准备启动 RSS 替补")
        return None # 返回 None 表示“不可用”，触发 RSS
        
    url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {BOCHA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": "人工智能 AI 行业动态 DeepSeek 商业落地 OpenAI 最新消息 site:36kr.com OR site:ithome.com OR site:jiqizhixin.com",
        "freshness": "oneDay",
        "count": 15 # 获取 15 条
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # 博查返回结构解析
            results = []
            for item in data.get('data', []):
                results.append({
                    "title": item.get('name') or item.get('title'),
                    "url": item.get('url'),
                    "content": item.get('snippet') or item.get('summary')
                })
            print(f"✅ Bocha 获取成功: {len(results)} 条")
            return results
        else:
            print(f"❌ Bocha API 错误: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Bocha 请求异常: {e}")
        return None

# ---------------------------------------------------------
# 🛡️ 数据源 C: RSS 兜底 (36Kr/IT之家)
# ---------------------------------------------------------
def get_rss_data():
    print("🔄 正在启动 RSS 兜底机制 (36Kr & IT之家)...")
    rss_sources = [
        "https://36kr.com/feed",
        "https://www.ithome.com/rss/"
    ]
    results = []
    try:
        for rss_url in rss_sources:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:10]: # 每个源取10条
                results.append({
                    "title": entry.title,
                    "url": entry.link,
                    "content": entry.summary[:200] if hasattr(entry, 'summary') else entry.title
                })
        print(f"✅ RSS 获取成功: {len(results)} 条")
        return results
    except Exception as e:
        print(f"❌ RSS 抓取失败: {e}")
        return []

# ---------------------------------------------------------
# ⚙️ 核心调度逻辑 (双核 + 自动降级)
# ---------------------------------------------------------
def get_realtime_news():
    all_news = []
    
    # 1. 并发获取 Tavily
    tavily_data = get_tavily_data()
    all_news.extend(tavily_data)
    
    # 2. 尝试获取 Bocha
    bocha_data = get_bocha_data()
    
    # 3. 逻辑分支：Bocha 是否可用？
    if bocha_data is not None and len(bocha_data) > 0:
        # 场景 A: 博查可用 -> 强强联手
        print("🚀 模式：Tavily + Bocha 双核驱动")
        all_news.extend(bocha_data)
    else:
        # 场景 B: 博查不可用/失败 -> 启用 RSS 替补
        print("🛡️ 模式：Bocha 缺位，RSS 替补上场")
        rss_data = get_rss_data()
        all_news.extend(rss_data)
    
    # 4. 终极兜底：如果 Tavily 也挂了，确保至少有 RSS 数据
    if len(all_news) == 0:
        print("⚠️ 警告：所有商业 API 均失败，强制重试 RSS...")
        all_news.extend(get_rss_data())
        
    # 去重逻辑 (简单按链接去重)
    seen_urls = set()
    unique_news = []
    for news in all_news:
        if news['url'] not in seen_urls:
            unique_news.append(news)
            seen_urls.add(news['url'])
            
    print(f"📊 最终聚合情报数: {len(unique_news)} 条")
    return unique_news

# ---------------------------------------------------------
# 🧠 DeepSeek 思考与清洗
# ---------------------------------------------------------
def call_deepseek(prompt):
    print("3. 正在调用 DeepSeek V3 进行深度分析与排序...")
    if "在此粘贴" in DEEPSEEK_API_KEY:
        print("❌ DeepSeek Key 未配置")
        return None

    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False, 
        "temperature": 0.7, 
        "max_tokens": 8000 # 🔥 增加 Token 上限，确保能写完 20 条
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"❌ DeepSeek 接口报错: {response.text}")
            return None
    except Exception as e:
        print(f"网络请求异常: {e}")
        return None

def ai_process_content(news_data):
    if not news_data: return None
    
    beijing_date = get_beijing_time().strftime('%Y-%m-%d')
    # 截取前 40 条投喂，防止超长
    data_str = json.dumps(news_data[:40], ensure_ascii=False)

    prompt = f"""
    你是一名顶级 AI 战略顾问。这里有来自全球 ({len(news_data)}条) 关于 AI、OpenAI、DeepSeek 的最新混合资讯。
    
    🔥 **你的任务：**
    1. **去重与清洗**：合并相似内容，剔除广告。
    2. **热门排序**：根据【行业影响力】和【商业价值】进行降序排列。越重磅的新闻越靠前。
    3. **输出数量**：**必须输出 20 条以上** 的核心情报（如果内容足够）。
    
    🔥 **输出格式要求**：
    ### 🚀 AI 全球情报内参 ({beijing_date})
    > 🧠 智能驱动：DeepSeek V3 | 🌍 信源：Tavily + Bocha/RSS
    
    #### ⭐ 顶级重磅 (Top 3)
    1. **[标签] 标题...**
    ...
    
    #### 📰 行业必读 (Top 4-20+)
    4. **[标签] ...**
    ...
    20. **[标签] ...**
    
    ---
    #### 🔭 深度战略研判
    ...
    
    **原始数据：**
    {data_str}
    """
    return call_deepseek(prompt)

# ---------------------------------------------------------
# 📢 推送通道 (飞书/企微)
# ---------------------------------------------------------
def push_wechat(content):
    if not content or "在此粘贴" in WECOM_WEBHOOK_URL: return
    print("4.1 推送至企微...")
    # 分段推送防止截断
    if len(content.encode('utf-8')) > 4000:
        # 简单逻辑：如果太长，先发前 3000 字
        part1 = content[:3000] + "\n...(下接第二条)..."
        part2 = "...(接上条)...\n" + content[3000:]
        requests.post(WECOM_WEBHOOK_URL, json={"msgtype": "markdown", "markdown": {"content": part1}})
        requests.post(WECOM_WEBHOOK_URL, json={"msgtype": "markdown", "markdown": {"content": part2}})
        return

    headers = {"Content-Type": "application/json"}
    data = {"msgtype": "markdown", "markdown": {"content": content}}
    try: requests.post(WECOM_WEBHOOK_URL, headers=headers, data=json.dumps(data))
    except: pass

def push_feishu(content):
    if not content or "在此粘贴" in FEISHU_WEBHOOK_URL: return
    print("4.2 推送至飞书...")
    current_time = get_beijing_time().strftime('%Y-%m-%d %H:%M')
    
    # 飞书卡片构建
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {"content": "🚀 AI 全球情报内参 (Max版)", "tag": "plain_text"}
            },
            "elements": [
                {"tag": "markdown", "content": content},
                {"tag": "note", "elements": [{"tag": "plain_text", "content": f"更新: {current_time}"}]}
            ]
        }
    }
    try: requests.post(FEISHU_WEBHOOK_URL, json=payload)
    except: pass

if __name__ == "__main__":
    print("🚀 启动 Max 版情报系统...")
    
    # 1. 智能获取数据
    raw_data = get_realtime_news()
    
    if raw_data:
        # 2. AI 排序与生成 (20条+)
        final_text = ai_process_content(raw_data)
        
        if final_text:
            push_wechat(final_text)
            push_feishu(final_text)
            print("✅ 任务完成")
        else:
            print("⚠️ 内容生成为空")
    else:
        print("❌ 严重错误：全网无数据")
