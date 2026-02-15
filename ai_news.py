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
    # 关键词优化：增加 'money', 'business', 'startups' 引导商业新闻
    query = "AI Artificial Intelligence news business impact startups money trends OpenAI DeepSeek Nvidia Google"
    try:
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
        "query": "DeepSeek 商业化 赚钱机会 AI创业 融资快讯 site:36kr.com OR site:qbitai.com OR site:jiqizhixin.com",
        "freshness": "oneDay",
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
    all_news.extend(get_tavily_data())
    all_news.extend(get_bocha_data())
    
    if len(all_news) < 5:
        print("🛡️ API 数据不足，强制启动 RSS 补充...")
        all_news.extend(get_rss_data())
        
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
# 🧠 DeepSeek 思考与清洗 (Prompt 4维度升级版)
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
    data_str = json.dumps(news_data[:50], ensure_ascii=False)

    # 🔥 核心修改：Prompt 强制要求 4 维度战略研判
    prompt = f"""
    你是一名残酷、挑剔且极具商业洞察力的顶级 AI 战略顾问。这里有 {len(news_data)} 条关于 AI 的原始资讯。
    请从中提炼出 **20 条** 最有价值的情报，并撰写一份深度的《AI 全球实战内参》。

    **❌ 严禁出现的问题：**
    1. 标题空洞（如“XX发布新功能”）。
    2. 标签笼统（如 [技术]）。
    3. **战略研判模糊**（严禁写“我们需要关注XX”，要写“现在立刻去更XX”）。

    **✅ 必须执行的标准：**
    1. **资讯部分**：标题必须包含【谁 + 做了什么 + 具体影响/数据】。链接必须另起一行，格式为 `🔗 [媒体名](url)`。
    2. **战略研判部分（核心）**：必须严格按照以下四个维度进行深度剖析：
       - **维度一：⚡ 格局重塑** (行业现状/巨头博弈/护城河变化)
       - **维度二：🌪️ 崛起风口** (红利机会/资金流向/信息差)
       - **维度三：💰 落地变现** (普通人/开发者/创业者 具体能做什么？怎么搞钱？)
       - **维度四：🎯 核心结论** (一句话总结今日风向)

    **🔥 输出格式模板（请严格模仿）：**

    ### 🚀 AI 全球实战内参 ({beijing_date})
    > 🧠 智能驱动：DeepSeek V3 | 🌍 覆盖信源：Tavily (国际) + Bocha (国内)
    
    #### ⭐ 顶级重磅 (Top 3)
    1. **[芯片封锁] 英伟达特供版 H20 芯片被曝停供，国内大模型训练成本或上涨 30%**
       🔗 [36氪](https://...)
    ...
    
    #### 📰 行业必读 (Top 4-20)
    4. **[融资风向] 只做 AI 应用的 Jasper 估值缩水 40%，SaaS 壳公司泡沫破裂**
       🔗 [TheInfo](https://...)
    ...
    
    ---
    #### 🔭 深度战略研判
    
    **1. ⚡ 格局重塑：**
    OpenAI 与 Google 的模型护城河已断裂。DeepSeek 的开源证明了“蒸馏+微调”可以低成本复刻 95% 的能力。现在的战场从“拼模型参数”转移到了“拼私有数据”和“端侧部署”。

    **2. 🌪️ 崛起风口：**
    **“企业私有化部署”** 是当前最大的红利。因为数据安全顾虑，大量公司不敢用 ChatGPT，但急需 DeepSeek 本地版。懂 Docker 部署和微调的技术人员，现在是市场上的香饽饽。

    **3. 💰 落地变现：**
    * **针对普通人：** 别再学 Prompt 工程了，去学 ComfyUI 工作流和 AI 视频生成，这是接单变现最快的领域。
    * **针对创业者：** 放弃“套壳 Chat”，去做“垂直行业的数据清洗服务”。所有大模型公司都缺高质量数据，这是一门卖铲子的生意。

    **4. 🎯 核心结论：**
    模型不值钱了，数据和场景才是黄金。别造轮子，去造车。
    
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
