# AutoWorker 项目发展历程

> 从零手写的工作流自动化 Agent，记录每个版本的演进过程。
> 目标：用户输入调研目标 → 自动规划 → 搜索 → 抓取 → 总结 → 生成报告

---

## 版本演进路线图

```
v0.1 骨架    → v0.2 工具层  → v0.3 工作流  → v0.4 规划器  → v0.5 总论  → v0.6 决策 Agent → v1.0 Web 界面
 ✅            ✅             ✅             ✅            ✅            ⬜ 开发中          ⬜
```

---

## v0.1 骨架（state.py）— 口袋定义

**时间：2026-09-03 上午**

**做了什么：**
- 用 TypedDict 定义 WorkflowState（口袋）：goal / current_step / articles / report / errors / should_continue / report_path
- 写 create_initial_state(goal) 工厂函数返回初始口袋
- 学习"为什么需要口袋"：每个步骤要往里放东西、拿东西，单一变量装不下

**踩的坑：**
- `__name__ == "main"` 少了双下划线 → if 块永不执行（经典入门 bug）

**核心概念：**
- 口袋 = 所有步骤共享的数据容器
- 流程结束时口袋里装着全部成果（文章、报告、路径、错误记录）

**文件：** src/state.py

---

## v0.2 工具层（tools.py）— 三个工具

**时间：2026-09-03 上午**

**做了什么：**
- 工具① web_search：调 Tavily API（POST + api_key），返回文章列表
- 工具② fetch_page：requests.get + BeautifulSoup，清理 script/style/nav/header/footer/aside，提取正文
- 工具③ write_file：with open + encoding="utf-8"，返回文件路径

**踩的坑：**
- 跨目录 import：config.py 在根目录，tools.py 在 src/，需要 sys.path.append 加父目录
- fetch_page 抓到 1285 字符但开头有导航垃圾（div class="nav" 不是 nav 标签），暂不优化
- 相对路径：src/ 下跑要用 ../output/ 才能写到根目录 output/
- Tavily key 曾在聊天中完整发出（安全问题，已提醒换 key）

**核心技术点：**
- POST vs GET（寄信 vs 借书）
- User-Agent 伪装（防 403）
- BeautifulSoup html.parser + tag.decompose()
- with 上下文管理（自动关文件）
- encoding="utf-8" 防中文乱码

**文件：** src/tools.py, config.py

---

## v0.3 工作流（workflow.py）— 串起来自动跑

**时间：2026-09-03 中午**

**做了什么：**
- summarize_with_llm()：调 DeepSeek，temperature=0.3，剥洋葱取 choices[0].message.content
- run_workflow()：建口袋 → 搜 1 次（3 篇）→ 循环（抓正文 → 截 3000 字 → LLM 总结 → 收摘要）→ join 拼报告 → write_file 写 .md
- 全流程跑通：输入"AI Agent在医疗领域的应用" → 生成 .md 报告

**踩的坑：**
- Scribd 国外网站连接超时 → 程序崩溃 → 引入 try-except（单篇失败跳过，记入 state["errors"]）
- 踩坑教训：真实世界的网络请求随时可能失败，必须有容错
- 代码中 `"\n."` 手误写错（应该是 `"\n"`），已修正

**核心技术点：**
- 切片 full_text[:3000] 控制 LLM 输入长度
- "\n".join() 把列表粘成大字符串
- try-except 异常隔离（单篇失败不拖垮全局）
- 口袋设计哲学：发现缺字段就加（report_path 就是这时加的）

**设计决策：**
- summarize 不单独做工具：总结是"思考"不是"动作"，由 workflow 直接调 LLM
- 工具只做"LLM 做不到的事"（搜索、抓取、写文件）

**文件：** src/workflow.py

---

## v0.4 规划器（planner.py）— LLM 开始"想"

**时间：2026-09-03 下午**

**做了什么：**
- plan_search()：调 DeepSeek，让 LLM 从 3 个不同角度设计搜索关键词
- workflow.py 改造：goal → planner 出 3 个关键词 → 每个关键词搜 2 篇 → 共 6 篇文章
- all_articles.extend(results) 把多次搜索结果合并

**核心变化：**
```
旧版：goal → 直接搜 1 次（3 篇）       ← 不思考，蛮干
新版：goal → LLM 规划 3 个角度 → 搜 3 次（6 篇）  ← 先想再干
```

