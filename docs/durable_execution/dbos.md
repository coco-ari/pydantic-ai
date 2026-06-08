# 使用 DBOS 进行持久化执行 {#durable-execution-with-dbos}

[DBOS](https://www.dbos.dev/) 是一个轻量级[持久化执行](https://docs.dbos.dev/architecture)库，与 Pydantic AI 原生集成。

## 持久化执行 {#durable-execution}

DBOS workflows 会通过在数据库中 checkpoint 程序状态，让程序变得**持久化**。如果程序失败，重启时所有 workflows 都会自动从最后完成的 step 恢复。

* **Workflows** 必须是确定性的，通常不能包含 I/O。
* **Steps** 可以执行 I/O（网络、磁盘、API 调用）。如果 step 失败，它会从头重启。

每个 workflow input 和 step output 都会持久化存储在系统数据库中。当 workflow execution 因崩溃、网络问题或 server 重启而失败时，DBOS 会利用这些 checkpoints 从最后完成的 step 恢复 workflows。

DBOS **queues** 为 Celery 或 BullMQ 等系统提供了持久化、数据库支撑的替代方案，支持并发限制、速率限制、超时和优先级等功能。详情请参见 [DBOS docs](https://docs.dbos.dev/architecture)。

下图展示了 DBOS 中 agentic application 的整体架构。DBOS 完全作为库在进程内运行。函数仍然是普通 Python 函数，但会 checkpoint 到数据库（Postgres 或 SQLite）中。

```text
                    Clients
            (HTTP, RPC, Kafka, etc.)
                        |
                        v
+------------------------------------------------------+
|               Application Servers                    |
|                                                      |
|   +----------------------------------------------+   |
|   |        Pydantic AI + DBOS Libraries          |   |
|   |                                              |   |
|   |  [ Workflows (Agent Run Loop) ]              |   |
|   |  [ Steps (Tool, MCP, Model) ]                |   |
|   |  [ Queues ]   [ Cron Jobs ]   [ Messaging ]  |   |
|   +----------------------------------------------+   |
|                                                      |
+------------------------------------------------------+
                        |
                        v
+------------------------------------------------------+
|                      Database                        |
|   (Stores workflow and step state, schedules tasks)  |
+------------------------------------------------------+
```

更多信息请参见 [DBOS documentation](https://docs.dbos.dev/architecture)。

## 持久化 Agent {#durable-agent}

任何 agent 都可以包装为 [`DBOSAgent`][pydantic_ai.durable_exec.dbos.DBOSAgent] 以获得持久化执行。`DBOSAgent` 会自动：

* 将 `Agent.run` 和 `Agent.run_sync` 包装为 DBOS workflows。
* 将 [model requests](../models/overview.md) 和 [MCP communication](../mcp/client.md) 包装为 DBOS steps。

自定义 tool functions 和 event stream handlers **不会被 DBOS 自动包装**。如果它们涉及非确定性行为或执行 I/O，应显式用 `@DBOS.step` 装饰它们。

原始 agent、model 和 MCP server 仍可在 DBOS workflow 外正常使用。

下面是一个简单但完整的示例，展示如何包装 agent 以进行持久化执行。它只需要安装带 DBOS [open-source library](https://github.com/dbos-inc/dbos-transact-py) 的 Pydantic AI：

```bash
pip/uv-add pydantic-ai[dbos]
```

或者，如果你使用 slim 包，可以安装带 `dbos` 可选组的版本：

```bash
pip/uv-add pydantic-ai-slim[dbos]
```

```python {title="dbos_agent.py" test="skip"}
from dbos import DBOS, DBOSConfig

from pydantic_ai import Agent
from pydantic_ai.durable_exec.dbos import DBOSAgent

dbos_config: DBOSConfig = {
    'name': 'pydantic_dbos_agent',
    'system_database_url': 'sqlite:///dbostest.sqlite',  # (3)!
}
DBOS(config=dbos_config)

agent = Agent(
    'gpt-5.2',
    instructions="You're an expert in geography.",
    name='geography',  # (4)!
)

dbos_agent = DBOSAgent(agent)  # (1)!

async def main():
    DBOS.launch()
    result = await dbos_agent.run('What is the capital of Mexico?')  # (2)!
    print(result.output)
    #> Mexico City (Ciudad de México, CDMX)
```

1. Workflows 和 `DBOSAgent` 必须在 `DBOS.launch()` 前定义，这样 recovery 才能正确找到所有 workflows。
2. [`DBOSAgent.run()`][pydantic_ai.durable_exec.dbos.DBOSAgent.run] 的工作方式类似 [`Agent.run()`][pydantic_ai.agent.Agent.run]，但会作为 DBOS workflow 运行，并将 model requests、已装饰 tool calls 和 MCP communication 作为 DBOS steps 执行。
3. 此示例使用 SQLite。生产环境推荐使用 Postgres。
4. agent 的 `name` 用于唯一标识其 workflows。

_（此示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

由于 DBOS workflows 需要在调用 `DBOS.launch()` 前定义，而 `DBOSAgent` 实例会自动将 `run` 和 `run_sync` 注册为 workflows，因此它也需要在调用 `DBOS.launch()` 前定义。

关于如何在 Python applications 中使用 DBOS，更多信息请参见其 [Python SDK guide](https://docs.dbos.dev/python/programming-guide)。

## DBOS 集成注意事项 {#dbos-integration-considerations}

将 DBOS 与 Pydantic AI agents 一起使用时，需要注意几个重要事项，以确保 workflows 和 toolsets 行为正确。

### Agent 和 Toolset 要求 {#agent-and-toolset-requirements}

每个 agent 实例都必须有唯一的 `name`，这样 DBOS 才能在失败或重启后正确恢复 workflows。

Tools 和 event stream handlers 不会被 DBOS 自动包装。你可以决定如何集成它们：

* 如果函数涉及非确定性或 I/O，请用 `@DBOS.step` 装饰。
* 如果不需要 durability，可以跳过装饰器，以避免额外的 DB checkpoint 写入。
* 如果函数需要 enqueue tasks 或调用其他 DBOS workflows，请在 agent 的主 workflow 内运行它（不要作为 step）。

除此之外，任何 agent 和 toolset 都可以直接工作。

### Agent Run Context 和依赖 {#agent-run-context-and-dependencies}

DBOS 使用 [`pickle`](https://docs.python.org/3/library/pickle.html) 将 workflow inputs/outputs 和 step outputs checkpoint 到数据库中。这意味着你需要确保提供给 [`DBOSAgent.run()`][pydantic_ai.durable_exec.dbos.DBOSAgent.run] 或 [`DBOSAgent.run_sync()`][pydantic_ai.durable_exec.dbos.DBOSAgent.run_sync] 的[依赖](../dependencies.md)对象，以及 tool outputs 都可以用 pickle 序列化。你也可能需要让 inputs 和 outputs 保持较小（小于约 2 MB）。PostgreSQL 和 SQLite 每个字段最多支持 1 GB，但大对象可能影响性能。

### Streaming {#streaming}

由于 DBOS 无法直接将 output stream 到 workflow 或 step 调用位置，因此在 DBOS workflow 内运行时不支持 [`Agent.run_stream()`][pydantic_ai.agent.Agent.run_stream] 和 [`Agent.run_stream_events()`][pydantic_ai.agent.Agent.run_stream_events]。

你可以改为在 `Agent` 或 `DBOSAgent` 实例上设置 [`event_stream_handler`][pydantic_ai.agent.EventStreamHandler]，并使用 [`DBOSAgent.run()`][pydantic_ai.durable_exec.dbos.DBOSAgent.run] 来实现 streaming。event stream handler 函数会接收 agent [run context][pydantic_ai.tools.RunContext]，以及来自 model streaming response 和 agent 工具执行的 events 的 async iterable。示例请参见 [streaming docs](../agent.md#streaming-all-events)。


### 并行工具执行 {#parallel-tool-execution}

使用 `DBOSAgent` 时，tools 默认并行执行，以最小化延迟。为了保证确定性 replay 和可靠 recovery，DBOS 会等待所有并行 tool calls 完成，然后**按顺序**发出 events。这等价于 [`with agent.parallel_tool_call_execution_mode('parallel_ordered_events')`][pydantic_ai.agent.AbstractAgent.parallel_tool_call_execution_mode] 的行为。

如果你更偏好严格顺序，可以在初始化 `DBOSAgent` 时设置 [`parallel_execution_mode='sequential'`][pydantic_ai.durable_exec.dbos.DBOSAgent]，让 agent 顺序运行 tools。


## Step 配置 {#step-configuration}

你可以向 `DBOSAgent` 构造函数传入 [`StepConfig`][pydantic_ai.durable_exec.dbos.StepConfig] 对象，自定义 DBOS step 行为，例如 retries：

- `mcp_step_config`：用于 MCP server communication 的 DBOS step config。省略时不重试。
- `model_step_config`：用于 model request steps 的 DBOS step config。省略时不重试。

对于 custom tools，可以根据需要直接用 [`@DBOS.step`](https://docs.dbos.dev/python/reference/decorators#step) 或 [`@DBOS.workflow`](https://docs.dbos.dev/python/reference/decorators#workflow) decorators 标注它们。这些 decorators 在 DBOS workflows 外没有效果，因此 tools 在非 DBOS agents 中仍可使用。


## Step 重试 {#step-retries}

除了 DBOS 会对 request failures 执行自动 retries 之外，Pydantic AI 和各类 provider API clients 也有自己的 request retry 逻辑。同时启用这些机制可能导致 request 重试次数超过预期，并带来不当的 `Retry-After` 处理。

使用 DBOS 时，推荐不要使用 [HTTP Request Retries](../retries.md)，并关闭 provider API client 自身的 retry 逻辑，例如在[自定义 `OpenAIProvider` API client](../models/openai.md#custom-openai-client) 上设置 `max_retries=0`。

你可以使用 [step configuration](#step-configuration) 自定义 DBOS 的 retry policy。

## 使用 Logfire 进行可观测性分析 {#observability-with-logfire}

可以配置 DBOS 为每次 workflow 和 step execution 生成 OpenTelemetry spans，而 Pydantic AI 会为每次 agent run、model request 和 tool invocation 发出 spans。你可以将这些 spans 发送到 [Pydantic Logfire](../logfire.md)，以获得应用中正在发生事情的完整端到端视图。

关于 DBOS logging 和 tracing 的更多信息，请参见 [DBOS docs](https://docs.dbos.dev/python/tutorials/logging-and-tracing)。
