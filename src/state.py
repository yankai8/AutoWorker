"""WorkflowState  --  工作流的“口袋”定义"""

from typing import TypedDict

class WorkflowState(TypedDict):
    """工作流的状态口袋，所有步骤共享"""
    goal : str  #用户的任务是什么
    current_step : int  # 现在做到第几步了
    articles : list  # 搜索到的文章列表
    report : str # 最终报告的内容
    errors : list  #执行过程中的错误
    should_continue : bool # 是否进行下一步
    report_path : str # 报告文件存放位置

def create_initial_state(goal : str) -> WorkflowState:
    """
    创建一个新口袋（初始状态）
    goal：用户给的新任务
    """
    return WorkflowState(
        goal = goal,
        current_step = 0,
        articles=[],
        report="",
        errors=[],
        should_continue=True,
        report_path="",
    )

if __name__ == "__main__":
    pocket = create_initial_state("帮我调研AI agent在医疗领域的应用")
    print("口袋创建成功")
    print(f"goal:{pocket['goal']}")
