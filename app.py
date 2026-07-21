import streamlit as st

from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

import ai_news

from config import (
    APP_ACCESS_CODE,
    ADMIN_ACCESS_CODE,
    check_user_config
)

from utils.logger import logger

def get_beijing_time():
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=8)

# ==========================================
# 🎯 赛道精细化配置字典
# ==========================================
INDUSTRY_CONFIG = {
    "🤖 人工智能与大模型": {
        "tavily_q": "AI startup funding open-source LLM AI infrastructure monetization generative AI",
        "bocha_q": "大模型商业化 算力 DeepSeek落地应用 AI变现 融资",
        "title": "AI行业趋势分析报告",
        "rss_urls": ["https://36kr.com/feed", "https://www.ithome.com/rss/"]
    },
    "📱 自媒体内容生态与创作者经济": {
        "tavily_q": "Creator economy TikTok algorithm update YouTube monetization social media growth hacking",
        "bocha_q": "抖音算法调整 小红书带货 视频号变现 短视频矩阵玩法 直播切片 创作者经济",
        "title": "自媒体内容生态趋势分析报告",
        "rss_urls": ["https://36kr.com/feed"] 
    },
    "🛒 跨境电商与全球市场": {
        "tavily_q": "Cross-border e-commerce policy US tariffs Amazon seller updates TikTok Shop global trade",
        "bocha_q": "亚马逊封号 TikTok Shop美区政策 独立站引流 Temu卖家 关税 物流",
        "title": "跨境市场趋势分析报告",
        "rss_urls": ["https://36kr.com/feed"] 
    }
}

# ==========================================
# 🛡️ 报告缓存模块
# ==========================================
@st.cache_data(ttl=86400)
def generate_cached_report(date_str, industry_key, config):
    raw_data = ai_news.get_realtime_news(
        tavily_query=config['tavily_q'],
        bocha_query=config['bocha_q'],
        rss_urls=config['rss_urls']
    )
    if not raw_data:
        return None
        
    return ai_news.ai_process_content(
        news_data=raw_data,
        industry_focus=industry_key.split(" ")[1],
        report_title=config['title']
    )

# ==========================================
# 🚀 网页前端 UI 渲染层
# ==========================================
st.set_page_config(page_title="AI商业情报雷达", page_icon="🤖", layout="centered")
try:

    check_user_config()


except Exception:
    logger.error(
        "用户配置检查失败",
        exc_info=True)
    st.error(
        "系统配置异常，请联系管理员"
    )

    st.stop()
st.markdown("""
<style>
.qr-box { background-color: #121212; border: 2px solid #FF4B4B; border-radius: 12px; padding: 25px; text-align: center; margin-top: 40px; box-shadow: 0px 10px 30px rgba(0,0,0,0.8); }
</style>
""", unsafe_allow_html=True)

st.title("🤖 AI商业情报雷达")
st.caption(
    "基于大语言模型的行业趋势分析与商业洞察平台"
)

st.markdown("""
            **系统能力：**
            🟢 多源信息采集
            🟢 数据清洗与结构化处理
            🟢 大模型智能分析
            🟢 自动化报告生成
            **数据来源：**
            Tavily + Bocha + RSS
            **AI分析引擎：**
            DeepSeek大模型"""
            )

selected_industry = st.selectbox("请选择要深度挖掘的商业赛道：", list(INDUSTRY_CONFIG.keys()))
current_config = INDUSTRY_CONFIG[selected_industry]

st.info(
    f"已选择分析方向：**{selected_industry}**。系统将采集行业信息，并生成趋势分析与商业洞察报告。")

st.markdown("---")

# ==========================================
# 🛡️ 用户权限管理
# ==========================================
unlock_code = st.text_input("🔑  请输入访问邀请码：", type="password")

if unlock_code == ADMIN_ACCESS_CODE:
    st.warning("⚠️ 已进入管理员模式")
    st.info("当前状态：准备执行系统级缓存清理。该操作将抹除今日所有赛道的旧抓取记录。")
    if st.button("清理报告缓存", type="primary"):
        st.cache_data.clear()
        st.success("✅ 报告缓存已清理，请清空密码框，换回邀请码进行测试。")

elif unlock_code == APP_ACCESS_CODE:
    if st.button(f"⚡ 消耗算力，生成【{current_config['title']}】", type="primary", use_container_width=True):
        today_str = get_beijing_time().strftime("%Y-%m-%d")
        
        with st.spinner(f'🕵️‍♂️正在采集【{selected_industry}】行业信息，并生成智能分析报告...'):
            try:
                full_report = generate_cached_report(today_str, selected_industry, current_config)
                
                if full_report:
                    st.success("✅ 全维研判报告生成完毕！")                    
                    st.markdown("### 📊 AI行业分析报告")
                    st.markdown(full_report)
                else:
                    st.error("❌ 抓取或推理失败，请检查网络或 API 额度。")
            except Exception:
                logger.error(
                    "报告生成流程异常",
                    exc_info=True
                )

                st.error(
                    "❌ 系统发生严重错误，请稍后重试"
                )

elif unlock_code != "":
    st.error("❌ 邀请码错误，请检查输入内容。")