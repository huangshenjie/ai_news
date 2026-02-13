import requests
import json
import datetime

# =========================================================
# 【请在此处粘贴你的 Webhook URL】
# 格式如: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxxx
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=7258cb28-bba6-46c7-9993-19c47b6e8b69"
# =========================================================

def get_ai_news():
    """
    模拟获取 AI 资讯的逻辑。
    在实际生产中，你可以接入具体的搜索 API (如 Perplexity 或 Google Search)。
    这里我为你预设了你关注的关键词。
    """
    today = datetime.date.today().strftime('%Y-%m-%d')
    
    # 构建推送内容
    content = f"### 🤖 AI 全球动态追踪 ({today})\n\n"
    
    # 1. OpenAI 动态
    content += "#### 🔥 OpenAI 核心动态\n- [最新] OpenAI 灰度测试下一代推理模型，响应速度提升 30%。\n- [进展] 关于 SearchGPT 的最新整合功能已向 Plus 用户全面开放。\n\n"
    
    # 2. 国内大模型投融资
    content += "#### 💰 国内大模型融投资\n- [融资] 某国产独角兽完成 C 轮融资，估值突破 200 亿人民币。\n- [布局] 头部互联网大厂成立专项 AI 投资基金，聚焦底层算力优化。\n\n"
    
    # 3. 国内 AI 信息汇总
    content += "#### 🇨🇳 国内 AI 信息快报\n- [模型] 智谱、通义千问、文心一言本周发布多项版本迭代。\n- [应用] 某国产办公软件全量接入 AI 助手，实现一键生成 PPT。\n\n"
    
    # 4. 全球爆火 AI 信息
    content += "#### 🌍 全球爆火 AI 趋势\n- [趋势] 全球开发者正在大规模向 Agentic Workflow（智能体工作流）转型。\n- [开源] Meta 发布最新的开源多模态模型，性能直逼闭源顶尖水平。\n\n"
    
    content += "> *推送说明：每日定时抓取全网最具价值信息，过滤公关噪音。*"
    
    return content

def push_to_weixin(text):
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": text
        }
    }
    
    response = requests.post(WEBHOOK_URL, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        print("推送成功")
    else:
        print(f"推送失败，错误代码：{response.text}")

if __name__ == "__main__":
    news_content = get_ai_news()
    push_to_weixin(news_content)