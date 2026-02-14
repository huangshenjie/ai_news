import requests
import json
from tavily import TavilyClient
from datetime import datetime, timedelta, timezone

# =========================================================
# 🔴 核心配置区
# =========================================================
# 1. 搜索与 AI Key
TAVILY_API_KEY = "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"
DEEPSEEK_API_KEY = "sk-gvvsglcyhujlvprlryxtwduxvbgwfyzqngzqesyvwvucjnyw" 

# 2. 推送通道配置
# [通道A] 企业微信 Webhook (修复点：必须定义这个变量)
WECOM_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0"

# [通道B] 飞书 Webhook (记得在飞书后台设关键词 "AI")
FEISHU_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/54e2a16a-8409-46c7-bd62-a169bc3e063f"
# =========================================================

def get_beijing_time():
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=8)

def get_realtime_news():
    print("1. 正在全网搜索 (优先国内信源)...")
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    query = "全球 AI 人工智能 行业动态 最新资讯 (OpenAI OR DeepSeek OR 字节跳动 OR 阿里 OR 腾讯) site:36kr.com OR site:jiqizhixin.com OR site:ithome.com OR site:qq.com OR site:mp.weixin.qq.com"
    try:
        response = tavily.search(query=query, search_depth="advanced", max_results=25, days=1)
        return response.get('results', [])
    except Exception as e:
        print(f"搜索失败: {e}")
        return []

def call_deepseek(prompt):
    print("2. 正在调用 DeepSeek V3...")
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
        return None
    except Exception as e:
        print(f"网络请求异常: {e}")
        return None

def ai_process_content(news_data):
    if not news_data: return None
    
    beijing_date = get_beijing_time().strftime('%Y-%m-%d')

    # 🔥 核心修改：升级 Prompt，强制要求“细分标签”
    prompt = f"""
    你是一名具有商业洞察力的 AI 战略顾问。请根据以下原始搜索数据，为我撰写一份【高价值】的行业内参。
    数据：{json.dumps(news_data, ensure_ascii=False)}

    🔥 **第一部分：资讯追踪 (15-20条)**
    1. **筛选标准**：保留最有技术含量或商业影响力的 15-20 条新闻。
    2. **标题格式（关键修改）**：
       - ✅ **标签必须精准细分**：根据新闻内容定制标签。
         - *不要用*：[行业]、[技术]、[重磅] 这种太宽泛的词。
         - *要用*：**[融资动态]**、**[技术突破]**、**[高层变动]**、**[政策风向]**、**[新品发布]**、**[算力基建]**、**[开源生态]**。
       - ✅ 必须使用长句标题（主谓宾+核心影响）。
    3. **链接要求**：优先展示国内直连链接。
    
    🔥 **第二部分：深度战略研判**
    1. **行业变局**：...
    2. **崛起风口**：...
    3. **落地机会**：...

    📝 **输出格式范例（请严格模仿标签的颗粒度）**：
    ### 🚀 AI 全球情报内参 ({beijing_date})
    > 🧠 智能驱动：DeepSeek V3 | 🌍 信源：Tavily
    
    #### 📰 核心动态
    1. **[融资动态] 谷歌计划发行百年期债券筹资 200 亿美元，用于 AI 算力基建狂飙**
       🔗 [IT之家](url)
    2. **[技术突破] DeepSeek 推出 V3 架构，推理成本降低 90%，开源生态再下一城**
       🔗 [机器之心](url)
    3. **[高层变动] OpenAI 挖角 Anthropic 安全负责人，硅谷人才战进入白热化**
       🔗 [36氪](url)
    ... (列出 15-20 条)
    
    ---
    #### 🔭 深度战略研判
    ...
    
    *(AI总结，仅供参考)*
    """
    return call_deepseek(prompt)

def push_wechat(content):
    try:
        if not content or not WECOM_WEBHOOK_URL: return
    except NameError: return
    print("3.1 推送至企微...")
    if len(content.encode('utf-8')) > 4000:
        content = content[:3000] + "\n\n...(内容过长截断)... \n*(AI总结，仅供参考)*"
    headers = {"Content-Type": "application/json"}
    data = {"msgtype": "markdown", "markdown": {"content": content}}
    try: requests.post(WECOM_WEBHOOK_URL, headers=headers, data=json.dumps(data))
    except: pass

def push_feishu(content):
    try:
        if not content or not FEISHU_WEBHOOK_URL: return
    except NameError: return
    print("3.2 推送至飞书...")
    current_time = get_beijing_time().strftime('%Y-%m-%d %H:%M')
    if len(content.encode('utf-8')) > 30000:
         content = content[:10000] + "\n...(内容过长截断)..."
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
    try:
        requests.post(FEISHU_WEBHOOK_URL, headers=headers, data=json.dumps(payload))
        print("✅ 飞书推送完成")
    except Exception as e:
        print(f"❌ 飞书错误: {e}")

if __name__ == "__main__":
    raw = get_realtime_news()
    if raw:
        text = ai_process_content(raw)
        push_wechat(text)
        push_feishu(text)
    else:
        print("无数据")
