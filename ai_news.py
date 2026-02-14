import requests
import json
import os
import feedparser
from tavily import TavilyClient
from datetime import datetime, timedelta, timezone

# =========================================================
# 🔴 核心配置区 (从环境变量读取，安全第一)
# =========================================================
# 在本地测试时，如果没有设置环境变量，请手动将 os.environ.get(...) 替换为具体的 Key
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-gvvsglcyhujlvprlryxtwduxvbgwfyzqngzqesyvwvucjnyw")
WECOM_WEBHOOK_URL = os.environ.get("WECOM_WEBHOOK_URL", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0")
FEISHU_WEBHOOK_URL = os.environ.get("FEISHU_WEBHOOK_URL", "https://open.feishu.cn/open-apis/bot/v2/hook/54e2a16a-8409-46c7-bd62-a169bc3e063f")

# 如果你想用博查 Bocha (方案B)，可以在这里填 Key，或者留空跳过
BOCHA_API_KEY = os.environ.get("BOCHA_API_KEY", "") 
# =========================================================

def get_beijing_time():
    """获取北京时间"""
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=8)

# ---------------------------------------------------------
# 🛡️ 数据源层：双保险机制 (Tavily -> Bocha -> RSS)
# ---------------------------------------------------------

def get_tavily_news():
    """方案 A: 全球搜索 (Tavily)"""
    if not TAVILY_API_KEY:
        print("⚠️ 未配置 Tavily Key，跳过方案 A")
        return []
        
    print("1. 正在尝试全球搜索 (Tavily)...")
    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
        query = "全球 AI 人工智能 行业动态 最新资讯 (OpenAI OR DeepSeek OR 字节跳动 OR 阿里 OR 腾讯) site:36kr.com OR site:jiqizhixin.com OR site:ithome.com OR site:qq.com OR site:mp.weixin.qq.com"
        response = tavily.search(query=query, search_depth="advanced", max_results=15, days=1)
        results = response.get('results', [])
        print(f"✅ Tavily 获取成功: {len(results)} 条")
        return results
    except Exception as e:
        print(f"❌ Tavily 搜索失败: {e}")
        return []

def get_bocha_news():
    """方案 B: 国内深度搜索 (博查 Bocha) - 可选"""
    if not BOCHA_API_KEY:
        return []

    print("🔄 正在尝试博查搜索 (Bocha)...")
    url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {BOCHA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": "DeepSeek 商业落地 OR OpenAI 最新动态 site:36kr.com",
        "freshness": "oneDay",
        "count": 5
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = [{"title": item['name'], "url": item['url'], "content": item['snippet']} for item in data.get('data', [])]
            print(f"✅ 博查获取成功: {len(results)} 条")
            return results
    except Exception as e:
        print(f"❌ 博查请求异常: {e}")
    return []

def get_rss_news():
    """方案 C: 免费 RSS 兜底 (36Kr / IT之家)"""
    print("🛡️ 正在启动免费 RSS 兜底 (36Kr)...")
    rss_url = "https://36kr.com/feed" 
    try:
        feed = feedparser.parse(rss_url)
        results = []
        for entry in feed.entries[:10]: # 只取前10条
            results.append({
                "title": entry.title,
                "url": entry.link,
                "content": entry.summary[:200] if hasattr(entry, 'summary') else entry.title
            })
        print(f"✅ RSS 获取成功: {len(results)} 条")
        return results
    except Exception as e:
        print(f"❌ RSS 抓取失败: {e}")
        return []

def get_realtime_news_mixed():
    """混合数据获取主入口"""
    all_news = []
    
    # 1. 尝试 Tavily
    tavily_data = get_tavily_news()
    if tavily_data:
        all_news.extend(tavily_data)
        
    # 2. 尝试 Bocha (如果有 Key)
    bocha_data = get_bocha_news()
    if bocha_data:
        all_news.extend(bocha_data)
        
    # 3. 如果前两者加起来数据太少 (< 5条)，强制启动 RSS 兜底
    if len(all_news) < 5:
        print("⚠️ 数据不足，强制启动 RSS 补充...")
        rss_data = get_rss_news()
        all_news.extend(rss_data)
        
    print(f"🚀 最终获取原始情报总数: {len(all_news)}")
    return all_news

# ---------------------------------------------------------
# 🧠 认知层：DeepSeek 处理
# ---------------------------------------------------------

def call_deepseek(prompt):
    print("2. 正在调用 DeepSeek V3 进行清洗与分析...")
    if not DEEPSEEK_API_KEY:
        print("❌ 未配置 DEEPSEEK_API_KEY")
        return None
        
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False, "temperature": 0.7, "max_tokens": 4096
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"❌ DeepSeek API 错误: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 网络请求异常: {e}")
        return None

