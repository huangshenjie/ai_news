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
    print("1. 正在全网搜索 AI 资讯 (Tavily)...")
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    try:
        response = tavily.search(
            query="OpenAI latest news, DeepSeek updates, Bytedance AI video model, China AI startup funding", 
            search_depth="advanced", 
            max_results=10,
            days=1
        )
        return response.get('results', [])
    except Exception as e:
        print(f"搜索失败: {e}")
        return []

def call_deepseek(prompt):
    """
    使用 DeepSeek V3 (硅基流动) 进行智能写作。
    无需代理，国内直连，速度快。
    """
    print("2. 正在调用 DeepSeek V3...")
    
    url = "https://api.siliconflow.cn/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-ai/DeepSeek-V3", # 使用满血版 V3
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"❌ DeepSeek 调用失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"网络请求异常: {e}")
        return None

def ai_process_content(news_data):
    if not news_data: return None

    prompt = f"""
    你是一名专业、犀利的 AI 行业情报官。请根据以下原始搜索数据，为我撰写一份【中文日报】。
    
    原始数据：
    {json.dumps(news_data, ensure_ascii=False)}
    
    撰写要求：
    1. **只说人话**：标题要简练、有力，拒绝营销号废话。
    2. **筛选精华**：只保留 8-10 条最有价值的新闻（去重）。
    3. **必须包含**：OpenAI 动态、国产大模型（DeepSeek/字节/阿里）进展。
    4. **格式规范**：Markdown 列表，格式为 `1. **[标签] 标题** 🔗 [链接](url)`。
    
    输出模板：
    ### 🚀 AI 每日内参 ({datetime.now().strftime('%Y-%m-%d')})
    > 🧠 智能驱动：DeepSeek V3 | 🌍 实时信源：Tavily
    
    1. **[重磅]** ...
       🔗 [原文](url)
    
    ...
    
    ---
    **💡 辣评**：(一句话总结今日趋势)
    """
    return call_deepseek(prompt)

def push_wechat(content):
    if not content: return
    print("3. 正在推送...")
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
