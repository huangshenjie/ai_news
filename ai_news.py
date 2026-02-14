import requests
import json
import feedparser # 新增依赖
from tavily import TavilyClient
from datetime import datetime, timedelta, timezone

# =========================================================
# 🔴 核心配置区 (当前模式：硬编码调试模式)
# ⚠️ 警告：测试通过后，请务必改回 os.environ.get 以保护密钥安全
# =========================================================
TAVILY_API_KEY = "在此粘贴Tavily_Key"
DEEPSEEK_API_KEY = "sk-gvvsglcyhujlvprlryxtwduxvbgwfyzqngzqesyvwvucjnyw" 
WECOM_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0"
FEISHU_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/54e2a16a-8409-46c7-bd62-a169bc3e063f"
# =========================================================

def get_beijing_time():
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=8)

# ---------------------------------------------------------
# 🛡️ 数据源 A: Tavily 全网搜索
# ---------------------------------------------------------
def get_tavily_data():
    print("1. 正在全网搜索 (Tavily)...")
    if "在此粘贴" in TAVILY_API_KEY:
        print("⚠️ Tavily Key 未配置，跳过")
        return []
        
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    query = "全球 AI 人工智能 行业动态 最新资讯 (OpenAI OR DeepSeek OR 字节跳动 OR 阿里 OR 腾讯) site:36kr.com OR site:jiqizhixin.com OR site:ithome.com OR site:qq.com OR site:mp.weixin.qq.com"
    try:
        response = tavily.search(query=query, search_depth="advanced", max_results=20, days=1)
        results = response.get('results', [])
        print(f"✅ Tavily 获取成功: {len(results)} 条")
        return results
    except Exception as e:
        print(f"❌ Tavily 搜索失败: {e}")
        return []

# ---------------------------------------------------------
# 🛡️ 数据源 B: 免费 RSS 兜底 (36Kr)
# ---------------------------------------------------------
def get_rss_data():
    print("🔄 Tavily 失败或数据为空，正在启动免费 RSS 兜底 (36Kr)...")
    rss_url = "https://36kr.com/feed" 
    try:
        feed = feedparser.parse(rss_url)
        results = []
        # 只取前 10 条，并统一格式
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
# ⚙️ 双保险混合逻辑
# ---------------------------------------------------------
def get_realtime_news():
    # 1. 优先尝试 Tavily
    data = get_tavily_data()
    
    # 2. 如果 Tavily 没数据，或者报错导致列表为空，则启动 RSS
    if not data:
        data = get_rss_data()
        
    return data

# ---------------------------------------------------------
# 🧠 DeepSeek 处理逻辑 (保持不变)
# ---------------------------------------------------------
def call_deepseek(prompt):
    print("2. 正在调用 DeepSeek V3...")
    if "在此粘贴" in DEEPSEEK_API_KEY:
        print("❌ DeepSeek Key 未配置，无法生成内容")
        return None

    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False, "temperature": 0.7, "max_tokens": 4000
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
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
    
    # 将数据转为 JSON 字符串
    data_str = json.dumps(news_data, ensure_ascii=False)[:3000] # 截断防止超长

    prompt = f"""
    你是一名具有商业洞察力的 AI 战略顾问。请根据以下原始搜索数据，为我撰写一份【高价值】的行业内参。
    数据：{data_str}

    🔥 **第一部分：资讯追踪 (10-15条)**
    1. **筛选标准**：保留最有技术含量或商业影响力的 10-15 条新闻。
    2. **标题格式**：
       - ✅ **标签必须精准细分**：如 **[融资动态]**、**[技术突破]**、**[高层变动]**、**[政策风向]**。
       - ✅ 必须使用长句标题（主谓宾+核心影响）。
    3. **链接要求**：保留原始链接。
    
    🔥 **第二部分：深度战略研判**
    1. **行业变局**：一句话总结今天的市场最大变化。
    2. **崛起风口**：指出一个潜在的赚钱机会。
    3. **落地机会**：给普通创业者的一个建议。

    📝 **输出格式范例**：
    ### 🚀 AI 全球情报内参 ({beijing_date})
    > 🧠 智能驱动：DeepSeek V3 | 🌍 信源：全网聚合
    
    #### 📰 核心动态
    1. **[融资动态] 谷歌计划发行百年期债券筹资 200 亿美元，用于 AI 算力基建狂飙**
       🔗 [来源](url)
    ...
    
    ---
    #### 🔭 深度战略研判
    ...
    
    *(AI总结，仅供参考)*
    """
    return call_deepseek(prompt)

# ---------------------------------------------------------
# 📢 推送逻辑 (保持不变)
# ---------------------------------------------------------
def push_wechat(content):
    if not content or "在此粘贴" in WECOM_WEBHOOK_URL: return
    print("3.1 推送至企微...")
    headers = {"Content-Type": "application/json"}
    data = {"msgtype": "markdown", "markdown": {"content": content}}
    try: requests.post(WECOM_WEBHOOK_URL, headers=headers, data=json.dumps(data))
    except: pass

def push_feishu(content):
    if not content or "在此粘贴" in FEISHU_WEBHOOK_URL: return
    print("3.2 推送至飞书...")
    current_time = get_beijing_time().strftime('%Y-%m-%d %H:%M')
    headers = {"Content-Type": "application/json"}
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {"content": "🚀 AI 全球情报内参", "tag": "plain_text"}
            },
            "elements": [
                {"tag": "markdown", "content": content},
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": f"更新时间: {current_time} (北京时间)"}]
                }
            ]
        }
    }
    try: requests.post(FEISHU_WEBHOOK_URL, headers=headers, data=json.dumps(payload))
    except: pass

if __name__ == "__main__":
    print("🚀 启动 AI 情报系统 (双保险模式)...")
    
    # 1. 获取数据 (Tavily -> 失败 -> RSS)
    raw_data = get_realtime_news()
    
    if raw_data:
        # 2. 只有拿到数据才调用 DeepSeek
        final_text = ai_process_content(raw_data)
        
        if final_text:
            push_wechat(final_text)
            push_feishu(final_text)
            print("✅ 执行结束")
        else:
            print("⚠️ DeepSeek 生成为空，不推送")
    else:
        print("❌ 两个数据源都挂了，今日无情报")
