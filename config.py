"""
AI商业资讯雷达
统一配置管理模块

所有敏感配置：
- API Key
- Webhook
- 用户权限密码

统一从环境变量读取
"""

import os
from dotenv import load_dotenv


# 本地开发读取.env
load_dotenv()


# =========================
# 用户权限配置
# =========================


APP_ACCESS_CODE = os.getenv(
    "APP_ACCESS_CODE"
)


ADMIN_ACCESS_CODE = os.getenv(
    "ADMIN_ACCESS_CODE"
)



# =========================
# AI服务配置
# =========================


TAVILY_API_KEY = os.getenv(
    "TAVILY_API_KEY"
)


DEEPSEEK_API_KEY = os.getenv(
    "DEEPSEEK_API_KEY"
)


BOCHA_API_KEY = os.getenv(
    "BOCHA_API_KEY"
)



# =========================
# 消息推送
# =========================


FEISHU_WEBHOOK_URL = os.getenv(
    "FEISHU_WEBHOOK_URL"
)


WECOM_WEBHOOK_URL = os.getenv(
    "WECOM_WEBHOOK_URL"
)



def check_required_config():

    """
    检查核心配置是否存在
    """

    required = {

        "APP_ACCESS_CODE":
            APP_ACCESS_CODE,

        "ADMIN_ACCESS_CODE":
            ADMIN_ACCESS_CODE,

        "TAVILY_API_KEY":
            TAVILY_API_KEY,

        "DEEPSEEK_API_KEY":
            DEEPSEEK_API_KEY,

        "BOCHA_API_KEY":
            BOCHA_API_KEY

    }


    missing=[]


    for name,value in required.items():

        if not value:

            missing.append(name)



    if missing:

        raise RuntimeError(
            "缺少系统配置:"
            +
            ",".join(missing)
        )
