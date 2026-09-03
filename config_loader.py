"""加载 API 密钥

本地开发：从 config.py 读取（你的真实 key 在这里，不进 GitHub）
云端部署：从 Streamlit Secrets 读取（在云端后台配置）

这样就不用把密钥写进代码仓库，避免泄露。
"""


def load_keys():
    """返回 (TAVILY_API_KEY, DEEPSEEK_API_KEY)"""
    try:
        # 本地：config.py 存在，直接用
        from config import TAVILY_API_KEY, DEEPSEEK_API_KEY
        return TAVILY_API_KEY, DEEPSEEK_API_KEY
    except ImportError:
        # 云端：config.py 不在，从 Streamlit Secrets 读
        import streamlit as st
        return st.secrets["TAVILY_API_KEY"], st.secrets["DEEPSEEK_API_KEY"]
