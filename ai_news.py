import requests
import json
from tavily import TavilyClient
from datetime import datetime

# =========================================================
# 🔴 核心配置区
# =========================================================
TAVILY_API_KEY = "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"  # 在这里粘贴 Tavily Key
DEEPSEEK_API_KEY = "sk-gvvsglcyhujlvprlryxtwduxvbgwfyzqngzqesyvwvucjnyw" # 在此粘贴刚刚复制的 DeepSeek Key

# WxPusher 配置
WXPUSHER_APP_TOKEN = "AT_KXoDPf0Fy4VwQ8qxUIhn2njLwpW9dMiz"
WXPUSHER_UIDS = ["UID_2ZZlmxgdNTPBIDQ7mo9SMdEZpMOK"] # 务必填入你的 UID
# =========================================================

def get_realtime_news():
    print("1. 正在全网搜索...")
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    query = "全球 AI 人工智能 行业动态 最新资讯 (OpenAI OR DeepSeek OR 字节跳动) site:36kr.com OR site:jiqizhixin.com OR site:ithome.com"
    try:
        response = tavily.search(query=query, search_depth="advanced", max_results=25, days=1)
        return response.get('results', [])
    except Exception as e:
        print(f"搜索失败: {e}")
        return []

def call_deepseek(prompt):
    print("2. 正在调用 DeepSeek V3...")
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False, 
        "temperature": 0.7,
        "max_tokens": 4000
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    except Exception as e:
        print(f"AI 请求失败: {e}")
        return None

def ai_process_content(news_data):
    if not news_data: return None
    prompt = f"""
    你是一名 AI 战略顾问。请根据以下数据撰写一份【AI 行业内参】。
    数据：{json.dumps(news_data, ensure_ascii=False)}
    
    要求：
    1. 筛选 15-20 条高价值新闻。
    2. 使用长句标题（主谓宾+影响）。
    3. 优先国内链接。
    
    格式：
    ### 🚀 AI 全球情报内参 ({datetime.now().strftime('%Y-%m-%d')})
    > 🧠 智能驱动：DeepSeek V3
    
    #### 📰 核心动态
    1. **[标签] 标题...**
       🔗 [链接](url)
    
    ---
    #### 🔭 深度战略研判
    * **⚡ 变局**：...
    * **📈 风口**：...
    * **💰 机会**：...
    
    *(AI总结，仅供参考)*
    """
    return call_deepseek(prompt)

def push_wxpusher(content):
    if not content: return
    print("3. 正在推送至 WxPusher...")
    
    url = "https://wxpusher.zjiecode.com/api/send/message"
    payload = {
        "appToken": WXPUSHER_APP_TOKEN,
        "content": content,
        "summary": f"AI 日报更新: {datetime.now().strftime('%m-%d')}",
        "contentType": 3, 
        "uids": WXPUSHER_UIDS,
        "verifyPay": False
    }
    try:
        res = requests.post(url, json=payload).json()
        if res['code'] == 1000:
            print("✅ WxPusher 推送成功！")
        else:
            print(f"❌ WxPusher 推送失败: {res['msg']}")
    except Exception as e:
        print(f"网络异常: {e}")

if __name__ == "__main__":
    raw = get_realtime_news()
    if raw:
        text = ai_process_content(raw)
        push_wxpusher(text) # 只保留这一个推送
    else:
        print("无数据")
