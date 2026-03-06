import requests
import json
import os
from tavily import TavilyClient
from datetime import datetime, timezone, timedelta

# =========================================================
# 🔴 核心配置区
# =========================================================
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY") or "在此粘贴Tavily_Key"
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY") or "在此粘贴DeepSeek_Key"
BOCHA_API_KEY = os.environ.get("BOCHA_API_KEY") or "在此粘贴Bocha_Key"

def get_beijing_time():
    utc_now = datetime.now(timezone.utc)
    return utc_now + timedelta(hours=8)

# ---------------------------------------------------------
# 🌍 深度搜索源 A: Tavily (取消时间限制，进行历史深度挖掘)
# ---------------------------------------------------------
def search_tavily(keyword):
    print("1. 正在启动国际引擎 (Tavily) 进行深度挖掘...")
    if not TAVILY_API_KEY or "在此粘贴" in TAVILY_API_KEY:
        print("⚠️ Tavily Key 未配置，跳过")
        return []
        
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    # 限定高质量文本平台与视频平台描述
    query = f"{keyword} 商业模式 复盘 变现 site:zhuanlan.zhihu.com OR site:juejin.cn OR site:youtube.com OR site:bilibili.com"
    try:
        # 注意：删除了 days=1 参数，获取全局历史数据
        response = tavily.search(query=query, search_depth="advanced", max_results=15)
        results = response.get('results', [])
        print(f"✅ Tavily 挖掘成功: {len(results)} 条碎片")
        return results
    except Exception as e:
        print(f"❌ Tavily 搜索失败: {e}")
        return []

# ---------------------------------------------------------
# 🇨🇳 深度搜索源 B: 博查 Bocha (取消时间限制，深挖国内闭环生态)
# ---------------------------------------------------------
def search_bocha(keyword):
    print("2. 正在启动国内引擎 (Bocha) 穿透微信生态...")
    if not BOCHA_API_KEY or "在此粘贴" in BOCHA_API_KEY:
        print("⚠️ Bocha Key 未配置，跳过")
        return [] 
        
    url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {BOCHA_API_KEY}",
        "Content-Type": "application/json"
    }
    # 重点穿透微信公众号和国内创作者社区
    payload = {
        "query": f"{keyword} 实操 搞钱 独立开发者 一人公司 site:mp.weixin.qq.com OR site:sspai.com",
        "count": 15
        # 注意：故意删除了 "freshness" 参数，我们要搜出经典老案例
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            web_pages = data.get('data', {}).get('webPages', {})
            items_list = web_pages.get('value', [])
            
            results = []
            for item in items_list:
                results.append({
                    "title": item.get('name'),
                    "url": item.get('url'),
                    "content": item.get('snippet')
                })
            print(f"✅ Bocha 挖掘成功: {len(results)} 条碎片")
            return results
        else:
            print(f"❌ Bocha API 错误: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Bocha 请求异常: {e}")
        return []

# ---------------------------------------------------------
# 🧠 DeepSeek 商业大脑：强制表格化输出
# ---------------------------------------------------------
def analyze_cases_with_deepseek(news_data, search_topic):
    print("3. 正在将碎片数据送入 DeepSeek 进行商业逻辑重构...")
    if not DEEPSEEK_API_KEY or "在此粘贴" in DEEPSEEK_API_KEY:
        return "❌ DeepSeek Key 未配置"

    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    
    data_str = json.dumps(news_data[:30], ensure_ascii=False)

    # 🔥 核心：残酷投资人视角的 Prompt，强制 Markdown 表格输出
    prompt = f"""
    你是一个冷酷、极其务实的顶级风险投资人。你现在的任务是从以下杂乱的网页碎片中，挖掘出关于【{search_topic}】的高价值“一人公司/超级个体”搞钱案例。

    **❌ 绝对禁止：**
    1. 严禁脑补和编造数据，不知道就写“无数据”。
    2. 严禁讲废话、煲鸡汤，我只要冰冷的商业逻辑和执行步骤。
    3. 严禁输出列表或段落，**必须且只能以完整的 Markdown 表格形式输出**！

    **✅ 表格必须包含以下确切的列：**
    | 案例名称与来源 | 案例定位(他是谁/做什么) | 核心产品(卖什么赚钱) | 流量密码(怎么获客) | 搞钱逻辑(客单价与营收) | 可复制性与护城河(第一步怎么抄) |

    **挖掘要求：**
    - 至少提炼出 3 到 5 个高价值的独立商业案例。
    - 将参考来源的链接使用 Markdown 语法附在“案例名称”下方，例如：`[案例名](URL)`。
    - 内容要极致精简，一针见血，直指商业模式的核心。

    原始碎片数据如下：
    {data_str}
    """

    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False, "temperature": 0.5, "max_tokens": 4000
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return None
    except Exception as e:
        print(f"❌ 商业大脑运算异常: {e}")
        return None

# ---------------------------------------------------------
# 💾 本地持久化：保存为 Markdown 文件
# ---------------------------------------------------------
def save_to_markdown(content, topic):
    date_str = get_beijing_time().strftime("%Y%m%d_%H%M")
    filename = f"Case_Study_{topic}_{date_str}.md"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 🔍 商业案例深度挖掘报告：{topic}\n\n")
            f.write(f"> 生成时间：{get_beijing_time().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(content)
        print(f"\n🎉 完美收工！多维表格已成功保存至本地文件: 【{filename}】")
        print("💡 提示：你可以直接用 Excel 或 Notion 导入此 md 文件，完美呈现表格格式。")
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")

# ---------------------------------------------------------
# 🚀 挖掘机主程序
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🚀 启动 [一人公司商业挖掘机]...")
    
    # 你可以每次运行前修改这个关键词，定向挖掘不同领域的案例
    target_topic = "AI 知识库 自动化工作流"
    print(f"🎯 本次锁定的挖掘目标：【{target_topic}】\n")

    # 1. 联合收集数据
    raw_data = []
    raw_data.extend(search_tavily(target_topic))
    raw_data.extend(search_bocha(target_topic))
    
    if raw_data:
        print(f"总计获取素材: {len(raw_data)} 条，开始清洗去重...")
        # 简单去重
        unique_data = {item['url']: item for item in raw_data if item.get('url')}.values()
        
        # 2. 深度分析并生成多维表格
        final_table = analyze_cases_with_deepseek(list(unique_data), target_topic)
        
        if final_table:
            print("\n" + "="*50)
            print("👇 挖掘结果预览 👇")
            print("="*50)
            print(final_table)
            print("="*50)
            
            # 3. 自动生成文件
            save_to_markdown(final_table, target_topic.replace(" ", "_"))
        else:
            print("⚠️ 商业大脑未能产出有效结果。")
    else:
        print("❌ 目标领域太冷门或 API 额度耗尽，未挖到任何数据。")