**核心技术点：**
- prompt 约束格式："只输出关键词本身，每行一个，不要编号，不要解释"
- content.splitlines() 把 LLM 多行输出拆成列表
- extend vs append（倒进列表 vs 加一个元素）
- len() 调试打印（知道搜了几个词、几篇文章）

**意义：**
- 这一步让 AutoWorker 从"脚本"开始变成"Agent"——LLM 第一次参与决策
- 但只管了"搜什么"，后面的步骤还是代码写死 → 半个规划

**文件：** src/planner.py

---

## v0.5 总论段 — 报告可读性升级

**时间：2026-09-03 下午**

**做了什么：**
- 工作流⑤拼报告之前，新增一步：把 6 篇摘要拼成一大段 → 喂给 DeepSeek → 综合归纳成 200~300 字的综述
- 报告结构从"6 篇摘要平铺"变成"📋 总论 + 分隔线 + 逐篇详情"
- prompt 区分：summarize 是"压缩一篇"，总论是"综合多篇"

**核心变化：**
```
旧报告：                    新报告：
# 标题                      # 标题
## 文章1                    ## 📋 总论      ← 新增
摘要...                     （一段综述）     ← 新增
## 文章2                    ---
摘要...                     ## 文章1
                            摘要...
                            ## 文章2
                            摘要...
```

**核心技术点：**
- 同一个 DeepSeek API，不同 prompt 干不同的事（压缩 vs 归纳）
- all_summaries_text[:4000] 截断控制输入长度
- 报告分层：总论（读全局）→ 逐篇（看细节）

**文件：** src/workflow.py（修改）

---

## v0.6 决策 Agent — 开发中

**计划：让 LLM 在更多环节做决策**

| 能力 | v0.5 现状 | v0.6 目标 |
|------|----------|----------|
| 搜什么 | ✅ LLM 决定 | ✅ |
| 搜几次 | ❌ 写死 3 次 | ✅ LLM 判断 |
| 搜完够不够 | ❌ | ✅ "不够再搜一轮" |
| 哪篇该抓 | ❌ 全抓 | ✅ LLM 筛选 |
| 报告结构 | ❌ 写死格式 | ✅ LLM 决定 |

**核心升级：ReAct 循环**
- Thought → Action → Observation 循环
- LLM 在每一步都能思考"下一步干嘛"
- 这就是昨天用 LangChain create_react_agent 一行搞定的东西，今天手写实现

---

## v1.0 Web 界面 + 部署 — 未来

**计划：**
- Streamlit 包一层 Web 界面（输入框 + 进度条 + 报告展示）
- 部署到 Streamlit Community Cloud（免费）
- 简历可直接放链接：https://xxx.streamlit.app

---

## 版本对比总览

| 版本 | 搜索 | 文章数 | 规划 | 报告 | Agent 程度 |
|------|------|--------|------|------|-----------|
| v0.3 | 1 个词 | 3 篇 | ❌ | 平铺摘要 | 脚本 |
| v0.4 | LLM 出 3 词 | 6 篇 | ✅ 搜什么 | 平铺摘要 | 脚本+一点Agent |
| v0.5 | LLM 出 3 词 | 6 篇 | ✅ 搜什么 | 总论+详情 | 脚本+一点Agent |
| v0.6 | LLM 动态决定 | 动态 | ✅ 全程决策 | LLM 决定结构 | 真Agent |
| v1.0 | 同 v0.6 | 同 v0.6 | 同 v0.6 | 同 v0.6 | Web 可演示 |

---

## 技术栈对照表（与昨天 6 课的关系）

| 技术 | 昨天（agent_complete.py） | 今天（AutoWorker） |
|------|--------------------------|-------------------|
| 工具调用 | ✅ Function Calling | ✅ 工具本质相同（手动调） |
| ReAct 循环 | ✅ create_react_agent | ❌ v0.6 目标 |
| LangChain 框架 | ✅ | ❌ 故意手写 |
| LangGraph 状态 | ✅ | ✅ 手写 TypedDict 口袋 |
| RAG | ✅ | ❌ 场景不匹配 |
| 记忆 | ✅ MemorySaver | ❌ 单次任务不需要 |
| 流式输出 | ✅ agent.stream | ❌ 未来可加 |

**两个项目互补：** agent_complete.py = 框架全家桶演示；AutoWorker = 从零手写理解原理
