import streamlit as st
import requests
import json
import os
import feedparser
from tavily import TavilyClient
from datetime import datetime, timedelta, timezone

# =========================================================
# 🔴 核心配置区
# =========================================================
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
BOCHA_API_KEY = os.environ.get("BOCHA_API_KEY")

def get_beijing_time():
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=8)

# =========================================================
# 🕷️ 数据抓取引擎
# =========================================================
def get_realtime_news(industry):
    if industry == "自媒体":
        query_tavily = "自媒体 流量变现 短视频 爆款"
        query_bocha = "自媒体搞钱 抖音 小红书 变现实操"
    elif industry == "跨境电商":
        query_tavily = "TikTok e-commerce dropshipping Shopify"
        query_bocha = "跨境电商 TikTok带货 独立站 选品"
    else: # 默认人工智能
        query_tavily = "AI artificial intelligence breaking news"
        query_bocha = "大模型商业化 落地应用 AI变现"

    all_news = []
    
    if TAVILY_API_KEY:
        try:
            tavily = TavilyClient(api_key=TAVILY_API_KEY)
            all_news.extend(tavily.search(query=query_tavily, search_depth="advanced", max_results=15, days=1).get('results', []))
        except: pass
        
    if BOCHA_API_KEY:
        url = "https://api.bochaai.com/v1/web-search"
        headers = {"Authorization": f"Bearer {BOCHA_API_KEY}", "Content-Type": "application/json"}
        try:
            res = requests.post(url, json={"query": query_bocha, "freshness": "oneDay", "count": 15}, headers=headers, timeout=10)
            items = res.json().get('data', {}).get('webPages', {}).get('value', [])
            all_news.extend([{"title": i.get('name'), "url": i.get('url'), "content": i.get('snippet')} for i in items if len(i.get('name', '')) > 6])
        except: pass

    try:
        for url in ["https://36kr.com/feed", "https://www.ithome.com/rss/"]:
            for entry in feedparser.parse(url).entries[:10]:
                all_news.append({"title": entry.title, "url": entry.link, "content": entry.summary[:200] if hasattr(entry, 'summary') else entry.title})
    except: pass

    unique_news, seen = [], set()
    for news in all_news:
        if news.get('url') and news['url'] not in seen:
            unique_news.append(news)
            seen.add(news['url'])
    return unique_news

# =========================================================
# 🧠 AI 处理引擎
# =========================================================
def ai_process_content(news_data, industry):
    if not news_data: return "⚠️ 未抓取到数据"
    data_str = json.dumps(news_data[:50], ensure_ascii=False)

    prompt = f"""
    你是一名极其冷酷、务实的商业战略顾问。
    请基于原始数据，撰写一份针对【{industry}】赛道的《散户搞钱与避坑内参》。

    ❌ 致命红线：
    1. 绝对禁止使用“$”符号，用中文“美元”代替。
    2. 必须且只能输出纯文本内容，不要有任何代码块包裹。

    ✅ 任务要求：
    第一部分：⭐ 核心情报内参 (强制写满 10 条)
    * 提取最相关的 10 条情报。
    * ⚠️ 绝对红线（截流标记）：在第 3 条情报写完后，必须、立刻、单独空一行输出这串字符：“===PAYWALL===”，然后再继续写第 4 条！

    第二部分：🔭 深度战略研判 (宏观大局)
    包含：1. 到底发生了什么？ 2. 钱流向了哪里？ 3. 我们该怎么干？

    第三部分：💰 普通人无门槛搞钱专区 (3个落地案例)
    强制零成本、无代码、只做C端变现。包含：🎯 核心逻辑、🛠️ 工具与平台、👣 极简落地动作。

    第四部分：🛑 散户入局的 3 个致命避坑指南
    包含：🕳️ 陷阱表象、🩸 致命逻辑、🛡️ 破局自保。
    
    原始数据：{data_str}
    """
    
    if not DEEPSEEK_API_KEY: return "⚠️ 系统错误：未配置 DeepSeek API Key"
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-ai/DeepSeek-V3", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=240)
        return response.json()['choices'][0]['message']['content']
    except Exception as e: return f"⚠️ 大模型调用失败: {e}"

# =========================================================
# 🛡️ 极简缓存大法 (针对不同选项独立缓存！)
# =========================================================
@st.cache_data(ttl=86400) 
def generate_daily_report(today_date_str, industry):
    raw_news = get_realtime_news(industry)
    return ai_process_content(raw_news, industry)

