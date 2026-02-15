import requests
import json
import os
import feedparser
from tavily import TavilyClient
from datetime import datetime, timedelta, timezone

# =========================================================
# 🔴 核心配置区 (生产环境版：仅从环境变量读取)
# =========================================================
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
BOCHA_API_KEY = os.environ.get("BOCHA_API_KEY")

WECOM_WEBHOOK_URL = os.environ.get("WECOM_WEBHOOK_URL")
FEISHU_WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL")
# =========================================================

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=8)

# ---------------------------------------------------------
# 🌍 数据源 A: Tavily
# ---------------------------------------------------------
def get_tavily_data():
    print("1. 正在全网搜索 (Tavily)...")
    if not TAVILY_API_KEY:
        print("⚠️ Tavily Key 未配置，跳过")
        return []
    
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    query = "AI artificial intelligence breaking news energy crisis infrastructure arbitrage stock market business impact OpenAI DeepSeek"
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
def get_bocha_data():
    print("2. 正在尝试博查搜索 (Bocha)...")
    if not BOCHA_API_KEY:
        print("⚠️ Bocha Key 未配置，跳过")
        return [] 
        
    url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {BOCHA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": "DeepSeek 商业化 算力电力 监管套利 行业重磅 融资首发 AI落地案例 site:36kr.com OR site:qbitai.com OR site:jiqizhixin.com",
        "freshness": "oneDay",
        "count": 25
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            web_pages = data.get('data', {}).get('webPages', {})
            items_list = web_pages.get('value', [])
            results = []
            for item in items_list:
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
# 🛡️ 数据源 C: RSS
# ---------------------------------------------------------
def get_rss_data():
    print("3. 正在获取 RSS 深度资讯 (36Kr & IT之家)...")
    rss_sources = ["https://36kr.com/feed", "https://www.ithome.com/rss/"]
    results = []
    try:
        for rss_url in rss_sources:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:15]:
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
    all_news.extend(get_tavily_data())
    all_news.extend(get_bocha_data())
    all_news.extend(get_rss_data())
    
    print(f"📊 原始素材池总数: {len(all_news)} 条")
        
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
# 🧠 DeepSeek 思考与清洗 (防偷懒优化版)
# ---------------------------------------------------------
def call_deepseek(prompt):
    print("4. 正在调用 DeepSeek V3 进行深度筛选与详细解读...")
    if not DEEPSEEK_API_KEY:
        print("❌ DeepSeek Key 未配置")
        return None

    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False, 
        "temperature": 0.7, 
        # Token 保持最大，防止物理截断
        "max_tokens": 8000
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"❌ DeepSeek 接口报错: {response.text}")
            return None
    except Exception as e:
        print(f"❌ DeepSeek 请求异常: {e}")
        return None

def ai_process_content(news_data):
    if not news_data: return None
    
    beijing_date = get_beijing_time().strftime('%Y-%m-%d')
    data_str = json.dumps(news_data[:80], ensure_ascii=False)

    # 🔥🔥 核心 Prompt 修改：加入“防偷懒”死命令 🔥🔥
    prompt = f"""
    你是一名**极度务实、擅长深度剖析**的 AI 商业战略顾问。这里有 {len(news_data)} 条原始资讯。
    请撰写一份《AI 全球实战内参》。

    **❌ 绝对禁止（违反直接不合格）：**
    1. **禁止偷懒/截断：** 严禁输出“限于篇幅”、“仅展示部分”等废话。**必须完整输出 20 条，少一条都不行！**
    2. **禁止合规风险：** 描述灰色产业时，严禁使用“伪装/倒卖/黑市”等词，必须改用“数据资产化/合规架构/监管差异化运营”等商业术语。

    **✅ 任务要求：**
    
    **第一部分：资讯情报 (必须满 20 条)**
    * 按【S级 重磅】、【A级 焦点】、【B级 应用】三层分级。
    * **数量强制：** 必须从 1 列到 20。如果 S 级不够，就用 A/B 级填满。
    * **格式：** 标题 + 链接 + `💡 解读：`(大白话解释影响)。

    **第二部分：深度战略研判 (拆解逻辑)**
    * **1. ⚡ 到底发生了什么？** (解释背后的博弈)
    * **2. 💰 钱流向了哪里？** (解释基建/能源/B2B/套利背后的为什么)
    * **3. 👉 我们该怎么干？** (针对打工人/创业者/投资者的具体建议)
    * **4. 🛑 终极总结** (趋势预判)

    **🔥 输出格式模板：**

    ### 🚀 AI 全球实战内参 ({beijing_date})
    > 🧠 智能驱动：DeepSeek V3 | 🌍 覆盖信源：Tavily + Bocha + RSS
    
    #### ⭐ 顶级重磅 (Level S - 必读)
    1. **[标签] 标题**
       🔗 [媒体名](url)
       💡 **解读：** ...
    ...
    (中间不要省略，一直写到第 20 条)
    ...
    20. **[标签] 标题**
       🔗 [媒体名](url)
       💡 **解读：** ...

    ---
    #### 🔭 深度战略研判 (逻辑拆解版)
    
    **1. ⚡ 到底发生了什么？**
    ...

    **2. 💰 钱流向了哪里？ (详细拆解)**
    ...
    * **快钱（信息差与套利）：** ... (注意使用合规术语)

    **3. 👉 我们该怎么干？ (行动指南)**
    ...

    **4. 🛑 终极总结：**
    ...
    
    **原始数据投喂：**
    {data_str}
    """
    return call_deepseek(prompt)

# ---------------------------------------------------------
# 📢 推送通道
# ---------------------------------------------------------
def push_wechat(content):
    if not content or not WECOM_WEBHOOK_URL: return
    print("5.1 推送至企微...")
    # 微信限制 4096 字节，分段推送
    if len(content.encode('utf-8')) > 4000:
        part1 = content[:3000] + "\n...(下接第二条)..."
        part2 = "...(接上条)...\n" + content[3000:]
        requests.post(WECOM_WEBHOOK_URL, json={"msgtype": "markdown", "markdown": {"content": part1}})
        requests.post(WECOM_WEBHOOK_URL, json={"msgtype": "markdown", "markdown": {"content": part2}})
    else:
        requests.post(WECOM_WEBHOOK_URL, json={"msgtype": "markdown", "markdown": {"content": content}})

def push_feishu(content):
    if not content or not FEISHU_WEBHOOK_URL: return
    print("5.2 推送至飞书...")
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

if __name__ == "__main__":
    print("🚀 启动 AI 情报系统 (防偷懒 + 安全版)...")
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
