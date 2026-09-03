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
        # 【核心改动】用 st.status 实时显示进度
        with st.status("🚀 正在调研，请稍候...", expanded=True) as status:
            result = None
            for step_name, message in run_workflow(goal):
                if step_name == "_RESULT_":
                    result = message  # ← 拿到 state
                else:
                    status.update(label=message)
                    st.write(f"**[{step_name}]** {message}")  # 每步写进状态栏日志

        # 显示报告
        if result and result.get("report"):
            st.success(f"✅ 完成！报告已保存")

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
