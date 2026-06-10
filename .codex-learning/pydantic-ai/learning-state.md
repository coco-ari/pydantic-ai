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

- 阶段：`4. 工具与依赖注入`
- 当前主题：先补 `.tool_plain` demo 所需 Python 语法，再写并运行最小工具 demo。
- 下一步：学习函数定义、类型注解、装饰器和 `dict` 最小语法，然后创建 `.tool_plain` demo。

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
| 2026-06-10 | `_agent_graph.py` 三个核心节点 | `pydantic_ai_slim/pydantic_ai/_agent_graph.py`, `pydantic_ai_slim/pydantic_ai/agent/abstract.py`, `pydantic_ai_slim/pydantic_ai/run.py` | 用户能说明 `CallToolsNode` 会根据模型响应决定执行工具后回到 `ModelRequestNode`，或直接返回 `End` | 阅读 `messages.py` 中请求、响应和 parts |
| 2026-06-10 | `ModelRequest` 与 `ModelResponse` | `pydantic_ai_slim/pydantic_ai/messages.py` | 用户能说明 `ModelRequest` 是 agent 发给 LLM，`ModelResponse` 是 LLM 发给 agent | 继续阅读常见 message parts |
| 2026-06-10 | message parts | `pydantic_ai_slim/pydantic_ai/messages.py`, `pydantic_ai_slim/pydantic_ai/_agent_graph.py` | 用户能说明模型返回 `ToolCallPart` 时会进入 `CallToolsNode` 执行本地工具 | 阅读 `models/test.py`，用测试模型串起完整运行 |
| 2026-06-10 | 核心 node 的入参与返回 | `pydantic_ai_slim/pydantic_ai/_agent_graph.py`, `pydantic_ai_slim/pydantic_ai/models/test.py` | 用户能总结 `UserPromptNode` 产出 `ModelRequestNode`，`ModelRequestNode` 调 model 得到 `ModelResponse` 并交给 `CallToolsNode`，`CallToolsNode` 根据响应返回 `End` 或新的 `ModelRequestNode` | 画出阶段 3 的 5 步总流程 |
| 2026-06-10 | `TestModel` 与 graph node 区分 | `pydantic_ai_slim/pydantic_ai/models/test.py`, `pydantic_ai_slim/pydantic_ai/_agent_graph.py` | 用户能说明 `TestModel` 不是 graph node，而是被 `ModelRequestNode` 调用的模型实现 | 画出阶段 3 的 5 步总流程 |
| 2026-06-10 | 普通 function tool 消息链条 | `pydantic_ai_slim/pydantic_ai/_agent_graph.py`, `pydantic_ai_slim/pydantic_ai/messages.py` | 用户能说明 `ToolCallPart` 是大模型发给 agent，`ToolReturnPart` 是 agent 发回大模型 | 进入阶段 4：工具与依赖注入 |
| 2026-06-10 | `.tool_plain` 注册工具 | `pydantic_ai_slim/pydantic_ai/agent/__init__.py`, `pydantic_ai_slim/pydantic_ai/toolsets/function.py`, `pydantic_ai_slim/pydantic_ai/tools.py` | 用户能说明 `.tool_plain` 只是注册工具，不会执行工具函数 | 理解工具如何变成 `ToolDefinition` 并发送给模型 |

## 新会话启动协议

1. 先读取本文件，确认当前阶段和下一步。
2. 读取 `python-ability-table.md`，确认用户已掌握的 Python 知识。
3. 读取 `roadmap.md`，选择当前阶段的下一个任务。
4. 讲解前列出本节需要的 Python 前置知识。
5. 对用户未掌握的知识先做最小补课，再进入源码。
6. 用户完成练习或确认理解后，更新学习状态和能力表。
