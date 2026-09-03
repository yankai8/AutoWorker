import streamlit as st
import sys
import os

# 把项目根目录加到路径（让 from src.workflow import 能找到）
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.workflow import run_workflow  # 导入核心工作流函数

# 页面配置
st.set_page_config(
    page_title="AutoWorker",
    page_icon="🤖",
    layout="wide"
)

# 主标题
st.title("🤖 AutoWorker - 调研报告自动生成")
st.markdown("**输入调研目标 → AI Agent 自动规划 → 搜索 → 总结 → 生成报告**")

# 输入框
goal = st.text_input(
    "🎯 调研目标",
    placeholder="例如：AI Agent在医疗领域的应用"
)

# 启动按钮
if st.button("🚀 开始调研", type="primary"):
    if not goal.strip():
        st.error("❌ 请输入调研目标")
    else:
        # ── 进度日志区（实时累加显示，不被覆盖）─────────────────
        log_container = st.container()
        log_placeholder = log_container.empty()
        log_lines = []

        def append_log(step_name, message):
            """追加一行进度日志"""
            tag_map = {
                "规划": "🧠", "搜索": "🔍", "决策": "🤔",
                "处理": "📖", "评分": "📊", "错误": "⚠️",
                "总论": "✍️", "保存": "💾", "完成": "✅"
            }
            icon = tag_map.get(step_name, "▶️")
            log_lines.append(f"**{icon} [{step_name}]** {message}")
            log_placeholder.markdown("\n\n".join(log_lines))

        # ── spinner 单独跑，表示程序在运行 ─────────────────────
        with st.spinner("🚀 AI Agent 工作中，请稍候..."):
            result = None
            for step_name, message in run_workflow(goal):
                if step_name == "_RESULT_":
                    result = message  # ← 拿到最终 state
                else:
                    append_log(step_name, message)

        # ── 显示报告 ─────────────────────────────────────────
        if result and result.get("report"):
            st.success(f"✅ 完成！报告已保存至 {os.path.basename(result.get('report_path', ''))}")

            # 在网页上展示报告
            st.markdown("---")
            st.subheader("📄 调研报告")
            st.markdown(result["report"])

            # 下载按钮
            st.download_button(
                label="📥 下载报告",
                data=result["report"],
                file_name=os.path.basename(result["report_path"]),
                mime="text/markdown"
            )
        else:
            st.error("❌ 运行出错，请检查终端日志")

# 页脚说明
st.markdown("---")
st.caption("💡 AutoWorker v1.0 | 基于 LangChain 概念手写实现")
