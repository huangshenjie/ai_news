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
    # 关键词优化：增加 'money', 'business', 'jobs' 引导更接地气的新闻
    query = "AI Artificial Intelligence news business impact jobs money trends OpenAI DeepSeek Nvidia Google"
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
        "query": "DeepSeek 商业化 赚钱机会 AI创业 融资快讯 行业变局 site:36kr.com OR site:qbitai.com OR site:jiqizhixin.com",
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
# 🧠 DeepSeek 思考与清洗 (Pro Max 人话版)
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
        # 保持 180s 超时设置，确保思考充分
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
    # 保持 35 条投喂量
    data_str = json.dumps(news_data[:35], ensure_ascii=False)

    # 🔥🔥 核心 Prompt 修改：要求“说人话”且“逻辑清晰” 🔥🔥
    prompt = f"""
    你是一名**极度务实、拒绝废话**的 AI 商业情报专家。这里有 {len(news_data)} 条关于 AI 的原始资讯。
    请提炼出 **20 条** 最有价值的情报，并撰写一份《AI 全球实战内参》。

    **❌ 绝对禁止：**
    1. **禁止堆砌专业术语：** 比如“端侧推理”、“垂直整合”、“护城河”，除非你马上用通俗语言解释它意味着什么。
    2. **禁止空洞结论：** 别说“未来可期”或“需要关注”，要告诉我“现在该干什么”。
    3. **禁止标题党：** 标题必须包含具体事实。

    **✅ 必须执行的标准：**
    1. **资讯部分**：标题 = 【谁 + 做了什么 + 结果/影响】。链接另起一行 `🔗 [媒体名](url)`。
    2. **深度战略研判（核心中的核心）**：
       - 请用**“大白话”**把事情讲清楚。
       - 必须解释**“为什么”**（底层逻辑）和**“怎么做”**（具体行动）。
       - 必须覆盖以下四个维度：

       **维度一：⚡ 到底发生了什么？ (世界观)**
       不要只罗列新闻，要把新闻串起来。告诉读者：今天巨头们打架的本质是什么？谁慌了？谁赢了？市场规则变了没？

       **维度二：💰 钱流向了哪里？ (风口)**
       资金正在往哪个具体的细分领域涌入？不是“AI应用”，而是“AI视频生成”还是“医疗数据清洗”？

       **维度三：👉 普通人/创业者怎么干？ (实操)**
       * **对普通打工人**：别说“提升自我”，要说“去学 XX 工具，因为 XX 岗位正在高薪招人”。
       * **对小创业者**：别说“布局AI”，要说“去干 XX 细分业务，因为大厂看不上但很赚钱”。

       **维度四：🛑 最终建议 (一句话)**
       给读者的最后忠告，犀利、直接。

    **🔥 输出格式模板（请严格模仿）：**

    ### 🚀 AI 全球实战内参 ({beijing_date})
    > 🧠 智能驱动：DeepSeek V3 | 🌍 覆盖信源：Tavily (国际) + Bocha (国内)
    
    #### ⭐ 顶级重磅 (Top 3)
    1. **[巨头互殴] 亚马逊停止采购英伟达芯片，转用自研芯片，英伟达股价应声下跌 5%**
       🔗 [CNBC](https://...)
    ...
    
    #### 📰 行业必读 (Top 4-20)
    ...
    
    ---
    #### 🔭 深度战略研判 (通俗版)
    
    **1. ⚡ 到底发生了什么？**
    简单来说，以前大家都给英伟达交“过路费”，现在亚马逊和谷歌觉得太贵，决定自己造路了。这意味着英伟达一家独大的日子结束了，AI 芯片的价格会被打下来，我们以后用 AI 服务的成本会变低。

    **2. 💰 钱流向了哪里？**
    热钱正在从“造大模型”转向“电力和数据”。
    * **电力：** AI 极其耗电，谁能搞定便宜的电（比如核电、偏远水电），谁就是大爷。
    * **数据：** 网上能爬的免费数据都被爬光了，现在这种“经过律师确认、医生标注”的高质量私有数据，价格翻了3倍。

    **3. 👉 我们该怎么干？**
    * **普通打工人：** 建议去看看 **ComfyUI**（一种画图工具）或者 **Cursor**（AI写代码工具）。现在很多公司招人要求“会用 AI 提效”，而不只是“会干活”。学会这个，你就有溢价。
    * **小创业者/副业党：** 别去卷大模型，没戏。去看看**“数据标注”**的包工头生意，或者给传统小公司（比如律所、诊所）做**“私有知识库搭建”**。他们不敢把数据传给 ChatGPT，这恰恰是 DeepSeek 本地部署的机会。

    **4. 🛑 最终建议：**
    不要焦虑 AI 会取代你，先去把那个能帮你干活的 AI 工具装进电脑里。
    
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
    print("🚀 启动 Pro Max (人话版) 情报系统...")
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
