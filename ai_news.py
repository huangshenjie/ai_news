import requests
import json
import os
import feedparser
from tavily import TavilyClient
from datetime import datetime, timedelta, timezone

# =========================================================
# 🔴 核心配置区 (Bocha 单兵测试版)
# =========================================================
# 请务必填入你刚才在博查后台获取的 API Key
BOCHA_API_KEY = "sk-2fae396b559249da8dab4fe7de1ae125" 

# 其他 Key 暂时留空也没事，因为这次我们只测博查
TAVILY_API_KEY = "在此粘贴Tavily_Key"
DEEPSEEK_API_KEY = "sk-gvvsglcyhujlvprlryxtwduxvbgwfyzqngzqesyvwvucjnyw" 
WECOM_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0"
FEISHU_WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/54e2a16a-8409-46c7-bd62-a169bc3e063f"
# =========================================================

def get_beijing_time():
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=8)

# ---------------------------------------------------------
# 🇨🇳 数据源 B: 博查 Bocha (本次测试的主角)
# ---------------------------------------------------------
def get_bocha_data():
    print("👉 正在发起博查搜索 (Bocha)...")
    
    # 简单的 Key 检查
    if "在此粘贴" in BOCHA_API_KEY or not BOCHA_API_KEY:
        print("❌ 错误：Bocha Key 未配置！请填入 Key 后再试。")
        return []
        
    url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {BOCHA_API_KEY}",
        "Content-Type": "application/json"
    }
    # 专门针对国内 AI 圈子的搜索词
    payload = {
        "query": "DeepSeek 商业化落地 最新进展 OR OpenAI Sora 最新消息 site:36kr.com OR site:qbitai.com",
        "freshness": "oneDay", # 只看 1 天内的，确保是新闻
        "count": 10
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            results = []
            # 解析博查返回的数据结构
            for item in data.get('data', []):
                results.append({
                    "title": item.get('name') or item.get('title'),
                    "url": item.get('url'),
                    "content": item.get('snippet') or item.get('summary')
                })
            
            if results:
                print(f"✅ 博查测试成功！抓取到 {len(results)} 条数据。")
                # 打印第一条看看质量
                print(f"   第一条标题: {results[0]['title']}")
            else:
                print("⚠️ 博查请求成功，但没搜到数据 (可能关键词太偏或今天无新闻)")
                
            return results
        else:
            print(f"❌ 博查 API 报错: 状态码 {response.status_code}")
            print(f"   错误信息: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ 网络请求异常: {e}")
        return []

# ---------------------------------------------------------
# ⚙️ 核心调度逻辑 (已锁定为：仅博查)
# ---------------------------------------------------------
def get_realtime_news():
    print("🔒 启动【博查单兵测试】模式...")
    all_news = []
    
    # 1. 暂时禁用 Tavily
    # print("🚫 (测试中) Tavily 已禁用")
    
    # 2. ⚡ 只运行博查
    bocha_data = get_bocha_data()
    if bocha_data:
        all_news.extend(bocha_data)
    
    # 3. 🚫 严厉禁用 RSS (确保你看到的是博查的真实实力)
    print("🚫 (测试中) RSS 兜底已禁用。如果博查失败，程序将直接结束。")
    
    print(f"📊 最终测试获取情报数: {len(all_news)} 条")
    return all_news

# ---------------------------------------------------------
# 🧠 DeepSeek 与 推送 (保持不变，用于验证数据能否走通全流程)
# ---------------------------------------------------------
def call_deepseek(prompt):
    print("2. 正在调用 DeepSeek 进行测试清洗...")
    if "在此粘贴" in DEEPSEEK_API_KEY:
        print("⚠️ DeepSeek Key 未配置，跳过清洗步骤")
        return "【测试模式】博查数据获取成功，但 DeepSeek 未配置，无法生成研报。"

    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False, "temperature": 0.7, "max_tokens": 2000
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        return None
    except: return None

def ai_process_content(news_data):
    if not news_data: return None
    data_str = json.dumps(news_data[:5], ensure_ascii=False) # 测试只发5条
    prompt = f"请把这些新闻简单总结成一个列表：\n{data_str}"
    return call_deepseek(prompt)

def push_wechat(content):
    if not content or "在此粘贴" in WECOM_WEBHOOK_URL: 
        print("⚠️ 企微 Webhook 未配置，跳过推送")
        return
    print("3. 正在尝试推送到企微...")
    requests.post(WECOM_WEBHOOK_URL, json={"msgtype": "markdown", "markdown": {"content": content}})

if __name__ == "__main__":
    # 1. 获取数据
    raw_data = get_realtime_news()
    
    # 2. 如果有数据，尝试走完后面的流程
    if raw_data:
        final_text = ai_process_content(raw_data)
        if final_text:
            print("\n🎉 测试报告内容预览：")
            print("-" * 20)
            print(final_text[:100] + "...")
            print("-" * 20)
            push_wechat(final_text)
    else:
        print("\n❌ 测试失败：博查没有返回任何数据。请检查 Key 或网络。")
