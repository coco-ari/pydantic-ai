# Pydantic AI 源码学习路线

## 学习原则

- 先文档，再入口文件，再核心流程，最后深入 provider、tool、streaming 和 graph。
- 每一节先补 Python 前置知识，再读源码。
- 每次只读少量文件，读完做一个小练习。
- 讲解时优先链接真实文件，不凭记忆描述。

## 阶段 0：建立地图

目标：知道项目是什么、有哪些包、最小示例如何运行。

阅读顺序：

1. `docs/index.md`
2. `docs/install.md`
3. `docs/agent.md`
4. `README.md`
5. 根目录 `pyproject.toml`

需要补的 Python：

- `import`
- 函数调用
- 字符串
- 关键字参数
- 类与实例

阶段练习：

- 用自己的话解释 `Agent('openai:gpt-5.2')` 这一行做了什么。

## 阶段 1：包结构

目标：知道每个主要包负责什么。

主包：

- `pydantic_ai_slim/pydantic_ai/`：核心 Agent 框架。
- `pydantic_graph/pydantic_graph/`：图执行引擎，驱动 Agent 循环。
- `pydantic_evals/pydantic_evals/`：评估框架。
- `clai/clai/`：命令行聊天应用。
- `docs/`：用户文档。
- `tests/`：行为测试和文档示例测试。

阶段练习：

- 从一个文件路径判断它属于"核心框架、图执行、评估、CLI、文档、测试"中的哪一类。

## 阶段 2：`Agent` API 入口

目标：理解用户代码 `from pydantic_ai import Agent` 如何到达真正的类。

阅读顺序：

1. `pydantic_ai_slim/pydantic_ai/__init__.py`
2. `pydantic_ai_slim/pydantic_ai/agent/__init__.py`
3. `pydantic_ai_slim/pydantic_ai/agent/abstract.py`
4. `pydantic_ai_slim/pydantic_ai/agent/wrapper.py`

需要补的 Python：

- 包导入和重新导出
- 类
- 方法
- 继承
- 类型注解

阶段练习：

- 找出 `Agent.run_sync` 是在哪里定义或继承来的。

## 阶段 3：最小运行流程

目标：理解 `agent.run_sync('hello')` 到模型响应的大致链路。

阅读顺序：

1. `docs/agent.md` 的 "Running Agents"
2. `pydantic_ai_slim/pydantic_ai/run.py`
3. `pydantic_ai_slim/pydantic_ai/_agent_graph.py`
4. `pydantic_ai_slim/pydantic_ai/messages.py`
5. `pydantic_ai_slim/pydantic_ai/models/test.py`

核心问题：

- `run_sync()` 和 `run()` 是什么关系？
- 用户 prompt 如何变成 request message？
- 模型响应如何变成 `RunResult.output`？
- 为什么底层需要 graph？

需要补的 Python：

- `async` / `await`
- context manager
- dataclass
- union 类型
- Pydantic model

阶段练习：

- 画出 `run_sync -> run -> graph -> model -> result` 的 5 步流程。

## 阶段 4：工具与依赖注入

目标：理解 `@agent.tool`、`RunContext` 和 `deps`。

阅读顺序：

1. `docs/tools.md`
2. `docs/dependencies.md`
3. `pydantic_ai_slim/pydantic_ai/tools.py`
4. `pydantic_ai_slim/pydantic_ai/_run_context.py`
5. `pydantic_ai_slim/pydantic_ai/toolsets/function.py`

阶段练习：

- 写一个只返回固定字符串的 tool，并解释 `ctx.deps` 从哪里来。

## 阶段 5：结构化输出与消息历史

目标：理解 `output_type`、Pydantic 校验、历史消息复用。

阅读顺序：

1. `docs/output.md`
2. `docs/message-history.md`
3. `pydantic_ai_slim/pydantic_ai/output.py`
4. `pydantic_ai_slim/pydantic_ai/_output.py`
5. `pydantic_ai_slim/pydantic_ai/messages.py`

阶段练习：

- 解释 `result.output` 为什么可以是 `str`，也可以是一个 `BaseModel`。

## 阶段 6：模型、Provider 和 Profile

目标：理解模型无关是怎么实现的。

阅读顺序：

1. `docs/models/overview.md`
2. `pydantic_ai_slim/pydantic_ai/models/__init__.py`
3. `pydantic_ai_slim/pydantic_ai/models/openai.py`
4. `pydantic_ai_slim/pydantic_ai/providers/openai.py`
5. `pydantic_ai_slim/pydantic_ai/profiles/openai.py`

阶段练习：

- 说明 model、provider、profile 三者各自负责什么。

## 阶段 7：Streaming、Capabilities、Durable Exec

目标：理解更高级的运行方式。

阅读顺序：

1. `docs/capabilities.md`
2. `docs/deferred-tools.md`
3. `docs/durable_execution/overview.md`
4. `pydantic_ai_slim/pydantic_ai/capabilities/`
5. `pydantic_ai_slim/pydantic_ai/durable_exec/`

阶段练习：

- 解释为什么 capability 适合做可组合扩展。
