import requests
import json
import time
from tavily import TavilyClient
from datetime import datetime

# =========================================================
# 🔴 务必填入你刚刚新建项目生成的 Key
# =========================================================
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0"
TAVILY_API_KEY = "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"  # 在这里粘贴 Tavily Key
GEMINI_API_KEY = "AIzaSyAzPYpVuOZYStxlxTdvSAewCTaSpIiRffs"   # 在这里粘贴你刚才复制的 Gemini Key
# =========================================================

def get_realtime_news():
    print("1. 正在全网搜索 AI 资讯...")
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

def call_gemini_simple(prompt):
    """
    使用最基础的 HTTP 请求调用 gemini-1.5-flash。
    新项目的 Key 一定支持这个模型。
    """
    print("2. 正在调用 Gemini API...")
    
    # 强制指定版本号，避免歧义
    model_name = "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            print(f"❌ 调用失败 (Code {response.status_code}): {response.text}")
            return None
            
    except Exception as e:
        print(f"网络异常: {e}")
        return None

def ai_process_content(news_data):
    if not news_data: return None

    prompt = f"""
    你是一名 AI 情报专家。请根据以下搜索结果整理为中文日报：
    {json.dumps(news_data)}
    
    要求：
    1. 必须中文。
    2. 筛选 8 条核心资讯。
    3. 格式：Markdown 列表，包含 [来源]、标题、链接。
    
    输出模板：
    ### 🤖 AI 全球情报 ({datetime.now().strftime('%Y-%m-%d')})
    
    1. **[标题]** ...
       🔗 [链接](url)
    """
    return call_gemini_simple(prompt)

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
