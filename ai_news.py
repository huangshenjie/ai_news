import requests
import json
from tavily import TavilyClient
from datetime import datetime

# =========================================================
# 🔴 核心配置区 (请填入你的 Key)
# =========================================================
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0"
TAVILY_API_KEY = "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"  # 在这里粘贴 Tavily Key
DEEPSEEK_API_KEY = "sk-gvvsglcyhujlvprlryxtwduxvbgwfyzqngzqesyvwvucjnyw" # 在此粘贴刚刚复制的 DeepSeek Key
# =========================================================

def get_realtime_news():
    """
    搜索策略：
    混合国内主流科技媒体(36kr, 机器之心等) + 全球热点(OpenAI, DeepSeek)
    """
    print("1. 正在全网搜索 (优先国内信源)...")
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    
    # 强制搜索国内源 + 全球热点
    query = "全球 AI 人工智能 行业动态 最新资讯 (OpenAI OR DeepSeek OR 字节跳动 OR 阿里 OR 腾讯) site:36kr.com OR site:jiqizhixin.com OR site:ithome.com OR site:qq.com OR site:mp.weixin.qq.com"
    
    try:
        response = tavily.search(
            query=query, 
            search_depth="advanced", 
            max_results=25, # 抓取更多以备筛选
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
        "temperature": 0.7, # 稍微提高一点温度，让分析更有灵感
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

    # Prompt 升级：增加战略研判模块
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

def push_wechat(content):
    if not content: return
    print("3. 正在推送...")
    
    # 企业微信 Markdown 消息长度限制保护
    # DeepSeek 的分析可能会比较长，如果超过限制，优先保留前面的新闻和最后的分析
    if len(content.encode('utf-8')) > 4000:
        # 简单截断策略：保留前 3000 字符，加上提示
        content = content[:3000] + "\n\n...(内容过长，请点击链接查看更多)... \n*(AI总结，仅供参考)*"
    
    headers = {"Content-Type": "application/json"}
    data = {"msgtype": "markdown", "markdown": {"content": content}}
    requests.post(WEBHOOK_URL, headers=headers, data=json.dumps(data))
    print("推送完成")

if __name__ == "__main__":
    raw = get_realtime_news()
    if raw:
        text = ai_process_content(raw)
        push_wechat(text)
    else:
        print("无数据")
