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
# 🌍 数据源 A: Tavily (国际 - 广撒网)
# ---------------------------------------------------------
def get_tavily_data():
    print("1. 正在全网搜索 (Tavily)...")
    if not TAVILY_API_KEY or "在此粘贴" in TAVILY_API_KEY:
        print("⚠️ Tavily Key 未配置，跳过")
        return []
    
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    # 策略：增加 energy, infrastructure, arbitrage 等词，引导搜出基建和套利相关新闻
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
# 🇨🇳 数据源 B: 博查 Bocha (国内 - 广撒网)
# ---------------------------------------------------------
def get_bocha_data():
    print("2. 正在尝试博查搜索 (Bocha)...")
    if not BOCHA_API_KEY or "在此粘贴" in BOCHA_API_KEY:
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
    
    print(f"📊 原始素材池总数: {len(all_news)} 条")

    if len(all_news) < 20:
        print("🛡️ 素材不足，启动 RSS 补充...")
        all_news.extend(get_rss_data())
        
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
# 🧠 DeepSeek 思考与清洗 (Pro Max+ 深度拆解版)
# ---------------------------------------------------------
def call_deepseek(prompt):
    print("3. 正在调用 DeepSeek V3 进行深度筛选与详细解读...")
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
        # 🔥 Token 拉满，防止回答被截断
        "max_tokens": 8000
    }
    try:
        # 🔥 保持 180s 超时
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
    data_str = json.dumps(news_data[:70], ensure_ascii=False)

    # 🔥🔥 核心 Prompt 修改：要求“详细拆解”、“逻辑闭环”、“多路径建议” 🔥🔥
    prompt = f"""
    你是一名**极度务实、擅长深度剖析**的 AI 商业战略顾问。这里有 {len(news_data)} 条原始资讯。
    请撰写一份《AI 全球实战内参》，分为“资讯情报”和“深度研判”两部分。

    **第一部分：资讯情报 (20条)**
    1. **凑齐 20 条：** 按【S级 重磅】、【A级 焦点】、【B级 应用】三层分级。如果 S 级不够，用 A/B 级填满，**严禁少于 20 条**。
    2. **人话解读：** 每条新闻下必须有一句 `💡 解读：`，用大白话解释对行业/个人的具体影响。

    **第二部分：深度战略研判 (必须详细、拆解逻辑)**
    *这是本报告的灵魂，请不要吝啬笔墨，要像“老师傅”带徒弟一样把逻辑讲透。*

    **1. ⚡ 到底发生了什么？ (底层逻辑)**
    不要只重复新闻。要解释表象背后的**博弈逻辑**。
    * 例如：DeepSeek 的低成本不仅仅是省钱，它打破了美国科技巨头的什么垄断？为什么这会让华尔街恐慌？

    **2. 💰 钱流向了哪里？ (必须解释“为什么”)**
    * **硬钱（基建/能源）：** * 不要只说“电力”，要解释：为什么 AI 会导致缺电？为什么风电不行，火电/核电却火了？（提示：解释数据中心的稳定性需求）。
        * 提及“老旧数据中心改造”带来的机会。
    * **软钱（B2B应用）：** * 具体指哪些软件？（例如：法律AI、医疗影像AI）。为什么这些比通用大模型赚钱？
    * **快钱（套利/信息差）：** * **必须详细解释“监管套利”**：举例说明（例如：把国产模型包装成海外壳公司，卖给受限制的地区；或者利用国内外信息差做倒卖）。让读者看懂这个灰色/灰色地带的操作逻辑。

    **3. 👉 我们该怎么干？ (分人群多路径建议)**
    不要只说“去学习”。请针对不同人群给出**具体、可执行**的建议：
    * **路径 A (打工人/转型)：** 比如“学习 ComfyUI 做商业切片”，或者“转行去做 AI 数据中心的运维（蓝领）”。
    * **路径 B (小创业者/生意人)：** 比如“给传统企业（如律所、餐馆）做私有化知识库部署”，解释为什么他们需要这个。
    * **路径 C (投资者/投机者)：** 比如“关注电网设备股”或者“做空硬件泡沫”。

    **4. 🛑 终极总结 (趋势预判)**
    对未来 1-3 年的局势做一个详细推演，而不是一句口号。

    **🔥 输出格式模板：**

    ### 🚀 AI 全球实战内参 ({beijing_date})
    > 🧠 智能驱动：DeepSeek V3 | 🌍 覆盖信源：Tavily (国际) + Bocha (国内)
    
    #### ⭐ 顶级重磅 (Level S - 必读)
    1. **[标签] 标题**
       🔗 [媒体名](url)
       💡 **解读：** ...
    ... (直到凑齐 20 条)

    ---
    #### 🔭 深度战略研判 (逻辑拆解版)
    
    **1. ⚡ 到底发生了什么？**
    ...

    **2. 💰 钱流向了哪里？ (详细拆解)**
    * **硬钱（电力与基建）：** ... (解释为什么流向这里)
    * **快钱（信息差与套利）：** ... (解释具体的操作逻辑)

    **3. 👉 我们该怎么干？ (行动指南)**
    * **路径 A (技术/职场)：** ...
    * **路径 B (生意/副业)：** ...

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
    if not content or not WECOM_WEBHOOK_URL or "在此粘贴" in WECOM_WEBHOOK_URL: return
    print("4.1 推送至企微...")
    # 微信限制 4096 字节，分段推送
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
    print("🚀 启动 AI 情报系统 (深度解读版)...")
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