def ai_process_content(news_data):
    if not news_data: return None
    
    beijing_date = get_beijing_time().strftime('%Y-%m-%d')
    
    # 将数据转为 JSON 字符串，防止 Prompt 过长，只取前 25 条
    data_str = json.dumps(news_data[:25], ensure_ascii=False)

    prompt = f"""
    你是一名具有商业洞察力的 AI 战略顾问。请根据以下原始搜索数据（可能包含重复或无关信息），为我撰写一份【高价值】的行业内参。
    数据：{data_str}

    🔥 **第一部分：资讯追踪 (15-20条)**
    1. **去重与清洗**：合并相似新闻，剔除无关广告。
    2. **筛选标准**：保留最有技术含量或商业影响力的条目。
    3. **标题格式**：
       - ✅ **标签必须精准细分**：使用 **[融资动态]**、**[技术突破]**、**[高层变动]**、**[政策风向]**、**[新品发布]**、**[算力基建]**、**[开源生态]**。
       - ✅ 必须使用长句标题（主谓宾+核心影响）。
    4. **链接要求**：保留原始链接。
    
    🔥 **第二部分：深度战略研判**
    1. **行业变局**：一句话总结今天的市场最大变化。
    2. **崛起风口**：指出一个潜在的赚钱机会。
    3. **落地机会**：给普通创业者的一个建议。

    📝 **输出格式范例**：
    ### 🚀 AI 全球情报内参 ({beijing_date})
    > 🧠 智能驱动：DeepSeek V3 | 🌍 信源：全网聚合
    
    #### 📰 核心动态
    1. **[融资动态] 谷歌计划发行百年期债券筹资 200 亿美元，用于 AI 算力基建狂飙**
       🔗 [来源](url)
    ...
    
    ---
    #### 🔭 深度战略研判
    ...
    
    *(AI总结，仅供参考)*
    """
    return call_deepseek(prompt)

# ---------------------------------------------------------
# 📢 触达层：多渠道分发
# ---------------------------------------------------------

def push_wechat(content):
    if not content or not WECOM_WEBHOOK_URL: return
    print("3.1 推送至企微...")
    # 简单的长度保护
    if len(content.encode('utf-8')) > 4000:
        content = content[:3000] + "\n\n...(内容过长截断)..."
        
    headers = {"Content-Type": "application/json"}
    data = {"msgtype": "markdown", "markdown": {"content": content}}
    try: 
        resp = requests.post(WECOM_WEBHOOK_URL, headers=headers, data=json.dumps(data))
        print(f"企微推送结果: {resp.text}")
    except Exception as e: 
        print(f"企微推送失败: {e}")

def push_feishu(content):
    if not content or not FEISHU_WEBHOOK_URL: return
    print("3.2 推送至飞书...")
    current_time = get_beijing_time().strftime('%Y-%m-%d %H:%M')
    
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
        resp = requests.post(FEISHU_WEBHOOK_URL, headers=headers, data=json.dumps(payload))
        print(f"飞书推送结果: {resp.text}")
    except Exception as e:
        print(f"❌ 飞书错误: {e}")

# ---------------------------------------------------------
# 🚀 主程序入口
# ---------------------------------------------------------

if __name__ == "__main__":
    print("🚀 启动 AI 情报自动化系统...")
    
    # 1. 获取数据 (双保险模式)
    raw_data = get_realtime_news_mixed()
    
    if raw_data:
        # 2. AI 清洗与生成
        final_report = ai_process_content(raw_data)
        
        if final_report:
            # 3. 分发
            push_wechat(final_report)
            push_feishu(final_report)
            print("✅ 所有任务执行完毕")
        else:
            print("⚠️ DeepSeek 生成内容为空")
    else:
        print("⚠️ 未获取到任何有效新闻数据")
