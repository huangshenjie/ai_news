import requests
import json
import time
from tavily import TavilyClient
from datetime import datetime

# =========================================================
# 🔴 核心配置区 (务必填入 Key)
# =========================================================
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0"
TAVILY_API_KEY = "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"  # 在这里粘贴 Tavily Key
GEMINI_API_KEY = "AIzaSyBnUO6BQs5jRJ86WpZOV7UmNxB0t8Zxr0g"   # 在这里粘贴你刚才复制的 Gemini Key
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

def call_gemini_with_fallback(prompt):
    """
    智能轮询：依次尝试不同的模型名称，直到成功。
    解决了 404 (找不到模型) 和 429 (额度超限) 的问题。
    """
    # 备选模型列表（按优先级排序）
    # 1.5-flash-latest: 通常是最新的稳定版
    # 1.5-flash-001: 具体的版本号，最保险
    # 1.5-pro: 备用
    # gemini-pro: 老版本，作为最后的底线
    models_to_try = [
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-001",
        "gemini-1.5-flash",
        "gemini-1.5-pro-latest",
        "gemini-pro"
    ]
    
    print("2. 正在调用 Gemini API (智能轮询模式)...")
    
    for model_name in models_to_try:
        print(f"   Trying model: {model_name} ...")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        try:
            response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
            
            if response.status_code == 200:
                print(f"   ✅ 成功连接模型: {model_name}")
                result = response.json()
                return result['candidates'][0]['content']['parts'][0]['text']
            
            elif response.status_code == 404:
                print(f"   ❌ 模型未找到 (404)，尝试下一个...")
                continue # 试下一个
            
            elif response.status_code == 429:
                print(f"   ⚠️ 模型额度耗尽 (429)，尝试下一个...")
                continue # 试下一个
                
            else:
                print(f"   ❌ 未知错误 {response.status_code}: {response.text}")
                continue
                
        except Exception as e:
            print(f"   网络异常: {e}")
            continue

    return None

def ai_process_content(news_data):
    if not news_data: return None

    prompt = f"""
    你是一名 AI 情报专家。请根据以下搜索结果整理为中文日报：
    {json.dumps(news_data)}
    
    要求：
    1. 必须中文。
    2. 筛选 8-10 条核心资讯。
    3. 格式：Markdown 列表，包含 [来源]、标题、链接。
    
    输出模板：
    ### 🤖 AI 全球情报 ({datetime.now().strftime('%Y-%m-%d')})
    
    1. **[标题]** ...
       🔗 [链接](url)
    """
    
    # 使用智能轮询函数
    return call_gemini_with_fallback(prompt)

def push_wechat(content):
    if not content: 
        print("内容为空，无法推送")
        return
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
