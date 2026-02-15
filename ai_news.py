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
    except Exception as e:
        print(f"❌ DeepSeek 请求异常: {e}")
        return None

def ai_process_content(news_data):
    if not news_data: return None
    
    beijing_date = get_beijing_time().strftime('%Y-%m-%d')
    
    # 🔥 投喂量拉满：给 70 条，让它从中挑最好的 20 条
    data_str = json.dumps(news_data[:70], ensure_ascii=False)

    # 🔥🔥 严选 Prompt：按热度排序，拒绝凑数 🔥🔥
    prompt = f"""
    你是一名**极度挑剔、只关注重磅消息**的 AI 首席主编。这里有 {len(news_data)} 条原始资讯。
    你的任务是从中筛选出 **Top 20** 条最有价值的情报，并按**【影响力/热度】降序排列**。

    **❌ 严禁（凑数行为）：**
    1. **剔除鸡毛蒜皮：** 某公司发布了一个小补丁、某人发表了一句无关痛痒的话 -> **直接删掉**。
    2. **剔除重复冗余：** 同一件大事如果有多个来源，只保留分析最深度的一个。
    3. **严禁编造：** 如果有价值的新闻不足 20 条，宁可只写 15 条，也不要编造或凑数。

    **✅ 必须执行的标准（按热度排序）：**
    1. **优先级逻辑：** - **Level S (最高):** 导致股市暴跌/暴涨、国家级政策禁令、颠覆性技术发布（如 GPT-5）。
       - **Level A (中等):** 巨头战略转向、亿级融资、重大高管变动。
       - **Level B (一般):** 有趣的新应用、行业数据报告。
    2. **资讯格式：** - 标题 = 【标签】+ 核心事实 + **(数据/影响)**。
       - 必须在标题下方换行附带链接：`🔗 [媒体名](url)`。

    **🔥 输出格式模板：**

    ### 🚀 AI 全球实战内参 ({beijing_date})
    > 🧠 智能驱动：DeepSeek V3 | 🌍 覆盖信源：Tavily (国际) + Bocha (国内)
    
    #### ⭐ 顶级重磅 (Level S - 必读)
    1. **[股市震荡] DeepSeek 效应持续，英伟达市值单日蒸发 2000 亿，华尔街下调 AI 硬件评级**
       🔗 [Bloomberg](url)
    2. **[技术封锁] 美国商务部拟对中国 AI 模型实施“字节跳动式”禁令，禁止云厂商提供算力**
       🔗 [Reuters](url)
    ...
    
    #### 📰 行业焦点 (Level A - 核心动态)
    ...
    
    #### 💡 创新与应用 (Level B - 机会前瞻)
    ...
    
    ---
    #### 🔭 深度战略研判 (通俗版)
    
    **1. ⚡ 到底发生了什么？ (本质)**
    （用大白话解释今天的头条新闻背后的博弈。谁动了谁的蛋糕？）

    **2. 💰 钱流向了哪里？ (风口)**
    （指出资金正在疯狂涌入的具体细分赛道）

    **3. 👉 我们该怎么干？ (实操)**
    * **普通打工人：** ...
    * **创业者/搞钱党：** ...

    **4. 🛑 最终建议：**
    （一句话犀利总结）
    
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
    print("🚀 启动 AI 情报系统 (严选版)...")
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
