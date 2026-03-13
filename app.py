import streamlit as st
import requests
import json
import os
import feedparser
from tavily import TavilyClient
from datetime import datetime, timedelta, timezone

# =========================================================
# 🔴 核心配置区 (确保在运行前配置好这些环境变量或 Streamlit Secrets)
# =========================================================
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
BOCHA_API_KEY = os.environ.get("BOCHA_API_KEY")

def get_beijing_time():
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=8)

# =========================================================
# 🕷️ 数据抓取引擎 (保持原样)
# =========================================================
def get_tavily_data(query="AI artificial intelligence breaking news"):
    if not TAVILY_API_KEY: return []
    try:
        tavily = TavilyClient(api_key=TAVILY_API_KEY)
        return tavily.search(query=query, search_depth="advanced", max_results=25, days=1).get('results', [])
    except Exception: return []

def get_bocha_data(query="AI大模型 商业化 落地应用"):
    if not BOCHA_API_KEY: return [] 
    url = "https://api.bochaai.com/v1/web-search"
    headers = {"Authorization": f"Bearer {BOCHA_API_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.post(url, json={"query": query, "freshness": "oneDay", "count": 25}, headers=headers, timeout=10)
        items = response.json().get('data', {}).get('webPages', {}).get('value', [])
        return [{"title": i.get('name'), "url": i.get('url'), "content": i.get('snippet')} for i in items if len(i.get('name', '')) > 6]
    except Exception: return []

def get_rss_data(rss_sources=["https://36kr.com/feed", "https://www.ithome.com/rss/"]):
    results = []
    try:
        for url in rss_sources:
            for entry in feedparser.parse(url).entries[:15]:
                results.append({"title": entry.title, "url": entry.link, "content": entry.summary[:200] if hasattr(entry, 'summary') else entry.title})
        return results
    except Exception: return []

def get_realtime_news():
    all_news = get_tavily_data() + get_bocha_data() + get_rss_data()
    unique_news, seen = [], set()
    for news in all_news:
        if news.get('url') and news['url'] not in seen:
            unique_news.append(news)
            seen.add(news['url'])
    return unique_news

# =========================================================
# 🧠 AI 处理引擎 (加入断点截流指令)
# =========================================================
def call_deepseek(prompt):
    if not DEEPSEEK_API_KEY: return "⚠️ 系统错误：未配置 DeepSeek API Key"
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-ai/DeepSeek-V3", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=240)
        return response.json()['choices'][0]['message']['content']
    except Exception as e: return f"⚠️ 大模型调用失败: {e}"

def ai_process_content(news_data):
    if not news_data: return "⚠️ 未抓取到数据"
    beijing_date = get_beijing_time().strftime('%Y-%m-%d')
    data_str = json.dumps(news_data[:80], ensure_ascii=False)

    prompt = f"""
    你是一名极其冷酷、务实的【人工智能】商业战略顾问。
    请基于原始数据撰写《AI 散户搞钱与避坑内参》。

    ❌ 致命红线：
    1. 绝对禁止使用“$”符号，用中文“美元”代替。
    2. 必须且只能输出纯文本内容，不要有任何代码块包裹。

    ✅ 任务要求：
    第一部分：⭐ 核心情报内参 (强制写满 20 条)
    * 提取最相关的 20 条情报。
    * ⚠️ 绝对红线（截流标记）：在第 5 条情报写完后，必须、立刻、单独空一行输出这串字符：“===PAYWALL===”，然后再继续写第 6 条！

    第二部分：🔭 深度战略研判 (宏观大局)
    包含：1. 到底发生了什么？ 2. 钱流向了哪里？ 3. 我们该怎么干？

    第三部分：💰 普通人无门槛搞钱专区 (3个落地案例)
    强制零成本、无代码、只做C端变现。包含：🎯 核心逻辑、🛠️ 工具与平台、👣 极简落地动作。

    第四部分：🛑 散户入局 AI 的 3 个致命避坑指南
    包含：🕳️ 陷阱表象、🩸 致命逻辑、🛡️ 破局自保。
    
    原始数据：{data_str}
    """
    return call_deepseek(prompt)

# =========================================================
# 🛡️ 极简缓存大法 (每天只耗费一次 API)
# =========================================================
@st.cache_data(ttl=86400) 
def generate_daily_report(today_date_str):
    raw_news = get_realtime_news()
    return ai_process_content(raw_news)

# =========================================================
# 🚀 网页前端渲染与截流 UI
# =========================================================
st.set_page_config(page_title="AI 实战情报中心", page_icon="🚀", layout="centered")

# 强制注入 CSS 样式
st.markdown("""
<style>
.blurred-content {
    color: transparent;
    text-shadow: 0 0 15px rgba(255, 255, 255, 0.7);
    user-select: none;
    pointer-events: none;
    margin-bottom: 50px;
}
.paywall-box {
    background-color: #1E1E1E;
    border: 2px solid #FF4B4B;
    border-radius: 12px;
    padding: 30px;
    text-align: center;
    margin-top: -120px;
    position: relative;
    z-index: 999;
    box-shadow: 0px 20px 50px rgba(0,0,0,0.9);
}
</style>
""", unsafe_allow_html=True)

today_str = get_beijing_time().strftime("%Y-%m-%d")

st.title("🚀 AI 一人公司：每日实战情报中心")
st.caption(f"当前版本：V1.0 | 算力驱动：DeepSeek V3 | 更新日期：{today_str}")

with st.spinner("正在从云端引擎提取今日内参，请稍候..."):
    report_content = generate_daily_report(today_str)

# 执行截流逻辑
if report_content and "===PAYWALL===" in report_content:
    parts = report_content.split("===PAYWALL===")
    free_part = parts[0]
    paid_part = parts[1]
    
    # 1. 毫无保留地展示前 5 条
    st.markdown(free_part)
    
    # 2. 露出诱人的标题钩子
    st.markdown("### 🔭 二、 深度战略研判 (独家大局观)")
    st.markdown("### 💰 三、 普通人无门槛搞钱专区 (3个落地案例)")
    st.markdown("### 🛑 四、 散户入局 AI 的 3 个致命避坑指南")
    
    # 3. 渲染高斯模糊的后续内容
    st.markdown(f'<div class="blurred-content">{paid_part[:600]}...</div>', unsafe_allow_html=True)
    
    # 4. 残暴的拦截弹窗
    st.markdown("""
    <div class="paywall-box">
        <h2 style="color: #FF4B4B; margin-bottom: 5px;">⚠️ 算力保护限制</h2>
        <h4 style="margin-bottom: 15px;">你已免费阅读今日 Top 5 商业情报。</h4>
        <p style="color: #AAAAAA; line-height: 1.6; margin-bottom: 20px;">
            解锁完整 20 条高价值内参及<b>《小白首单实操防坑手册 (V1.0)》</b><br>
            请扫描下方主理人微信提取密码<br>
            <span style="color:#FF4B4B; font-weight:bold;">（每日仅限 50 个免费内测名额，次日零点刷新）</span>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # =======================================================
    # 🎯 你的二维码在这里添加！！！
    # =======================================================
    # 极其简单：把你的微信二维码图片命名为 qr.png，放在代码同级目录下！
    try:
        st.image("qr.png", width=250, use_column_width=False)
    except:
        st.error("⚠️ 未找到二维码图片，请将微信二维码命名为 qr.png 并放在代码目录下！")

else:
    # 容错：如果模型未按指令输出 PAYWALL，则直接全量显示
    st.markdown(report_content)
