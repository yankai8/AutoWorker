import sys
import os
import requests
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config_loader import load_keys
TAVILY_API_KEY, DEEPSEEK_API_KEY = load_keys()

def plan_search(goal:str,num_keywords:int = 3) -> list:
    """让LLM根据调研目标,规划出num_keywords个不同角度的关键词"""
    url = url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    prompt = f"""你是调研规划专家。用户想调研这个主题:
    {goal}

    请从 {num_keywords} 个不同角度,各设计 1 个搜索关键词(可以中文或英文),
    让这些关键词搜出来的内容能覆盖主题的不同方面。

    要求:
    - 只输出关键词本身,每行一个,不要编号,不要解释
    - 严格只输出 {num_keywords} 行"""

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    content = data["choices"][0]["message"]["content"]

    # 把 LLM 输出的多行文字拆成列表
    keywords = []
    for line in content.splitlines():
        line = line.strip()
        if line:
            keywords.append(line)
    return keywords

def should_continue_searching(goal,articles,max_articles = 10):
    """让llm判断:搜到的文章够不够看,不够就给出关键词"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    # 将已有的文章拿给llm看
    article_list = ""
    for a in articles:
        article_list += f" - {a['title']}\n"
    prompt = f"""【硬性规则】如果文章数量 ≥ {max_articles} 篇，第一行必须直接输出"是"，不要任何解释、犹豫、补充。

【软性参考】仅当文章数量 < {max_articles} 篇时，才考虑这些文章是否覆盖了主题的3个不同方面（如技术、应用、挑战）。如已够，回答"是"；如还不够，给出补充关键词。

用户调研主题：{goal}

已有文章（{len(articles)} 篇）：{article_list}

请按以下格式输出（两行）：
第一行：是 或 否
第二行：补充关键词（如果第一行是"是"，第二行写"无"）"""

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    content = data["choices"][0]["message"]["content"]

    # 解析 LLM 的两行输出
    lines = content.strip().splitlines()
    enough = "是" in lines[0] if lines else True

    # 取第二行,拆分成多个关键词
    raw_keyword = lines[1].strip() if len(lines) > 1 else "无"
    if raw_keyword == "无" or not raw_keyword:
        next_keywords = []
    else:
        # 用多种分隔符拆分
        import re
        parts = re.split(r"[、,,\s]+", raw_keyword)
        next_keywords = [p.strip() for p in parts if p.strip() and len(p.strip()) >= 2]

    return enough, next_keywords

def score_relevance(goal:str,article:dict,summary:str) -> int:
    """让 LLM 评估文章与调研目标的相关度,返回 1-10 分"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    prompt = f"""调研目标:{goal}

    文章标题:{article['title']}
    文章摘要:{summary}

    请评估这篇文章与调研目标的相关度(1-10 分):
    - 9-10 分:核心相关,直接覆盖主题
    - 6-8 分:部分相关,能给主题提供有用信息
    - 3-5 分:边缘相关,仅有少量联系
    - 1-2 分:基本无关

    只输出一个数字(1-10 之间),不要其他任何文字或标点。"""

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,  # 评分要稳定,温度低一点
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    content = data["choices"][0]["message"]["content"].strip()

    # 提取数字(防御 LLM 输出多余文字)
    import re
    match = re.search(r'\d+', content)
    if match:
        score = int(match.group())
        return min(max(score, 1), 10)  # 限制在 1-10
    return 5  # 解析失败默认 5 分

if __name__ == "__main__":

    # 测试plan_search
    kws = plan_search("AI Agent在医疗领域的应用")
    print(f"规划出的关键词:{kws}")

    # 测试 score_relevance
    test_cases = [
        {
            "goal": "AI Agent在医疗领域的应用",
            "article": {"title": "医疗AI Agent元年:从概念到落地"},
            "summary": "本文介绍医疗AI Agent如何重构医疗服务全流程,包括诊断、随访、药物研发等场景。",
            "expected_range": "应该 8~10 分",
        },
        {
            "goal": "AI Agent在医疗领域的应用",
            "article": {"title": "什么是应用程序?"},
            "summary": "应用程序是运行在设备上的小程序,提供额外功能,如通信、娱乐、交通信息等。",
            "expected_range": "应该 1~2 分",
        },
        {
            "goal": "AI Agent在医疗领域的应用",
            "article": {"title": "司法局权威指引:企业出海合规必看!"},
            "summary": "深圳市司法局发布《进出口合规指南》,助力企业应对出海合规风险。",
            "expected_range": "应该 1~3 分",
        },
    ]

    print("\n=== 测试 score_relevance ===")
    for tc in test_cases:
        score = score_relevance(tc["goal"], tc["article"], tc["summary"])
        print(f"\n文章:{tc['article']['title']}")
        print(f"评分:{score} 分 ({tc['expected_range']})")

    # 测试 should_continue_searching(模拟已有文章)
    fake_articles = [
        {"title": "AI Agent 医疗诊断应用综述"},
        {"title": "医疗大模型落地案例分析"},
    ]
    enough, next_kw = should_continue_searching("AI Agent在医疗领域的应用", fake_articles)
    print(f"够了吗:{enough}")
    print(f"补充关键词:{next_kw}")