import os
from dotenv import load_dotenv
from pydantic import StrictStr

load_dotenv()

ALI_LLM_KEY = StrictStr(os.getenv("ALI_LLM_KEY"))
ALI_LLM_BASE_URL = StrictStr(os.getenv("ALI_LLM_BASE_URL"))

JU_HE_MCP = StrictStr(os.getenv("JU_HE_MCP"))

ALI_LLM_DICT = {
    "qwen3Max": "qwen3-max",
    "deepseekV32": "deepseek-v3.2",
    "qwen3VlFlash": "qwen3-vl-flash"
}

MCP_DICT = {
    "juhe": JU_HE_MCP
}

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "xiaofeng71.")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "mooda")
MYSQL_CHARSET = os.getenv("MYSQL_CHARSET", "utf8mb4")

WECHAT_APP_ID = os.getenv("WECHAT_APP_ID", "")
WECHAT_APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")
WECHAT_REDIRECT_URI = os.getenv("WECHAT_REDIRECT_URI", "http://localhost:8003/api/v1/auth/wechat/callback")

