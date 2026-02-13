import requests
import json
from tavily import TavilyClient
from google import genai
from datetime import datetime

# =========================================================
# 🔴 核心配置区 (请重新填入你的 Key)
# =========================================================
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0"
TAVILY_API_KEY = "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"  # 在这里粘贴 Tavily Key
GEMINI_API_KEY = "AIzaSyBnUO6BQs5jRJ86WpZOV7UmNxB0t8Zxr0g"   # 在这里粘贴你刚才复制的 Gemini Key
# =========================================================

def get_realtime_news():
    """1. 使用 Tavily 进行全网深度搜索"""
    print("正在全网检索 AI 实时情报...")
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    
    query = "OpenAI latest updates 24h, DeepSeek news, Bytedance PixelDance video model, China AI startup funding"
    
    try:
        response = tavily.search(
            query=query, 
            search_depth="advanced", 
            max_results=15,
            days=1
        )
        return response.get('results', [])
    except Exception as e:
        print(f"Tavily 搜索失败: {e}")
        return []

def ai_process_content(news_data):
    """2. 使用最新的 Google GenAI SDK 进行处理"""
    if not news_data:
        return None

    print("正在调用 Gemini 进行智能清洗与重写...")
    
    # 【核心修改】使用新版 SDK 初始化
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    你是一名顶级 AI 情报分析师。基于以下搜索结果撰写中文日报：
    {json.dumps(news_data)}
    
    要求：
    1. 筛选 10-15 条最有价值的 AI 资讯（去重、去广告）。
    2. 将英文标题重写为专业的中文标题。
    3. 重点关注：OpenAI、DeepSeek、字节跳动等大厂动态。
    4. 格式：Markdown 列表，包含 [分类]、标题、链接。
    
    输出模板：
    ### 🤖 全球 AI 核心情报 ({datetime.now().strftime('%Y-%m-%d')})
    > 🧠 智能重写：Gemini 1.5 Flash
    
    1. **[标签] 中文标题**
       🔗 [原文链接](url)
    
    ---
    **💡 顾问点评**：(一句话总结)
    """
    
    try:
        # 【核心修改】新版调用方式
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Gemini 生成失败: {e}")
        return None

def push_wechat(content):
    """3. 推送到企业微信"""
    if not content:
        print("内容为空，跳过推送")
        return

    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "markdown",
        "markdown": {"content": content}
    }
    resp = requests.post(WEBHOOK_URL, headers=headers, data=json.dumps(data))
    print(f"推送结果: {resp.text}")

if __name__ == "__main__":
    raw_data = get_realtime_news()
    if raw_data:
        final_report = ai_process_content(raw_data)
        push_wechat(final_report)
    else:
        print("今日无重大更新或搜索接口异常。")
