import requests
import json
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
        # 搜索最近 24 小时的 AI 动态
        response = tavily.search(
            query="OpenAI latest news, DeepSeek updates, Bytedance AI video model, China AI startup funding", 
            search_depth="advanced", 
            max_results=12,
            days=1
        )
        return response.get('results', [])
    except Exception as e:
        print(f"搜索失败: {e}")
        return []

def call_gemini_api(prompt):
    """
    使用纯 HTTP 请求调用 Gemini API，绕过 SDK 版本问题。
    使用 gemini-1.5-flash 模型，速度快且免费额度高。
    """
    print("2. 正在调用 Gemini API (HTTP) ...")
    
    # API 端点
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    # 请求体
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, headers={'Content-Type': 'application/json'}, json=payload)
        
        # 检查是否成功
        if response.status_code == 200:
            result = response.json()
            # 提取生成的文本
            return result['candidates'][0]['content']['parts'][0]['text']
        elif response.status_code == 429:
            print("❌ 错误：请求过于频繁 (Quota Exceeded)，请稍后再试。")
            return None
        else:
            print(f"❌ Gemini API 调用失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"网络请求异常: {e}")
        return None

def ai_process_content(news_data):
    if not news_data: return None

    # 构造提示词
    prompt = f"""
    你是一名 AI 情报专家。请根据以下搜索结果整理为中文日报：
    {json.dumps(news_data)}
    
    要求：
    1. 必须使用中文输出。
    2. 筛选 10 条最有价值的新闻（去重）。
    3. 格式：Markdown 列表，包含 [来源]、标题、链接。
    4. 标题要清晰简练，概括核心事实。
    
    输出模板：
    ### 🤖 AI 全球情报 ({datetime.now().strftime('%Y-%m-%d')})
    
    1. **[标签] 标题**
       🔗 [链接](url)
    """
    
    return call_gemini_api(prompt)

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
