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
# 🌍 数据源 A: Tavily (国际视野 - 扩容版)
# ---------------------------------------------------------
def get_tavily_data():
    print("1. 正在全网搜索 (Tavily - 国际视野)...")
    
    if not TAVILY_API_KEY or "在此粘贴" in TAVILY_API_KEY:
        print("⚠️ Tavily Key 未配置，跳过")
        return []
        
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    # 优化：关键词增加 'impact', 'price', 'release' 等词，引导搜出具体实锤新闻
    query = "AI Artificial Intelligence news impact pricing release OpenAI DeepSeek Nvidia Google business trends"
    try:
        # 🔥 修改点 1：max_results 提升到 20
        response = tavily.search(query=query, search_depth="advanced", max_results=20, days=1)
        results = response.get('results', [])
        print(f"✅ Tavily 获取成功: {len(results)} 条")
        return results
    except Exception as e:
        print(f"❌ Tavily 搜索失败: {e}")
        return []

# ---------------------------------------------------------
# 🇨🇳 数据源 B: 博查 Bocha (国内视野 - 扩容版)
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
        "query": "DeepSeek 商业化 价格战 算力成本 OpenAI 竞争 site:36kr.com OR site:qbitai.com OR site:jiqizhixin.com",
        "freshness": "oneDay",
        # 🔥 修改点 2：count 提升到 20
        "count": 20
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            web_pages = data.get('data', {}).get('webPages', {})
            items_list = web_pages.get('value', [])
            
            results = []
            for item in items_list:
                # 简单的清洗，去掉太短的标题
                if len(item.get('name', '')) > 5:
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
# ⚙️ 核心调度逻辑
# ---------------------------------------------------------
def get_realtime_news():
    all_news = []
    
    # 1. 获取 Tavily (20条)
    all_news.extend(get_tavily_data())
    
    # 2. 获取 Bocha (20条)
    all_news.extend(get_bocha_data())
    
    # 3. 只有当两者加起来都很少时，才用 RSS
    if len(all_news) < 5:
        print("🛡️ API 数据不足，强制启动 RSS 补充...")
        all_news.extend(get_rss_data())
        
    # 去重
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
# 🧠 DeepSeek 思考与清洗 (Prompt 大升级)
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
        "max_tokens": 8000
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
    # 增加投喂量，给 DeepSeek 更多素材
    data_str = json.dumps(news_data[:50], ensure_ascii=False)

    # 🔥 修改点 3：Prompt 究极进化版
    prompt = f"""
    你是一名残酷、挑剔且极具商业洞察力的科技情报分析师。这里有 {len(news_data)} 条关于 AI 的原始资讯。
    请从中提炼出 **20 条** 最有价值的情报，撰写一份《AI 全球实战内参》。

    **❌ 严禁出现的问题（出现则不及格）：**
    1. **标题空洞：** 严禁使用“XX计划启动”、“XX发布新功能”这种正确的废话。
    2. **标签笼统：** 严禁使用 [市场]、[技术] 这种大词。
    3. **丢失链接：** 每一条新闻必须附带原始链接。

    **✅ 必须执行的标准：**
    1. **标题信息量爆炸：** 标题必须包含【谁(Who) + 做了什么(Action) + 具体数据/后果(Result)】。
       - *反例*：太空数据中心计划启动，应对 AI 高能耗挑战。
       - *正例*：**Lomen 启动首个太空数据中心，利用太阳能降低 40% AI 训练成本。**
    2. **标签精准犀利：** 使用具体领域的细分标签。
       - *正例*：**[算力降本]**、**[端侧模型]**、**[监管重拳]**、**[人才挖角]**。
    3. **格式严格统一：** 必须在标题下方另起一行放链接，格式为 `🔗 [媒体名](url)`。

    **🔥 输出格式模板（请严格模仿）：**

    ### 🚀 AI 全球实战内参 ({beijing_date})
    > 🧠 智能驱动：DeepSeek V3 | 🌍 覆盖信源：Tavily (国际) + Bocha (国内)
    
    #### ⭐ 顶级重磅 (Top 3)
    1. **[芯片封锁] 英伟达特供版 H20 芯片被曝停供，国内大模型训练成本或上涨 30%**
       🔗 [36氪](https://...)
    2. **[模型价格战] DeepSeek API 降价 50% 倒逼 OpenAI 跟进，每百万 Token 跌破 1 美元**
       🔗 [TechCrunch](https://...)
    ...
    
    #### 📰 行业必读 (Top 4-20)
    4. **[融资风向] 只做 AI 应用的 Jasper 估值缩水 40%，SaaS 壳公司泡沫破裂**
       🔗 [TheInfo](https://...)
    ...
    
    ---
    #### 🔭 深度战略研判
    （用一段话犀利点评今日的行业风向，指出一个被忽视的搞钱机会）
    
    **原始数据投喂：**
    {data_str}
    """
    return call_deepseek(prompt)

# ---------------------------------------------------------
# 📢 推送通道
# ---------------------------------------------------------
def push_wechat(content):
    if not content or not WECOM_WEBHOOK_URL or "在此粘贴" in WECOM_WEBHOOK_URL: return
    print("4.1 推送至企微...")
    if len(content.encode('utf-8')) > 4000:
        part1 = content[:3000] + "\n...(下接第二条)..."
        part2 = "...(接上条)...\n" + content[3000:]
        requests.post(WECOM_WEBHOOK_URL, json={"msgtype": "markdown", "markdown": {"content": part1}})
        requests.post(WECOM_WEBHOOK_URL, json={"msgtype": "markdown", "markdown": {"content": part2}})
    else:
        requests.post(WECOM_WEBHOOK_URL, json={"msgtype": "markdown", "markdown": {"content": content}})

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
                "title": {"content": "🚀 AI 全球实战内参", "tag": "plain_text"}
            },
            "elements": [
                {"tag": "markdown", "content": content},
                {"tag": "note", "elements": [{"tag": "plain_text", "content": f"更新: {current_time}"}]}
            ]
        }
    }
    requests.post(FEISHU_WEBHOOK_URL, json=payload)

# ---------------------------------------------------------
# 🚀 主程序入口
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🚀 启动 Pro Max 版情报系统...")
    raw_data = get_realtime_news()
    if raw_data:
        final_text = ai_process_content(raw_data)
        if final_text:
            push_wechat(final_text)
            push_feishu(final_text)
            print("✅ 任务完成")
        else:
            print("⚠️ DeepSeek 生成为空")
    else:
        print("❌ 无数据")
