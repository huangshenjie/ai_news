import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()
import ai_news 

# ==========================================
# 🎯 赛道精细化配置字典 (完美契合 Plan 要求)
# ==========================================
INDUSTRY_CONFIG = {
    "🤖 人工智能与大模型": {
        "tavily_q": "AI startup funding open-source LLM AI infrastructure monetization generative AI",
        "bocha_q": "大模型商业化 算力 DeepSeek落地应用 AI变现 融资",
        "title": "AI 商业套利与实战内参",
        "rss_urls": ["https://36kr.com/feed", "https://www.ithome.com/rss/"]
    },
    "📱 自媒体与流量变现": {
        "tavily_q": "Creator economy TikTok algorithm update YouTube monetization social media growth hacking",
        "bocha_q": "抖音算法调整 小红书带货 视频号变现 短视频矩阵玩法 直播切片 创作者经济",
        "title": "自媒体流量套利实战内参",
        "rss_urls": ["https://36kr.com/feed"] # 采用泛商业权威源保底
    },
    "🛒 跨境电商与出海": {
        "tavily_q": "Cross-border e-commerce policy US tariffs Amazon seller updates TikTok Shop global trade",
        "bocha_q": "亚马逊封号 TikTok Shop美区政策 独立站引流 Temu卖家 关税 物流",
        "title": "跨境电商出海搞钱内参",
        "rss_urls": ["https://36kr.com/feed"] # 采用泛商业权威源保底
    }
}

# ==========================================
# 网页前端 UI 封装层
# ==========================================
st.set_page_config(page_title="商业情报套利雷达", page_icon="💰", layout="centered")

st.title("💰 全球信息差与套利雷达")
st.markdown("---")

st.markdown("""
**系统状态：** 🟢 跨端爬虫就绪 | 🔴 **【套利专区】+【战略研判】双擎全开** **接入信源：** 国际全网 (Tavily) + 国内垂类 (Bocha) + 核心媒资 (RSS)  
**驱动引擎：** DeepSeek-V3 商业操盘手模式
""")

selected_industry = st.selectbox("请选择要深度挖掘的搞钱赛道：", list(INDUSTRY_CONFIG.keys()))
current_config = INDUSTRY_CONFIG[selected_industry]

st.info(f"已锁定赛道：**{selected_industry}**。系统将提取前 20 条核心情报，并生成对应套利方案与宏观研判。")

if st.button(f"⚡ 生成【{current_config['title']}】", type="primary", use_container_width=True):
    with st.spinner(f'🕵️‍♂️ 正在穿透全网搜捕【{selected_industry}】情报并推演变现模型... (需约 3 分钟)'):
        try:
            raw_data = ai_news.get_realtime_news(
                tavily_query=current_config['tavily_q'],
                bocha_query=current_config['bocha_q'],
                rss_urls=current_config['rss_urls']
            )
            
            if not raw_data:
                st.error("❌ 抓取失败，请检查网络或 API 额度。")
            else:
                st.toast(f"✅ 捕获 {len(raw_data)} 条底层素材！强制大模型启动套利逻辑...")
                
                final_report = ai_news.ai_process_content(
                    news_data=raw_data,
                    industry_focus=selected_industry.split(" ")[1],
                    report_title=current_config['title']
                )
                
                if final_report:
                    st.success("✅ 全维研判报告生成完毕！")
                    st.markdown("### 📊 最终变现与战略研判")
                    st.markdown(final_report)
                else:
                    st.error("❌ DeepSeek 推演失败，请检查命令行报错。")
        except Exception as e:
            st.error(f"❌ 系统发生严重错误: {str(e)}")