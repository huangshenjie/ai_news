import streamlit as st
import os
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()
import ai_news 

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
        "title": "AI 商业套利与实战内参",
        "rss_urls": ["https://36kr.com/feed", "https://www.ithome.com/rss/"]
    },
    "📱 自媒体与流量变现": {
        "tavily_q": "Creator economy TikTok algorithm update YouTube monetization social media growth hacking",
        "bocha_q": "抖音算法调整 小红书带货 视频号变现 短视频矩阵玩法 直播切片 创作者经济",
        "title": "自媒体流量套利实战内参",
        "rss_urls": ["https://36kr.com/feed"] 
    },
    "🛒 跨境电商与出海": {
        "tavily_q": "Cross-border e-commerce policy US tariffs Amazon seller updates TikTok Shop global trade",
        "bocha_q": "亚马逊封号 TikTok Shop美区政策 独立站引流 Temu卖家 关税 物流",
        "title": "跨境电商出海搞钱内参",
        "rss_urls": ["https://36kr.com/feed"] 
    }
}

# ==========================================
# ✂️ 视觉欺骗引擎 (暴力坐标切割法)
# ==========================================
def truncate_news_for_ui(full_report):
    """
    无视大模型的段落排版，直接寻找第 6 条和战略研判的物理坐标进行切割。
    """
    # 1. 寻找第 6 条的起始坐标 (容错: 6. | 6、 | **6. | **6、)
    match_6 = re.search(r'\n\s*(\*\*6\.|6\.|6、|\*\*6、)', full_report)
    
    # 2. 寻找第二部分(战略研判)的起始坐标 (容错: 二、 | 第二部分 | 🔭 | 深度战略研判)
    match_part2 = re.search(r'\n\s*(### |## |# )?(二、|第二部分|🔭|深度战略研判)', full_report)
    
    # 战术A：如果同时找到了第6条和第二部分，实施精准掏空
    if match_6 and match_part2 and match_6.start() < match_part2.start():
        cut_start = match_6.start()
        cut_end = match_part2.start()
        
        interceptor = "\n\n> 🔒 **[权限限制] 第 6 至 20 条核心 S 级情报已折叠。**\n> *(完整 20 条每日首发未删减版，已推送至内部核心圈。)*\n\n"
        
        # 拼接：前 5 条 + 拦截话术 + 第二部分及后续所有内容
        return full_report[:cut_start] + interceptor + full_report[cut_end:]
    
    # 战术B：大模型排版彻底崩盘（没找到第二部分），但找到了第6条，直接一刀切断
    elif match_6:
         cut_start = match_6.start()
         interceptor = "\n\n> 🔒 **[权限限制] 第 6 至 20 条核心 S 级情报已折叠。**\n> *(底层排版解析异常，为保护核心算力，后续模块已全量隐藏。)*\n\n"
         return full_report[:cut_start] + interceptor
         
    # 战术C：连数字6都没找到（大模型彻底失控），原样放行，确保网页不报错白屏
    return full_report
# ==========================================
# 🛡️ 极简缓存大法 (每天每赛道只耗费一次算力)
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
st.set_page_config(page_title="商业情报套利雷达", page_icon="💰", layout="centered")

st.markdown("""
<style>
.qr-box { background-color: #121212; border: 2px solid #FF4B4B; border-radius: 12px; padding: 25px; text-align: center; margin-top: 40px; box-shadow: 0px 10px 30px rgba(0,0,0,0.8); }
</style>
""", unsafe_allow_html=True)

st.title("💰 全球信息差与套利雷达")
st.markdown("---")

st.markdown("""
**系统状态：** 🟢 跨端爬虫就绪 | 🔴 **【套利专区】+【战略研判】双擎全开** **接入信源：** 国际全网 (Tavily) + 国内垂类 (Bocha) + 核心媒资 (RSS)  
**驱动引擎：** DeepSeek-V3 商业操盘手模式
""")

selected_industry = st.selectbox("请选择要深度挖掘的搞钱赛道：", list(INDUSTRY_CONFIG.keys()))
current_config = INDUSTRY_CONFIG[selected_industry]

st.info(f"已锁定赛道：**{selected_industry}**。系统将提取核心情报，并生成对应套利方案与宏观研判。")

st.markdown("---")
# ==========================================
# 🛑 商业风控与私域引流锁
# ==========================================
unlock_code = st.text_input("🔑 请输入内部邀请码解锁系统 (加主理人微信免费获取)：", type="password")

if unlock_code == "0515":
    if st.button(f"⚡ 消耗算力，生成【{current_config['title']}】", type="primary", use_container_width=True):
        today_str = get_beijing_time().strftime("%Y-%m-%d")
        
        with st.spinner(f'🕵️‍♂️ 正在穿透全网搜捕【{selected_industry}】情报并推演变现模型...'):
            try:
                # 触发底层全量抓取与缓存 (此时你的飞书收到全量 20 条)
                full_report = generate_cached_report(today_str, selected_industry, current_config)
                
                if full_report:
                    st.success("✅ 全维研判报告生成完毕！")
                    
                    # ✂️ 启动正则截断：只保留前 5 条情报，后续部分完好无损
                    display_report = truncate_news_for_ui(full_report)
                    
                    st.markdown("### 📊 最终变现与战略研判")
                    st.markdown(display_report)
                    
                    # ==========================================
                    # 🎯 底部强力逼单二维码
                    # ==========================================
                    st.markdown("""
                    <div class="qr-box">
                        <h3 style="color: #FF4B4B; margin-bottom: 5px;">⚠️ 想要解锁被折叠的 15 条 S 级情报？</h3>
                        <p style="color: #AAAAAA; font-size: 15px; margin-bottom: 15px;">
                            本页面为体验版，已开启算力保护限制。<br>
                            扫描下方主理人微信，获取<b>今日无删减版情报 +《小白首单实操防坑手册》</b>。<br>
                            <span style="color:#FF4B4B; font-weight:bold;">（内部社群每日仅限 50 个免费名额，满员即关）</span>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    try:
                        st.image("qr.png", width=220, use_column_width=False)
                    except:
                        st.error("⚠️ 未找到二维码图片，请将微信二维码命名为 qr.png 并放在代码目录下！")

                else:
                    st.error("❌ 抓取或推理失败，请检查网络或 API 额度。")
            except Exception as e:
                st.error(f"❌ 系统发生严重错误: {str(e)}")
elif unlock_code != "":
    st.error("❌ 邀请码错误或已失效！请返回抖音/小红书后台私信获取最新授权。")

