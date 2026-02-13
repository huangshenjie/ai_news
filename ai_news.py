import requests
import json
import feedparser
from datetime import datetime, timedelta

# =========================================================
# 【请确保此处粘贴了正确的 Webhook URL】
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=0ea95932-128f-47ca-bc26-0df9fbd41de0"
# =========================================================

def fetch_real_news():
    # 预设高质量 AI RSS 源
    rss_sources = [
        {"name": "机器之心", "url": "https://www.jiqizhixin.com/rss"},
        {"name": "36Kr AI", "url": "https://36kr.com/feed/ai"},
        {"name": "OpenAI Blog", "url": "https://openai.com/news/rss.xml"}
    ]
    
    all_news = []
    
    for source in rss_sources:
        try:
            feed = feedparser.parse(source['url'])
            for entry in feed.entries[:10]:  # 每个源取前10条
                all_news.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": source['name']
                })
        except Exception as e:
            print(f"抓取 {source['name']} 失败: {e}")

    # 仅保留最新的 20 条
    return all_news[:20]

def format_markdown(news_list):
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    content = f"### 🤖 实时 AI 资讯追踪 ({today})\n"
    content += f"> 当前监测到最新的 **20** 条行业动态：\n\n"
    
    for i, news in enumerate(news_list, 1):
        # 加上具体的来源标识，反应实时变化
        content += f"{i}. **[{news['source']}]** {news['title']}\n"
        content += f"   [查看详情]({news['link']})\n"
        
    content += "\n---\n> *数据源已切换至实时 RSS 抓取，确保信息真实具体。*"
    return content

def push_to_weixin(text):
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "markdown",
        "markdown": {"content": text}
    }
    requests.post(WEBHOOK_URL, headers=headers, data=json.dumps(data))

if __name__ == "__main__":
    real_news = fetch_real_news()
    if real_news:
        markdown_text = format_markdown(real_news)
        push_to_weixin(markdown_text)
    else:
        print("未获取到新资讯")
