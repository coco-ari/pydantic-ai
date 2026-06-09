# Pydantic AI 学习状态

> 新会话开始学习时，agent 应先读取本文件、`python-ability-table.md` 和 `roadmap.md`。

## 学习目标

- 从零理解 Pydantic AI 的文档、包结构和核心 `Agent` 运行流程。
- 在读源码时同步补齐 Python 基础。
- 用可持续更新的能力表记录已经掌握、正在学习和还没学的 Python 知识点。

## 学习者背景

- 有 5 年 Java 开发经验。
- Python 基础较弱，但可以使用 Java 中的类、对象、方法、字段、线程/异步概念做类比。
- 讲 Python 源码时优先使用 Java 类比，但不要假设已经掌握 Python 语法细节。

## 当前阶段

- 阶段：`0. 建立地图 + 最小示例`
- 当前主题：理解 `iter()` 创建 `AgentRun`，`run()` 驱动 `AgentRun`
- 下一步：进入 `_agent_graph.py`，认识 `UserPromptNode`、`ModelRequestNode`、`CallToolsNode` 三个核心节点。

## 已读核心文件

- `AGENTS.md`
- `agent_docs/index.md`
- `docs/index.md`
- `docs/agent.md`
- `pydantic_ai_slim/pydantic_ai/AGENTS.md`

## 学习记录

| 日期 | 主题 | 文件 | 结果 | 下一步 |
| --- | --- | --- | --- | --- |
| 2026-06-09 | 学习方案设计 | `docs/index.md`, `docs/agent.md`, `pydantic_ai_slim/pydantic_ai/` | 建立学习状态文件、能力表和路线图 | 讲解 docs、包结构、核心 `Agent` 运行流程 |
| 2026-06-09 | 最小 API 示例 | `.codex-learning/pydantic-ai/examples/hello_custom_api.py`, `docs/models/openai.md`, `pydantic_ai_slim/pydantic_ai/providers/openai.py` | 创建使用环境变量读取 API key 和 `base_url` 的 OpenAI-compatible 示例 | 设置环境变量并运行示例 |
| 2026-06-09 | Model 和 Provider 职责 | `.codex-learning/pydantic-ai/examples/hello_custom_api.py`, `pydantic_ai_slim/pydantic_ai/models/openai.py`, `pydantic_ai_slim/pydantic_ai/providers/openai.py` | 用户理解 `OpenAIProvider` 和 `OpenAIChatModel` 是类，用来创建 provider/model 对象；补充职责：provider 管连接，model 管协议翻译 | 阅读 `Agent(model)` 初始化源码 |
| 2026-06-09 | `Agent.__init__` 保存 model | `pydantic_ai_slim/pydantic_ai/agent/__init__.py` | 用户能说明 `self._model` 是 agent 内部模型变量，`models.infer_model(model)` 用来解析模型参数 | 阅读 `run_sync()` 到 `run()` 的入口 |
| 2026-06-09 | `run_sync()` 与事件循环 | `pydantic_ai_slim/pydantic_ai/agent/abstract.py`, `pydantic_ai_slim/pydantic_ai/_utils.py` | 用户理解 `_utils` 是导入模块，`get_event_loop()` 返回 event loop 对象，event loop 可以执行异步 agent 任务；暂不要求理解事件循环底层实现 | 阅读 `run()` 如何创建 Agent graph |
| 2026-06-09 | `run()` 驱动 graph node | `pydantic_ai_slim/pydantic_ai/agent/abstract.py` | 用户能说明 node 是任务节点，`while` 循环执行直到 `End`，`agent_run.next(node)` 返回下一个任务节点 | 阅读 `Agent.iter()` 创建 `AgentRun` |
| 2026-06-09 | `iter()` 与 `run()` 职责 | `pydantic_ai_slim/pydantic_ai/agent/__init__.py`, `pydantic_ai_slim/pydantic_ai/run.py` | 用户理解 `iter()` 负责创建运行，`run()` 负责执行运行；校正为 `iter()` 创建 `AgentRun` 而不是创建 `Agent` | 阅读 `_agent_graph.py` 核心节点 |

## 新会话启动协议

1. 先读取本文件，确认当前阶段和下一步。
2. 读取 `python-ability-table.md`，确认用户已掌握的 Python 知识。
3. 读取 `roadmap.md`，选择当前阶段的下一个任务。
4. 讲解前列出本节需要的 Python 前置知识。
5. 对用户未掌握的知识先做最小补课，再进入源码。
6. 用户完成练习或确认理解后，更新学习状态和能力表。
