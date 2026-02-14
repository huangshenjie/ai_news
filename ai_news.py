import requests
import json
import os
from datetime import datetime, timedelta, timezone

# =========================================================
# 🔴 核心配置区
# =========================================================
# 请务必确保填入了 Key
BOCHA_API_KEY = "sk-2fae396b559249da8dab4fe7de1ae125" 
# =========================================================

def get_bocha_data_debug():
    print("👉 正在发起博查搜索 (Debug模式)...")
    
    url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {BOCHA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": "DeepSeek 商业化落地 最新进展",
        "freshness": "oneDay",
        "count": 5
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # 🔥 核心调试点：打印原始数据结构 🔥
            print("\n📦【博查返回的原始数据结构】(请截图这部分):")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:1000]) # 只打前1000字防止刷屏
            print("-" * 30)

            # 尝试智能解析（修复之前的 Bug）
            results = []
            
            # 1. 提取核心数据层
            inner_data = data.get('data', {})
            
            # 2. 判断结构类型，防止报错
            items_list = []
            if isinstance(inner_data, list):
                # 情况 A: data 直接是列表
                items_list = inner_data
            elif isinstance(inner_data, dict):
                # 情况 B: data 是字典，列表可能藏在 webPages -> value 里 (常见结构)
                if 'webPages' in inner_data:
                    items_list = inner_data['webPages'].get('value', [])
                elif 'list' in inner_data:
                    items_list = inner_data['list']
                else:
                    # 如果找不到列表，打印键值对帮我们定位
                    print(f"⚠️ 未找到列表，inner_data 的 Keys: {list(inner_data.keys())}")
            
            # 3. 安全遍历
            for item in items_list:
                # 双重保险：确保 item 是字典
                if isinstance(item, dict):
                    results.append({
                        "title": item.get('name') or item.get('title') or "无标题",
                        "url": item.get('url') or item.get('link'),
                        "content": item.get('snippet') or item.get('summary') or item.get('content')
                    })

            if results:
                print(f"✅ 解析成功！抓取到 {len(results)} 条数据。")
                print(f"📄 第一条示例: {results[0]['title']}")
            else:
                print("❌ 解析后列表为空，请检查上方打印的【原始数据结构】")
                
            return results
        else:
            print(f"❌ 状态码错误: {response.status_code}")
            print(response.text)
            return []
            
    except Exception as e:
        import traceback
        print(f"❌ 发生异常: {e}")
        print(traceback.format_exc()) # 打印详细报错位置
        return []

if __name__ == "__main__":
    get_bocha_data_debug()
