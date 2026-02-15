import requests
import json
import os
import feedparser
from tavily import TavilyClient
from datetime import datetime, timedelta, timezone

# =========================================================
# 🔴 核心配置区 (支持 本地硬编码 + GitHub Secrets 双模式)
# =========================================================
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY") or "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"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY") or "sk-gvvsglcyhujlvprlryxtwduxvbgwfyzqngzqesyvwvucjnyw"
BOCHA_API_KEY = os.environ.get("BOCHA_API_KEY") or "sk-2fae396b559249da8dab4fe7de1ae125"

WECOM_WEBHOOK_URL = os.environ.get("WECOM_WEBHOOK_URL") or "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0"
FEISHU_WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL") or "https://open.feishu.cn/open-apis/bot/v2/hook/54e2a16a-8409-46c7-bd62-a169bc3e063f"
# =========================================================

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=8)

# ---------------------------------------------------------
# 🌍 数据源 A: Tavily (国际视野 - 广撒网版)
# ---------------------------------------------------------
def get_tavily_data():
    print("1. 正在全网搜索 (Tavily - 国际视野)...")
    
    if not TAVILY_API_KEY or "在此粘贴" in TAVILY_API_KEY:
        print("⚠️ Tavily Key 未配置，跳过")
        return []
        
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    # 策略：增加 breaking, stock, crisis 等词，确保抓到重磅大新闻
    query = "AI artificial intelligence breaking news stock market crisis breakthrough OpenAI DeepSeek Nvidia Google business impact"
    try:
        # 🔥 提升获取量到 25 条，确保素材库充足
        response = tavily.search(query=query, search_depth="advanced", max_results=25, days=1)
        results = response.get('results', [])
        print(f"✅ Tavily 获取成功: {len(results)} 条")
        return results
    except Exception as e:
        print(f"❌ Tavily 搜索失败: {e}")
        return []

# ---------------------------------------------------------
# 🇨🇳 数据源 B: 博查 Bocha (国内视野 - 广撒网版)
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
    # 策略：聚焦“重磅”、“首发”、“暴跌”、“红利”
    payload = {
        "query": "DeepSeek 商业化 股价暴跌 行业重磅 融资首发 AI落地案例 site:36kr.com OR site:qbitai.com OR site:jiqizhixin.com",
        "freshness": "oneDay",
        # 🔥 提升获取量到 25 条
        "count": 25
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # 路径：data -> webPages -> value
            web_pages = data.get('data', {}).get('webPages', {})
            items_list = web_pages.get('value', [])
            
            results = []
            for item in items_list:
                # 过滤掉标题过短的无效信息
                if len(item.get('name', '')) > 6:
                    results.append({
                        "title": item.get('name'),
                        "url": item.get('url'),
                        "content": item.get('snippet')
                    })
            print(f"✅ Bocha 获取成功: {len(results)} 条")
            return results
        else:
            print(f"❌ Bocha API 错误: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Bocha 请求异常: {e}")
        return []

# ---------------------------------------------------------
# 🛡️ 数据源 C: RSS 兜底
# ---------------------------------------------------------
def get_rss_data():
    print("🔄 正在启动 RSS 兜底机制 (36Kr & IT之家)...")
    rss_sources = ["https://36kr.com/feed", "https://www.ithome.com/rss/"]
    results = []
    try:
        for rss_url in rss_sources:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:10]:
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
# ⚙️ 核心调度逻辑 (汇聚更大的池子)
# ---------------------------------------------------------
def get_realtime_news():
    all_news = []
    
    # 1. 获取 Tavily
    all_news.extend(get_tavily_data())
    
    # 2. 获取 Bocha
    all_news.extend(get_bocha_data())
    
    print(f"📊 原始素材池总数: {len(all_news)} 条")

    # 3. 只有当总数极少时，才用 RSS 凑数 (避免 RSS 的水文稀释高质量搜索结果)
    if len(all_news) < 15:
        print("🛡️ 高价值 API 数据不足，启动 RSS 补充...")
        all_news.extend(get_rss_data())
        
    # 去重
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
# 🧠 DeepSeek 思考与清洗 (严选模式)
# ---------------------------------------------------------
def call_deepseek(prompt):
    print("3. 正在调用 DeepSeek V3 进行深度筛选与排序...")
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
        "max_tokens": 8000
    }
    try:
        # 给足 180秒，让它处理大量数据
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"❌ DeepSeek 接口报错: {response.text}")
            return None
    except Exception as e
