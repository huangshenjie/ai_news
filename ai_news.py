import requests
import json
import feedparser
from tavily import TavilyClient
import google.generativeai as genai
from datetime import datetime

# =========================================================
# 🔴 核心配置区 (请立即填入你的 Key，保留双引号)
# =========================================================
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0"
TAVILY_API_KEY = "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"  # 在这里粘贴 Tavily Key
GEMINI_API_KEY = "AIzaSyBnUO6BQs5jRJ86WpZOV7UmNxB0t8Zxr0g"   # 在这里粘贴你刚才复制的 Gemini Key
# =========================================================

def get_realtime_news():
    """1. 使用 Tavily 进行全网深度搜索 (搜索 + 过滤)"""
    print("正在全网检索 AI 实时情报...")
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    
    # 组合查询：覆盖 OpenAI、国内大厂、融资消息
    query = "OpenAI latest updates 24h, DeepSeek or Yi-Large model news, Bytedance AI video model, China AI startup funding"
    
    try:
        response = tavily.search(
            query=query, 
            search_depth="advanced", 
            max_results=15, # 获取15条最相关的
            days=1
        )
        return response.get('results', [])
    except Exception as e:
        print(f"Tavily 搜索失败: {e}")
        return []

def ai_process_content(news_data):
    """2. 使用 Gemini 大脑：阅读、理解、翻译、重写"""
    if not news_data:
        return None

    print("正在调用 Gemini 进行智能清洗与重写...")
    genai.configure(api_key=GEMINI_API_KEY)
    # 使用 Flash 模型，速度快且免费额度高
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    你是一名残酷诚实的顶级 AI 行业情报官。请根据以下原始英文搜素结果，为我撰写一份中文日报。
    
    原始数据：
    {json.dumps(news_data)}
    
    撰写要求：
    1. **只保留真新闻**：剔除营销号内容、重复内容，只保留真正有技术或商业价值的 10-15 条。
    2. **完全中文输出**：将所有英文标题和摘要翻译并重写为流畅、专业的中文。
    3. **格式清晰**：使用 Markdown 列表，每条新闻必须包含【分类标签】、一句话核心事实、以及[原文链接]。
    4. **国内视角**：特别关注涉及中国模型（如 DeepSeek, 智谱, 字节即梦等）的动态。
    
    输出模板：
    ### 🤖 全球 AI 核心情报 ({datetime.now().strftime('%Y-%m-%d')})
    > 🧠 智能重写：Gemini 1.5 | 🌍 实时信源：Tavily
    
    #### 🔥 头条重磅
    1. **[OpenAI]** ... (附链接)
    2. **[国内模型]** ... (附链接)
    
    #### 💰 投融资与行业
    3. ...
    
    ---
    **💡 顾问辣评**：(用一句话犀利点评今日最重要的趋势)
    """
    
    try:
        response = model.generate_content(prompt)
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
    # 执行流水线
    raw_data = get_realtime_news()
    if raw_data:
        final_report = ai_process_content(raw_data)
        push_wechat(final_report)
    else:
        print("今日无重大更新或搜索接口异常。")
