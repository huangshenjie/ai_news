import requests
import json
from tavily import TavilyClient
from datetime import datetime

# =========================================================
# 🔴 核心配置区 (请填入你的 Key)
# =========================================================
# 1. API Keys
TAVILY_API_KEY = "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"  # 在这里粘贴 Tavily Key
DEEPSEEK_API_KEY = "sk-gvvsglcyhujlvprlryxtwduxvbgwfyzqngzqesyvwvucjnyw" # 在此粘贴刚刚复制的 DeepSeek Key

# 2. 推送通道配置
# 企业微信 Webhook (如果不需要请留空)
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0"

# 飞书 Webhook (🔥 新增)
# 注意：在飞书机器人安全设置里，必须添加关键词 "AI"
FEISHU_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/323bfb85-211d-4710-824b-beb962b460a1"
# =========================================================

def get_realtime_news():
    print("1. 正在全网搜索 (优先国内信源)...")
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    
    # 强制搜索国内源 + 全球热点
    query = "全球 AI 人工智能 行业动态 最新资讯 (OpenAI OR DeepSeek OR 字节跳动 OR 阿里 OR 腾讯) site:36kr.com OR site:jiqizhixin.com OR site:ithome.com OR site:qq.com OR site:mp.weixin.qq.com"
    
    try:
        response = tavily.search(
            query=query, 
            search_depth="advanced", 
            max_results=25,
            days=1
        )
        return response.get('results', [])
    except Exception as e:
        print(f"搜索失败: {e}")
        return []

def call_deepseek(prompt):
    print("2. 正在调用 DeepSeek V3 (深度思考模式)...")
    
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "temperature": 0.7, 
        "max_tokens": 4000
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"❌ DeepSeek 调用失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"网络请求异常: {e}")
        return None

def ai_process_content(news_data):
    if not news_data: return None

    prompt = f"""
    你是一名具有商业洞察力的 AI 战略顾问。请根据以下原始搜索数据，为我撰写一份【高价值】的行业内参。
    
    原始数据：
    {json.dumps(news_data, ensure_ascii=False)}

    🔥 **第一部分：资讯追踪 (15-20条)**
    1. **筛选标准**：保留最有技术含量或商业影响力的 15-20 条新闻。
    2. **标题要求**：必须使用**长句标题**（包含主谓宾+核心影响），禁止短标题。让用户不用点链接就能看懂 80%。
    3. **链接要求**：**必须优先展示国内直连链接**（36kr/机器之心/IT之家/公众号等）。
    
    🔥 **第二部分：深度战略研判 (核心价值)**
    请基于今日资讯，进行深度的趋势分析，回答以下三个问题（每个问题 1-2 句话）：
    1. **行业变局**：哪个巨头正在被挑战？哪个旧规则正在失效？
    2. **崛起风口**：钱和注意力正在流向哪个细分赛道？
    3. **落地机会**：当下的技术进步，最适合赋能到哪个具体场景（普通人/开发者的机会在哪里）？

    📝 **输出格式（Markdown）**：
    ### 🚀 AI 全球情报内参 ({datetime.now().strftime('%Y-%m-%d')})
    > 🧠 智能驱动：DeepSeek V3 | 🌍 信源：Tavily
    
    #### 📰 核心动态
    1. **[标签] 这是一个非常详细的长标题，解释了新闻的核心内容和影响**
       🔗 [国内直连](url)
    2. **[标签] DeepSeek 发布 V3 版本，推理成本降低 90%，性能全面对标 GPT-4o**
       🔗 [机器之心](url)
    ... (列出 15-20 条)
    
    ---
    #### 🔭 深度战略研判
    * **⚡ 行业变局**：(例如：开源模型正在倒逼闭源厂商降价，模型护城河正在从参数量转向应用生态...)
    * **📈 崛起风口**：(例如：AI 视频生成正在爆发，短剧和广告行业将迎来洗牌...)
    * **💰 落地机会**：(例如：利用长上下文窗口进行法律/医疗文档的自动化处理是当前蓝海...)
    
    *(AI总结，仅供参考)*
    """
    return call_deepseek(prompt)

# === 通道 1: 企业微信 ===
def push_wechat(content):
    if not content or not WECOM_WEBHOOK_URL: 
        print("企业微信 Webhook 为空，跳过推送。")
        return
    print("3.1 正在推送至企业微信...")
    
    # 截断保护
    if len(content.encode('utf-8')) > 4000:
        content = content[:3000] + "\n\n...(内容过长，请点击链接查看更多)... \n*(AI总结，仅供参考)*"
    
    headers = {"Content-Type": "application/json"}
    data = {"msgtype": "markdown", "markdown": {"content": content}}
    
    try:
        requests.post(WECOM_WEBHOOK_URL, headers=headers, data=json.dumps(data))
        print("✅ 企微推送完成")
    except Exception as e:
        print(f"❌ 企微推送失败: {e}")

# === 通道 2: 飞书 (Lark) ===
def push_feishu(content):
    if not content or not FEISHU_WEBHOOK_URL: 
        print("飞书 Webhook 为空，跳过推送。")
        return
    print("3.2 正在推送至飞书...")

    # 飞书使用的是“富文本卡片消息”，体验比纯 Markdown 更好
    # 我们把 DeepSeek 的 Markdown 内容封装进卡片里
    
    # 截断保护 (飞书限制稍宽，但也做一下保护)
    if len(content.encode('utf-8')) > 30000: # 飞书限制很大，这里主要是为了防止极端的超长文本
         content = content[:10000] + "\n...(内容过长截断)..."

    headers = {"Content-Type": "application/json"}
    
    # 构造飞书卡片 JSON 结构
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": "blue", # 标题颜色：蓝色
                "title": {
                    "content": "🚀 AI 全球情报内参",
                    "tag": "plain_text"
                }
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": content # 直接把 DeepSeek 生成的 Markdown 塞进去，飞书支持渲染
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        }
                    ]
                }
            ]
        }
    }

    try:
        res = requests.post(FEISHU_WEBHOOK_URL, headers=headers, data=json.dumps(payload))
        result = res.json()
        if result.get("code") == 0:
            print("✅ 飞书推送完成")
        else:
            print(f"❌ 飞书推送失败: {result}")
    except Exception as e:
        print(f"❌ 飞书网络异常: {e}")

if __name__ == "__main__":
    raw = get_realtime_news()
    if raw:
        text = ai_process_content(raw)
        # 并行推送
        push_wechat(text)
        push_feishu(text)
    else:
        print("无数据")
