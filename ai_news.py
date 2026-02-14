import requests
import json
from tavily import TavilyClient
from datetime import datetime, timedelta, timezone

# =========================================================
# 🔴 核心配置区 (Key 保持不变，无需修改)
# =========================================================
# 1. 搜索与 AI Key
TAVILY_API_KEY = "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"
DEEPSEEK_API_KEY = "sk-gvvsglcyhujlvprlryxtwduxvbgwfyzqngzqesyvwvucjnyw" 

# 2. 推送通道配置
# [通道A] 企业微信 Webhook (修复点：必须定义这个变量)
WECOM_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0"

# [通道B] 飞书 Webhook (记得在飞书后台设关键词 "AI")
FEISHU_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/54e2a16a-8409-46c7-bd62-a169bc3e063f"
# =========================================================

# 🔥 新增：获取北京时间的辅助函数
def get_beijing_time():
    # UTC 时间 + 8 小时 = 北京时间
    utc_now = datetime.now(timezone.utc)
    beijing_time = utc_now + timedelta(hours=8)
    return beijing_time

def get_realtime_news():
    print("1. 正在全网搜索 (优先国内信源)...")
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    query = "全球 AI 人工智能 行业动态 最新资讯 (OpenAI OR DeepSeek OR 字节跳动 OR 阿里 OR 腾讯) site:36kr.com OR site:jiqizhixin.com OR site:ithome.com OR site:qq.com OR site:mp.weixin.qq.com"
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
        "stream": False, "temperature": 0.7, "max_tokens": 4000
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    except Exception as e:
        print(f"网络请求异常: {e}")
        return None

def ai_process_content(news_data):
    if not news_data: return None
    
    # 🔥 修改点 1：标题使用北京时间
    beijing_date = get_beijing_time().strftime('%Y-%m-%d')

    prompt = f"""
    你是一名具有商业洞察力的 AI 战略顾问。请根据以下原始搜索数据，为我撰写一份【高价值】的行业内参。
    数据：{json.dumps(news_data, ensure_ascii=False)}

    🔥 **第一部分：资讯追踪 (15-20条)**
    1. 筛选 15-20 条高价值新闻。
    2. 使用长句标题（主谓宾+核心影响）。
    3. **优先展示国内直连链接**。
    
    🔥 **第二部分：深度战略研判**
    1. **行业变局**：...
    2. **崛起风口**：...
    3. **落地机会**：...

    📝 **输出格式**：
    ### 🚀 AI 全球情报内参 ({beijing_date})
    > 🧠 智能驱动：DeepSeek V3 | 🌍 信源：Tavily
    
    #### 📰 核心动态
    ...
    
    ---
    #### 🔭 深度战略研判
    ...
    
    *(AI总结，仅供参考)*
    """
    return call_deepseek(prompt)

def push_wechat(content):
    try:
        if not content or not WECOM_WEBHOOK_URL: return
    except NameError: return

    print("3.1 推送至企微...")
    if len(content.encode('utf-8')) > 4000:
        content = content[:3000] + "\n\n...(内容过长截断)... \n*(AI总结，仅供参考)*"
    
    headers = {"Content-Type": "application/json"}
    data = {"msgtype": "markdown", "markdown": {"content": content}}
    try: requests.post(WECOM_WEBHOOK_URL, headers=headers, data=json.dumps(data))
    except: pass

def push_feishu(content):
    try:
        if not content or not FEISHU_WEBHOOK_URL: return
    except NameError: return

    print("3.2 推送至飞书...")
    
    # 🔥 修改点 2：底部时间戳使用北京时间
    current_time = get_beijing_time().strftime('%Y-%m-%d %H:%M')

    if len(content.encode('utf-8')) > 30000:
         content = content[:10000] + "\n...(内容过长截断)..."

    headers = {"Content-Type": "application/json"}
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {"content": "🚀 AI 全球情报内参", "tag": "plain_text"}
            },
            "elements": [
                {"tag": "markdown", "content": content},
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": f"更新时间: {current_time} (北京时间)"}]
                }
            ]
        }
    }
    try:
        requests.post(FEISHU_WEBHOOK_URL, headers=headers, data=json.dumps(payload))
        print("✅ 飞书推送完成")
    except Exception as e:
        print(f"❌ 飞书错误: {e}")

if __name__ == "__main__":
    raw = get_realtime_news()
    if raw:
        text = ai_process_content(raw)
        push_wechat(text)
        push_feishu(text)
    else:
        print("无数据")
