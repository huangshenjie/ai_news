import requests
import json
import os
import feedparser
from tavily import TavilyClient
from datetime import datetime, timedelta, timezone

# =========================================================
# 🔴 核心配置区 (支持 本地硬编码 + GitHub Secrets 双模式)
# =========================================================
# 玩法：
# 1. 本地测试时：直接把 Key 填在后面的引号里 (例如 "sk-xxx")
# 2. 上传 GitHub 时：不用改代码，GitHub 会自动读取前面的环境变量
# =========================================================

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "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")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-gvvsglcyhujlvprlryxtwduxvbgwfyzqngzqesyvwvucjnyw")
BOCHA_API_KEY = os.environ.get("BOCHA_API_KEY", "sk-2fae396b559249da8dab4fe7de1ae125")

WECOM_WEBHOOK_URL = os.environ.get("WECOM_WEBHOOK_URL", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0")
FEISHU_WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL", "https://open.feishu.cn/open-apis/bot/v2/hook/54e2a16a-8409-46c7-bd62-a169bc3e063f")

# =========================================================

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=8)

# ---------------------------------------------------------
# 🌍 数据源 A: Tavily (国际视野)
# ---------------------------------------------------------
def get_tavily_data():
    print("1. 正在全网搜索 (Tavily - 国际视野)...")
    
    # 简单的空值检查
    if not TAVILY_API_KEY or "在此粘贴" in TAVILY_API_KEY:
        print("⚠️ Tavily Key 未配置，跳过")
        return []
        
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    # 搜索词优化：覆盖 AI 巨头和技术关键词
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
# 🇨🇳 数据源 B: 博查 Bocha (国内精准 - 已修复结构)
# ---------------------------------------------------------
def get_bocha_data():
    print("2. 正在尝试博查搜索 (Bocha - 国内视野)...")
    
    if not BOCHA_API_KEY or "在此粘贴" in BOCHA_API_KEY:
        print("⚠️ Bocha Key 未配置，跳过")
        return [] 
        
    url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {BOCHA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": "DeepSeek 商业化落地 最新进展 OR OpenAI Sora 最新消息 site:36kr.com OR site:qbitai.com",
        "freshness": "oneDay",
        "count": 10
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # 🔥 核心修复：根据你截图的真实结构提取数据
            # 路径：data -> webPages -> value (列表在这里)
            web_pages = data.get('data', {}).get('webPages', {})
            items_list = web_pages.get('value', [])
            
            results = []
            for item in items_list:
                results.append({
                    "title": item.get('name'),     # 博查返回的是 name
                    "url": item.get('url'),
                    "content": item.get('snippet') # 博查返回的是 snippet
                })
            
            print(f"✅ Bocha 获取成功: {len(results)} 条")
            return results
        else:
            print(f"❌ Bocha API 错误: {response.status_code} - {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Bocha 请求异常: {e}")
        return []

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
# ⚙️ 核心调度逻辑 (混合双打 + 替补)
# ---------------------------------------------------------
def get_realtime_news():
    all_news = []
    
    # 1. 获取 Tavily (国际)
    tavily_data = get_tavily_data()
    all_news.extend(tavily_data)
    
    # 2. 获取 Bocha (国内)
    bocha_data = get_bocha_data()
    all_news.extend(bocha_data)
    
    # 3. 智能判断：如果数据太少 (比如 < 5条)，说明 API 可能都挂了或者没新闻
    #    这时候强制启动 RSS 兜底，保证日报有内容
    if len(all_news) < 5:
        print("🛡️ 检测到 API 数据不足，强制启动 RSS 替补上场...")
        rss_data = get_rss_data()
        all_news.extend(rss_data)
        
    # 简单去重 (按 URL)
    seen_urls = set()
    unique_news = []
    for news in all_news:
        url = news.get('url', '')
        if url and url not in seen_urls:
            unique_news.append(news)
            seen_urls.add(url)
            
    print(f"📊 最终聚合情报数: {len(unique_news)} 条")
    return unique_news

# ---------------------------------------------------------
# 🧠 DeepSeek 思考与清洗
# ---------------------------------------------------------
def call_deepseek(prompt):
    print("3. 正在调用 DeepSeek V3 进行深度分析与排序...")
    
    if not DEEPSEEK_API_KEY or "在此粘贴" in DEEPSEEK_API_KEY:
        print("❌ DeepSeek Key 未配置")
        return None

    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False, 
        "temperature": 0.7, 
        "max_tokens": 8000 # 增加 Token 以支持长日报
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
    > 🧠 智能驱动：DeepSeek V3 | 🌍 信源：Tavily + Bocha + RSS
    
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
    if not content or not WECOM_WEBHOOK_URL or "在此粘贴" in WECOM_WEBHOOK_URL: return
    print("4.1 推送至企微...")
    
    # 分段推送防止截断 (企微限制 4096 字节)
    if len(content.encode('utf-8')) > 4000:
        part1 = content[:3000] + "\n...(下接第二条)..."
        part2 = "...(接上条)...\n" + content[3000:]
        requests.post(WECOM_WEBHOOK_URL, json={"msgtype": "markdown", "markdown": {"content": part1}})
        requests.post(WECOM_WEBHOOK_URL, json={"msgtype": "markdown", "markdown": {"content": part2}})
    else:
        headers = {"Content-Type": "application/json"}
        data = {"msgtype": "markdown", "markdown": {"content": content}}
        try: requests.post(WECOM_WEBHOOK_URL, headers=headers, data=json.dumps(data))
        except: pass

def push_feishu(content):
    if not content or not FEISHU_WEBHOOK_URL or "在此粘贴" in FEISHU_WEBHOOK_URL: return
    print("4.2 推送至飞书...")
    current_time = get_beijing_time().strftime('%Y-%m-%d %H:%M')
    
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

# ---------------------------------------------------------
# 🚀 主程序入口
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🚀 启动 Max 版情报系统...")
    
    # 1. 智能获取数据 (Tavily + Bocha + RSS)
    raw_data = get_realtime_news()
    
    if raw_data:
        # 2. AI 排序与生成 (20条+)
        final_text = ai_process_content(raw_data)
        
        if final_text:
            # 3. 推送
            push_wechat(final_text)
            push_feishu(final_text)
            print("✅ 任务全部完成")
        else:
            print("⚠️ DeepSeek 内容生成为空")
    else:
        print("❌ 严重错误：全网无数据")
