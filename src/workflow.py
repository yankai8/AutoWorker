import sys
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config_loader import load_keys
TAVILY_API_KEY, DEEPSEEK_API_KEY = load_keys()
from src.state import create_initial_state
from src.tools import web_search, fetch_page, write_file
from src.planner import plan_search, should_continue_searching, score_relevance

def summarize_with_llm(text: str, max_length: int = 200) -> str:
    """调用 DeepSeek 把长文压缩成摘要"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    prompt = f"""请把以下文本压缩成不超过 {max_length} 字的中文摘要，保留核心观点：
{text}
摘要："""
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    return data["choices"][0]["message"]["content"]

def run_workflow(goal: str):
    """
    主工作流：规划 → 搜索+决策循环 → 并发处理文章 → 总论 → 写报告
    """
    state = create_initial_state(goal)

    # ① 规划搜索关键词
    keywords = plan_search(goal)
    yield ("规划", f"规划出 {len(keywords)} 个关键词：{keywords}")

    # ② 搜索 + LLM 决策循环
    all_articles = []
    max_rounds = 5
    next_keywords = None

    for round_num in range(max_rounds):
        if round_num == 0:
            search_keywords = keywords
        else:
            if not next_keywords:
                yield ("决策", "LLM 没给补充关键词，搜索完成")
                break
            search_keywords = next_keywords

        for kw in search_keywords:
            yield ("搜索", f"第 {round_num + 1} 轮搜索：{kw}")
            results = web_search(kw, max_results=2)
            all_articles.extend(results)

        # 按 URL 去重
        seen_urls = set()
        unique_articles = []
        for a in all_articles:
            if a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                unique_articles.append(a)
        all_articles = unique_articles
        state["articles"] = all_articles
        yield ("搜索", f"已搜到 {len(all_articles)} 篇文章")

        # 问 LLM：够不够？
        enough, next_keywords = should_continue_searching(goal, all_articles, max_articles=10)
        if enough:
            yield ("决策", "LLM 判断：够了，搜索完成")
            break
        else:
            if not next_keywords:
                yield ("决策", "LLM 没给补充关键词，搜索完成")
                break
            yield ("决策", f"LLM 判断：不够，补充搜索 {len(next_keywords)} 个关键词：{next_keywords}")
            search_keywords = next_keywords

    # ════════════════════ ③ 并发处理（核心改动） ════════════════════

    def process_article(article: dict) -> dict:
        """处理单篇文章：抓取 + 总结 + 评分，结果打成一个字典"""
        full_text = fetch_page(article["url"])
        summary = summarize_with_llm(full_text[:3000])
        score = score_relevance(goal, article, summary)
        return {
            "title": article["title"],
            "url": article["url"],
            "summary": summary,
            "score": score,
        }

    yield ("处理", f"开始并发处理 {len(state['articles'])} 篇文章（最多 5 个同时）...")

    summaries = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(process_article, a): a for a in state["articles"]}

        for future in as_completed(futures):
            article = futures[future]
            try:
                result = future.result()
                yield ("评分", f"相关度 {result['score']} 分：{result['title']}")
                if result["score"] < 6:
                    yield ("评分", f"跳过低相关度文章（{result['score']} 分）")
                    state["errors"].append(f"低相关度跳过: {result['title']}")
                else:
                    summaries.append(result)
            except Exception as e:
                yield ("错误", f"处理失败：{article['title']}，已跳过")
                state["errors"].append(f"{article['title']}: {e}")

    # ════════════════════════════════════════════════════════════════

    # ④ 生成总论
    yield ("总论", "正在生成总论...")
    all_summaries_text = ""
    for s in summaries:
        all_summaries_text += f"标题：{s['title']}\n摘要：{s['summary']}\n\n"

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    overview_prompt = f"""以下是关于"{goal}"的多篇文章摘要。请综合归纳成一段综述（200~300字），不要分点，写成一整段：

{all_summaries_text[:4000]}"""
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": overview_prompt}],
        "temperature": 0.3,
    }
    resp = requests.post(url, json=payload, headers=headers)
    overview = resp.json()["choices"][0]["message"]["content"]

    # ⑤ 拼报告
    report_lines = [f"# 调研报告：{goal}", ""]
    report_lines.append("## 总论")
    report_lines.append("")
    report_lines.append(overview)
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    for s in summaries:
        report_lines.append(f"## {s['title']}")
        report_lines.append(f"来源：{s['url']}")
        report_lines.append("")
        report_lines.append(s["summary"])
        report_lines.append("")

    state["report"] = "\n".join(report_lines)

    # 写文件（用绝对路径）
    src_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(src_dir)
    output_dir = os.path.join(project_root, "output")
    file_name = goal[:20].replace(" ", "_") + ".md"
    abs_file_path = os.path.join(output_dir, file_name)

    yield ("保存", f"报告将保存到：{file_name}")
    state["report_path"] = write_file(state["report"], abs_file_path)
    yield ("完成", f"[OK] 完成！共处理 {len(summaries)} 篇文章")

    yield ("_RESULT_", state)
    return
