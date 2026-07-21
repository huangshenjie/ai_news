import logging
import os
from datetime import datetime


# 创建日志目录
LOG_DIR = "logs"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


# 日志文件名称
log_file = os.path.join(
    LOG_DIR,
    f"ai_news_{datetime.now().strftime('%Y%m%d')}.log"
)


# 创建logger
logger = logging.getLogger("ai_news")

logger.setLevel(logging.INFO)


# 防止重复添加handler
if not logger.handlers:

    # 文件输出
    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8"
    )

    # 控制台输出
    console_handler = logging.StreamHandler()


    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )


    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)


    logger.addHandler(file_handler)
    logger.addHandler(console_handler)