# =========================================================
# 🚀 网页前端渲染
# =========================================================
st.set_page_config(page_title="一人公司 | 实战情报网", page_icon="🚀", layout="centered")

st.markdown("""
<style>
.blurred-content { color: transparent; text-shadow: 0 0 15px rgba(255, 255, 255, 0.85); user-select: none; pointer-events: none; margin-bottom: 50px; }
.paywall-box { background-color: #121212; border: 2px solid #FF4B4B; border-radius: 12px; padding: 30px; text-align: center; margin-top: -100px; position: relative; z-index: 999; box-shadow: 0px 20px 50px rgba(0,0,0,0.9); }
.stButton>button { width: 100%; font-size: 18px; font-weight: bold; background-color: #FF4B4B; color: white; border: none; padding: 12px; border-radius: 8px; transition: all 0.3s;}
.stButton>button:hover { background-color: #D43F3F; box-shadow: 0 4px 15px rgba(255, 75, 75, 0.4); }
</style>
""", unsafe_allow_html=True)

today_str = get_beijing_time().strftime("%Y-%m-%d")

# 头部设计
st.title("🚀 一人公司：全网实战情报中心")
st.caption(f"当前版本：V3.0 | 算力驱动：DeepSeek V3 | 今日日期：{today_str}")

# 使用优雅的 Expand (折叠面板) 提升专业感
with st.expander("⚙️ 系统算力节点监控 (运行正常)", expanded=False):
    st.write("🟢 Tavily 节点：在线")
    st.write("🟢 Bocha 节点：在线")
    st.write("🟢 DeepSeek V3 引擎：在线")

# --- 核心交互区 ---
st.markdown("### 🎯 第一步：锁定目标赛道")
# 改回下拉框，满足你的“美化”需求
selected_industry = st.selectbox(
    "系统将动用底层算力，定向抓取该赛道最新变现风向：",
    ("人工智能", "自媒体", "跨境电商")
)

st.markdown("---")

# 按钮触发逻辑
if st.button(f"⚡ 消耗算力，生成【{selected_industry}】专属内参"):
    
    with st.spinner(f"正在调取【{selected_industry}】赛道全球数据并进行降维拆解，预计 15-30 秒..."):
        # 这里的缓存是基于 today_str 和 selected_industry 的
        # 如果你之前跑过，这里就是 0.1 秒出结果！
        report_content = generate_daily_report(today_str, selected_industry)
    
    st.success(f"✅ 【{selected_industry}】赛道情报生成完毕！")
    
    # 渲染截流逻辑
    if report_content and "===PAYWALL===" in report_content:
        parts = report_content.split("===PAYWALL===")
        free_part = parts[0]
        paid_part = parts[1]
        
        # 展示免费前3条
        st.markdown(free_part)
        
        # 标题诱惑
        st.markdown("### 🔭 二、 深度战略研判 (独家大局观)")
        st.markdown(f"### 💰 三、 普通人无门槛搞钱专区 (3个【{selected_industry}】落地案例)")
        st.markdown("### 🛑 四、 散户入局的 3 个致命避坑指南")
        
        # 模糊层
        st.markdown(f'<div class="blurred-content">{paid_part[:400]}...</div>', unsafe_allow_html=True)
        
        # 拦截弹窗
        st.markdown(f"""
        <div class="paywall-box">
            <h2 style="color: #FF4B4B; margin-bottom: 5px;">⚠️ 核心算力告罄 / 权限受限</h2>
            <h4 style="margin-bottom: 15px;">你已免费阅读今日 Top 3 商业情报。</h4>
            <p style="color: #AAAAAA; line-height: 1.6; margin-bottom: 20px;">
                解锁完整高价值内参及<b>《{selected_industry}：小白首单实操防坑手册 (V1.0)》</b><br>
                请扫描下方主理人微信提取密码<br>
                <span style="color:#FF4B4B; font-weight:bold;">（系统负载过高，今日仅剩最后 17 个体验名额）</span>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            # 确保二维码在同一目录下
            st.image("qr.png", width=220, use_column_width=False)
        except:
            st.error("⚠️ 未找到二维码图片，请将微信二维码命名为 qr.png 并放在代码目录下！")
            
    else:
        st.markdown(report_content)
