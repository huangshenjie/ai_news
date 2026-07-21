"""
AI商业资讯雷达
统一配置管理模块

配置来源：

线上:
Streamlit Secrets

本地:
.env
"""


import os
from dotenv import load_dotenv

try:
    import streamlit as st
except ImportError:
    st = None


load_dotenv()



def get_config(name):
    """
    优先读取 Streamlit Secrets
    其次读取环境变量
    """

    # Streamlit Cloud
    if st is not None:

        try:
            if name in st.secrets:
                return st.secrets[name]

        except Exception:
            pass


    # 本地环境
    return os.getenv(name)



# =========================
# 用户权限
# =========================


APP_ACCESS_CODE = get_config(
    "APP_ACCESS_CODE"
)


ADMIN_ACCESS_CODE = get_config(
    "ADMIN_ACCESS_CODE"
)



# =========================
# AI服务
# =========================


TAVILY_API_KEY = get_config(
    "TAVILY_API_KEY"
)


DEEPSEEK_API_KEY = get_config(
    "DEEPSEEK_API_KEY"
)


BOCHA_API_KEY = get_config(
    "BOCHA_API_KEY"
)



# =========================
# Webhook
# =========================


FEISHU_WEBHOOK_URL = get_config(
    "FEISHU_WEBHOOK_URL"
)


WECOM_WEBHOOK_URL = get_config(
    "WECOM_WEBHOOK_URL"
)



def check_user_config():

    """
    网站启动检查
    """

    missing=[]


    configs={

        "APP_ACCESS_CODE":
        APP_ACCESS_CODE,


        "ADMIN_ACCESS_CODE":
        ADMIN_ACCESS_CODE

    }


    for k,v in configs.items():

        if not v:
            missing.append(k)



    if missing:

        raise RuntimeError(
            "缺少用户权限配置:"
            +
            ",".join(missing)
        )



def check_ai_config():

    """
    AI任务运行检查
    """

    missing=[]


    configs={

        "TAVILY_API_KEY":
        TAVILY_API_KEY,


        "DEEPSEEK_API_KEY":
        DEEPSEEK_API_KEY,


        "BOCHA_API_KEY":
        BOCHA_API_KEY

    }


    for k,v in configs.items():

        if not v:
            missing.append(k)



    if missing:

        raise RuntimeError(
            "缺少AI服务配置:"
            +
            ",".join(missing)
        )