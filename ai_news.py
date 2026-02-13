import requests
import json
import time
from tavily import TavilyClient
from datetime import datetime

# =========================================================
# 🔴 核心配置区
# =========================================================
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0"
TAVILY_API_KEY = "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"  # 在这里粘贴 Tavily Key
GEMINI_API_KEY = "AIzaSyDs1nN5RV0CTLzf9xj52FJdvP5FlQD8cF8" 
# =========================================================

def get_realtime_news():
    """
    搜索策略：混合国内主流科技媒体，确保链接可访问性
    """
    print("1. 正在全网搜索 (优先国内信源)...")
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    
    # 强制搜索国内源 + 全球热点
    query = "全球 AI 人工智能 行业动态 (OpenAI OR DeepSeek OR 字节跳动) site:36kr.com OR site:jiqizhixin.com OR site:ithome.com OR site:qq.com OR site:mp.weixin.qq.com"
    
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

def call_gemini_pro(prompt):
    """
    使用 Google Gemini 1.5 Flash (免费、快速、稳定)
    采用纯 HTTP 请求，无需安装 SDK，避免版本冲突。
    """
    print("2. 正在调用 Google Gemini (免费版)...")
    
    # 使用 1.5 Flash 模型
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 4000 
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        elif response.status_code == 429:
            print("❌ Google 额度暂时耗尽 (请稍后再试)")
            return None
        else:
            print(f"❌ Gemini 调用失败: {response.text}")
            return None
            
    except Exception as e:
        print(f"网络异常: {e}")
        return None

def ai_process_content(news_data):
    if not news_data: return None

    # Prompt 逻辑与 DeepSeek 版保持一致：长标题 + 20条 + 国内源
    prompt = f"""
    你是一名追求极致效率的 AI 首席情报官。请处理以下搜索数据：
    {json.dumps(news_data, ensure_ascii=False)}

    🔥 **任务要求**：
    1. **数量**：输出 **15-20 条** 核心情报。
    2. **标题**：必须使用**长句标题**（包含主谓宾+核心影响），禁止短标题。
       - 🚫 错误：DeepSeek 发布新模型
       - ✅ 正确：DeepSeek 发布 V3 版本，推理成本降低 90%，性能全面对标 GPT-4o
    3. **链接**：**只保留国内可直接访问的链接**（36kr/机器之心/IT之家等）。如果是国外链接，请在标题后标注 (需翻墙)。

    📝 **输出格式**：
    ### 🚀 AI 全球情报内参 ({datetime.now().strftime('%Y-%m-%d')})
    > 🧠 智能驱动：Gemini 1.5 Flash | 🌍 信源：Tavily
    
    1. **[标签] 长标题长标题长标题...**
       🔗 [来源媒体](url)
    
    (请列出 15-20 条...)
    
    ---
    **💡 趋势洞察**：(一句话总结)
    """
    return call_gemini_pro(prompt)

def push_wechat(content):
    if not content: return
    print("3. 正在推送...")
    
    if len(content.encode('utf-8')) > 4000:
        content = content[:1500] + "\n\n...(内容过长，截断显示)..."
    
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
