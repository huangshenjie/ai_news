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
    搜索策略优化：
    1. 增加 max_results 到 25 条，确保过滤后能剩下 20 条。
    2. 关键词中加入国内主流科技媒体，强制倾向于抓取国内可访问的链接。
    """
    print("1. 正在全网搜索 (优先国内信源)...")
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    
    # 组合查询：既包含全球热点，又限制中文来源权重
    # 技巧：在 Query 里直接带上媒体名字，能大幅提高国内链接的命中率
    query = "全球 AI 人工智能 行业动态 最新资讯 (OpenAI OR DeepSeek OR 字节跳动 OR 阿里) site:36kr.com OR site:jiqizhixin.com OR site:ithome.com OR site:qq.com OR site:mp.weixin.qq.com"
    
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
    print("2. 正在调用 DeepSeek V3 (长文本模式)...")
    
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
        "temperature": 0.6, # 稍微降低温度，让新闻更准确，不胡编
        "max_tokens": 4000  # 增加输出长度，防止 20 条新闻被截断
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

    # 构建 Prompt：这是 Agent 的大脑，决定了内容的质量
    prompt = f"""
    你是一名追求极致信息效率的 AI 首席情报官。请处理以下原始搜索数据：
    {json.dumps(news_data, ensure_ascii=False)}

    🔥 **核心任务**：
    1. **数量要求**：必须输出 **15-20 条** 最具价值的新闻。如果原始数据不够，则有多少列多少，不要编造。
    2. **标题改造（关键）**：
       - ❌ 拒绝短标题（如“OpenAI 发布新模型”）。
       - ✅ **必须使用长句标题**，包含“谁+做了什么+核心影响/参数”。
       - 标题长度应在 20-40 字之间，让用户**不用点开链接**就能获得 80% 的信息量。
    3. **链接清洗（关键）**：
       - 仔细检查原始数据中的 URL。
       - **优先保留国内可访问的链接**（如 36kr, 机器之心, 腾讯科技, IT之家, 公众号）。
       - 如果只有国外链接（Medium/Twitter），保留它但在标题后标注 (需翻墙)。

    📝 **输出格式（Markdown）**：
    ### 🚀 AI 全球情报内参 ({datetime.now().strftime('%Y-%m-%d')})
    > 🎯 重点关注：DeepSeek | OpenAI | 国产大模型
    
    1. **[标签] 这是一个非常详细的长标题，直接解释了新闻的核心内容和影响**
       🔗 [国内直连](url)
    
    2. **[标签] 字节跳动发布即梦 AI 视频模型，支持 60 秒超长生成，对标 Sora**
       🔗 [IT之家](url)
    
    (请依次列出 15-20 条...)
    
    ---
    **💡 趋势洞察**：(一句话总结今日最值得关注的一个信号)
    """
    return call_deepseek(prompt)

def push_wechat(content):
    if not content: return
    print("3. 正在推送...")
    
    # 企业微信 Markdown 消息长度有限制（约 4096 字节）
    # 如果 20 条新闻太长，可能导致发送失败。这里做一个简单的切分保护。
    if len(content.encode('utf-8')) > 4000:
        content = content[:1500] + "\n\n...(内容过长，仅显示前半部分)..."
    
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
