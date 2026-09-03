import sys
import os
from http.client import responses
from bs4 import BeautifulSoup

import requests

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config_loader import load_keys
TAVILY_API_KEY, DEEPSEEK_API_KEY = load_keys()

def web_search(query:str,max_results:int = 5) -> list:
    """搜索关键词，返回文章列表"""
    url = "https://api.tavily.com/search"
    headers = {"Content-Type":"application/json"}
    payload = {
        "api_key":TAVILY_API_KEY,
        "query":query,
        "max_results":max_results
    }
    response = requests.post(url,json=payload,headers=headers)
    data = response.json()
    return data["results"]

def fetch_page(url : str) -> str:
    """读取网页正文内容，返回纯文本"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text,"html.parser")
    # 删除无关内容，留下正文
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n",strip=True)
    return text

def write_file(content:str,file_path:str) -> str:
    """把内容写入指定文件，返回文件路径"""
    # 自动创建不存在的父目录
    parent_dir = os.path.dirname(file_path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    with open(file_path,"w",encoding="utf-8") as f:
        f.write(content)
    return file_path

if __name__ == "__main__":
    results = web_search("AI Agent 在医疗领域的应用",max_results=3)
    print(f"搜到{len(results)}条结果")
    for i,item in enumerate(results,1):
        print(f"\n--- 第{i}条 ---")
        print(f"标题: {item['title']}")
        print(f"链接: {item['url']}")
        print(f"摘要: {item['content'][:100]}")
    if results:
        first_url = results[0]["url"]
        print(f"\n=== 测试 fetch_page ===")
        print(f"抓取: {first_url}")
        text = fetch_page(first_url)
        print(f"抓取到 {len(text)} 个字符")
        print(f"开头 300 字:\n{text[:300]}")

        # 测试 write_file
        test_content = """# 测试报告
    这是用 write_file 写的第一行内容。
    ## 小标题
    - 项目 1
    - 项目 2
    """
        path = write_file(test_content, "../output/test_report.md")
        print(f"\n=== 测试 write_file ===")
        print(f"文件已保存到：{path}")
        # 读回来验证内容真的写进去了
        with open(path, "r", encoding="utf-8") as f:
            print(f"读出来的内容：\n{f.read()}")
