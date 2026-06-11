# Pydantic AI 学习状态

> 新会话开始学习时，agent 应先读取本文件、`python-ability-table.md` 和 `roadmap.md`。

## 学习目标

- 先稳扎稳打补齐 Python 语法，再用 Pydantic AI 小 demo 连接真实框架行为。
- 源码阅读只作为验证材料，不作为默认学习入口。
- 用可持续更新的能力表记录已经掌握、正在学习和还没学的 Python 知识点。

## 学习者背景

- 有 5 年 Java 开发经验。
- Python 基础较弱，但可以使用 Java 中的类、对象、方法、字段、线程/异步概念做类比。
- 讲解时优先使用 Java 类比，但不要假设已经掌握 Python 语法细节。

## 当前阶段

- 阶段：`4. 工具与依赖注入`
- 当前主题：已完成 `deps`/`ctx` 最小 demo，理解本地依赖如何进入工具。
- 下一步：用真实 Pydantic AI 最小 demo 验证 `run_sync(..., deps=...)` 到工具里的 `ctx.deps.unit`。

## 已读核心文件

- `AGENTS.md`
- `agent_docs/index.md`
- `docs/index.md`
- `docs/agent.md`
- `pydantic_ai_slim/pydantic_ai/AGENTS.md`

## 学习记录

> 历史记录只作为已学证据。表格里的旧“下一步”来自旧教学方式，不再驱动后续学习；以后以下方“新会话启动协议”为准。

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
| 2026-06-10 | `.tool_plain` 最小 demo | `.codex-learning/pydantic-ai/examples/tool_plain_demo.py`, `pydantic_ai_slim/pydantic_ai/models/test.py`, `pydantic_ai_slim/pydantic_ai/agent/__init__.py` | 已创建并运行 demo，输出 `{"weather_lookup":"a: sunny"}`；用户能总结 `.tool_plain` 注册工具，`agent.run_sync()` 启动运行，`TestModel` 生成参数 `"a"` 后由 agent 调用 `get_weather`；并能判断模型返回 `ToolCallPart` 时使用工具说明书里的名字 `weather_lookup` | 学习 `deps` 和 `ctx` |
| 2026-06-10 | `deps` 与 `ctx` 最小 demo | `.codex-learning/pydantic-ai/examples/tool_deps_demo.py` | 已创建并运行 demo，输出 `{"get_weather":"a: sunny, unit=C"}`；用户能说明 `deps` 是 agent 本地运行时传入，需要 `ctx.deps` 时使用 `.tool` | 读最小源码链路：`run_sync(..., deps=...)` -> `RunContext.deps` -> 工具执行 |
| 2026-06-11 | 对象属性访问 `obj.attr` | 内联语法示例 | 用户能判断 `book.title` 读到 `"Python Basics"` | 下一步学习 `dataclass` 创建保存数据的对象 |
| 2026-06-11 | `dataclass` 保存数据对象 | 内联语法示例 | 用户能把 `@dataclass` 类比为 Lombok `@Data`，并判断 `book.price` 打印 `99` | 下一步学习关键字参数 `name=value` |
| 2026-06-11 | 关键字参数 `name=value` | 内联语法示例 | 用户能判断 `unit="C"` 是把 `"C"` 传给 `unit` 参数 | 下一步学习类型注解 `name: str` |
| 2026-06-11 | 参数类型注解 `name: str` | 内联语法示例 | 用户能校正为 `unit: str` 表示 `unit` 的建议/声明类型是 `str`，不是运行时默认强制 | 下一步学习返回类型注解 `-> str` |
| 2026-06-11 | 返回类型注解 `-> str` | 内联语法示例 | 用户能说明 `-> int` 表示函数返回值建议是 `int` | 下一步学习泛型外观 `Box[Thing]` |
| 2026-06-11 | 泛型外观 `Box[Thing]` | 内联语法示例 | 用户能说明 `ctx: RunContext[WeatherDeps]` 表示 `ctx` 是 `RunContext`，里面关联/装着 `WeatherDeps` 类型的数据 | 下一步学习连续属性访问 `a.b.c` |
| 2026-06-11 | 连续属性访问 `a.b.c` | 内联语法示例 | 用户能判断 `ctx.deps.unit` 会读到 `"C"` | 下一步连接 `deps=...` 到 `ctx.deps.unit` |
| 2026-06-11 | 纯 Python 模拟 `deps` 到 `ctx.deps.unit` | 内联语法示例 | 用户能判断把 `WeatherDeps(unit="C")` 放到 `ctx.deps` 后，`ctx.deps.unit` 会读到 `"C"` | 下一步用真实 Pydantic AI demo 验证 |

## 新会话启动协议

1. 先读取本文件，确认当前阶段和下一步。
2. 读取 `python-ability-table.md`，确认用户已掌握的 Python 知识。
3. 读取 `roadmap.md`，只把它当长期方向；不要按源码阅读顺序推进。
4. 每轮只选一个最小 Python 语法点，默认用 5-15 行内联代码讲解。
5. 提一个 checkpoint 后停止，等用户答对或修改正确再进入下一个知识点。
6. 源码链接只在语法 checkpoint 通过后作为验证材料出现，且最多 1-2 个。
7. 只有小主题完成、能力状态变化或用户暂停时，才更新学习状态和能力表。
