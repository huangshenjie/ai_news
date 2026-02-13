import requests
import json
from tavily import TavilyClient
from google import genai
from datetime import datetime

# =========================================================
# 🔴 核心配置区 (请保留你的 Key，不要动引号)
# =========================================================
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0"
TAVILY_API_KEY = "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"  # 在这里粘贴 Tavily Key
GEMINI_API_KEY = "AIzaSyBnUO6BQs5jRJ86WpZOV7UmNxB0t8Zxr0g"   # 在这里粘贴你刚才复制的 Gemini Key
# =========================================================

def get_realtime_news():
    print("1. 正在全网搜索 AI 资讯...")
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    try:
        # 搜索过去24小时的精准信息
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

def ai_process_content(news_data):
    if not news_data: return None
    print("2. 正在调用 Gemini (新版 SDK) 进行重写...")

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    作为 AI 情报专家，请将以下搜索结果整理为中文日报：
    {json.dumps(news_data)}
    
    要求：
    1. 必须使用中文。
    2. 筛选 10 条最有价值的新闻。
    3. 格式：Markdown 列表，包含 [来源]、标题、链接。
    
    输出模板：
    ### 🤖 AI 全球情报 ({datetime.now().strftime('%Y-%m-%d')})
    > 🧠 智能重写：Gemini 2.0 Flash
    
    1. **[标题]** ...
       🔗 [链接](url)
    """
    
    try:
        # 👇【核心修复】切换到 Gemini 2.0 Flash，这是目前公测最稳定快速的版本
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt
        )
        return response.text
    except Exception as e:
        # 如果 2.0 也不行，打印出错误方便调试，并尝试 fallback
        print(f"Gemini 2.0 生成失败: {e}")
        try:
            print("尝试回退到 gemini-1.5-pro...")
            response = client.models.generate_content(
                model="gemini-1.5-pro",
                contents=prompt
            )
            return response.text
        except Exception as e2:
            print(f"所有模型尝试均失败: {e2}")
            return None

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
