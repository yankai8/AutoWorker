# 🤖 AutoWorker

**一个能够自主规划的多步骤 AI Agent：输入调研目标 → 自动搜索 → 筛选相关文章 → 总结 → 生成可下载报告**

[![Streamlit App](https://img.shields.io/badge/Streamlit-Cloud-FF4B4B?style=flat&logo=streamlit)](https://autoworker-pd4noq928xbkq5esfipz2a.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat&logo=python)](https://www.python.org/)

---

## 🚀 在线演示

**https://autoworker-pd4noq928xbkq5esfipz2a.streamlit.app**

> 直接打开链接，输入调研目标（如"AI Agent 在医疗领域的应用"），AI 会自动完成全流程并生成报告。

---

## 📌 功能特性

- **LLM 自主决策**：输入目标后，Agent 自动规划搜索关键词，并根据搜索结果动态决定是否继续搜索
- **文章相关性评分**：每篇文章经过 LLM 评分（1-10 分），自动过滤低相关内容
- **多轮搜索循环**：支持最多 5 轮搜索，每轮最多补充新的关键词，动态扩展信息覆盖面
- **实时进度展示**：Web 界面实时显示每一步操作（规划→搜索→抓取→评分→总结→保存）
- **Markdown 报告**：生成结构化报告，含总论综述 + 逐篇文章摘要 + 来源链接
- **一键下载**：报告可直接下载为 .md 文件

---

## 🏗️ 项目架构

```
用户输入调研目标
       ↓
┌─────────────────────────────────────────┐
│  workflow.py（总指挥）                    │
│  ├── planner.py（LLM 大脑）              │
│  │   ├── plan_search() 规划搜索关键词     │
│  │   ├── should_continue_searching()     │
│  │   │     判断是否继续搜索               │
│  │   └── score_relevance() 评分相关性     │
│  ├── tools.py（双手）                    │
│  │   ├── web_search() 调 Tavily 搜索     │
│  │   ├── fetch_page() 抓网页正文          │
│  │   └── write_file() 写 Markdown 报告   │
│  └── state.py（口袋）                    │
│        共享数据：articles / report /      │
│        errors / report_path              │
└─────────────────────────────────────────┘
       ↓
生成 .md 报告 + 网页展示 + 下载
```

**核心技术点：**
- 生成器模式（yield）：workflow 每一步实时推送状态，Web 界面实时渲染
- 口袋设计：TypedDict 统一管理跨步骤数据流，无需全局变量
- 相关性过滤：LLM 评分 + 阈值过滤，保证报告质量
- 容错处理：单篇抓取失败不影响整体流程，错误记录进 `state["errors"]`

---

## 🛠️ 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | **Streamlit** | 纯 Python 写 Web 界面，50 行出交互页面 |
| LLM | **DeepSeek Chat API** | 规划、总结、评分（统一大脑） |
| 搜索 | **Tavily AI Search API** | AI 优化的搜索，返回 title/url/content |
| 解析 | **BeautifulSoup** | 网页正文提取，去除导航/广告/脚本 |
| 部署 | **Streamlit Community Cloud** | GitHub 触发自动部署 |
| 版本控制 | **Git + GitHub** | 代码管理 + 云端部署联动 |

---

## 💻 本地运行

### 1. 克隆项目
```bash
git clone https://github.com/yankai8/AutoWorker.git
cd AutoWorker
```

### 2. 安装依赖
```bash
pip install streamlit requests beautifulsoup4
```

### 3. 配置密钥
在项目根目录新建 `config.py`：
```python
TAVILY_API_KEY = "tvly-你的Tavily密钥"
DEEPSEEK_API_KEY = "sk-你的DeepSeek密钥"
```

> Tavily 注册：https://app.tavily.com （免费版无需绑卡）
> DeepSeek API：https://platform.deepseek.com

### 4. 运行
```bash
streamlit run app.py
```
浏览器自动打开 `http://localhost:8501`，输入调研目标即可使用。

---

## ☁️ 云端部署

项目已部署至 Streamlit Community Cloud，Secrets 配置：
```
TAVILY_API_KEY   = "tvly-..."
DEEPSEEK_API_KEY = "sk-..."
```

本地代码更新后，`git push` 会自动触发重部署（约 1 分钟生效）。

---

## 📂 项目结构

```
AutoWorker/
├── app.py              # Streamlit Web 界面（入口）
├── config_loader.py    # 密钥加载器（本地/云端双模式）
├── requirements.txt    # 依赖清单
├── .gitignore          # 排除密钥和缓存文件
├── README.md           # 本文件
└── src/
    ├── state.py        # 数据口袋（TypedDict）
    ├── tools.py        # 工具层（搜索/抓取/写文件）
    ├── planner.py      # LLM 大脑（规划/决策/评分）
    └── workflow.py     # 总指挥（主流程 + 生成器）
```

---

## 📖 项目演进

详见 [docs/CHANGELOG.md](docs/CHANGELOG.md)

```
v0.1 骨架      v0.2 工具    v0.3 工作流   v0.4 规划器   v0.5 总论   v0.6 决策Agent  v1.0 Web界面
   ↓            ↓            ↓             ↓            ↓            ↓              ↓
口袋定义     三个工具     串起来跑      LLM想搜什么   LLM写综述    LLM决定搜几轮   网页可演示
```

---

## 📝 简历项目描述（参考）

> **AutoWorker · 多步骤 AI Agent 调研报告生成系统**
> - 从零设计并实现一个能够自主规划的多步骤 AI Agent，输入目标后自动完成搜索→筛选→总结→生成报告的全流程
> - 技术栈：Python · Streamlit · DeepSeek LLM · Tavily Search API · BeautifulSoup
> - 核心亮点：
>   - LLM 主导的动态决策循环（规划关键词 → 判断是否继续搜索 → 补充关键词）
>   - 基于 LLM 评分的文章相关性过滤，保证报告内容质量
>   - 生成器模式（yield）实现实时进度推送，Web 界面逐行显示执行状态
>   - 手写实现状态管理与工具调用，深入理解 Agent 核心原理
> - 已云端部署：https://autoworker-pd4noq928xbkq5esfipz2a.streamlit.app
