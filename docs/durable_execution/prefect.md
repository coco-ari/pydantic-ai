# 使用 Prefect 进行持久化执行 {#durable-execution-with-prefect}

[Prefect](https://www.prefect.io/) 是一个工作流编排框架，用于在 Python 中构建有韧性的数据管道，并与 Pydantic AI 原生集成。

## 持久化执行 {#durable-execution}

Prefect 3.0 为你的 Python 工作流带来了[事务语义](https://www.prefect.io/blog/transactional-ml-pipelines-with-prefect-3-0)，允许你把任务组合成原子单元并定义失败模式。如果事务中的任何部分失败，整个事务都可以回滚到干净状态。

* **Flows** 是工作流的顶层入口点。它们可以包含 tasks 和其他 flows。
* **Tasks** 是单独的工作单元，可以独立重试、缓存和监控。

Prefect 3.0 的事务编排方法让你的工作流天然具备**幂等性**：可以在任何环境中重新运行，而不会产生重复或不一致。每个 task 都在一个 transaction 中执行，该 transaction 管理 task 的结果记录何时以及在哪里持久化。如果 task 在相同上下文下再次运行，它不会重新执行，而是加载之前的结果。

下面的图展示了一个使用 Prefect 的 agentic 应用的整体架构。
Prefect 默认使用客户端侧 task 编排，并可选择连接服务端以获得调度、监控等高级功能。

```text
            +---------------------+
            |   Prefect Server    |      (Monitoring,
            |      or Cloud       |       scheduling, UI,
            +---------------------+       orchestration)
                     ^
                     |
        Flow state,  |   Schedule flows,
        metadata,    |   track execution
        logs         |
                     |
+------------------------------------------------------+
|               Application Process                    |
|   +----------------------------------------------+   |
|   |              Flow (Agent.run)                |   |
|   +----------------------------------------------+   |
|          |          |                |               |
|          v          v                v               |
|   +-----------+ +------------+ +-------------+       |
|   |   Task    | |    Task    | |    Task     |       |
|   |  (Tool)   | | (MCP Tool) | | (Model API) |       |
|   +-----------+ +------------+ +-------------+       |
|         |           |                |               |
|       Cache &     Cache &          Cache &           |
|       persist     persist          persist           |
|         to           to               to             |
|         v            v                v              |
|   +----------------------------------------------+   |
|   |     Result Storage (Local FS, S3, etc.)     |    |
|   +----------------------------------------------+   |
+------------------------------------------------------+
          |           |                |
          v           v                v
      [External APIs, services, databases, etc.]
```

更多信息请参阅 [Prefect 文档](https://docs.prefect.io/)。

## 持久化 Agent {#durable-agent}

任何 agent 都可以包装在 [`PrefectAgent`][pydantic_ai.durable_exec.prefect.PrefectAgent] 中以获得持久化执行能力。`PrefectAgent` 会自动：

* 将 [`Agent.run`][pydantic_ai.agent.Agent.run] 和 [`Agent.run_sync`][pydantic_ai.agent.Agent.run_sync] 包装为 Prefect flows。
* 将[模型请求](../models/overview.md)包装为 Prefect tasks。
* 将[工具调用](../tools.md)包装为 Prefect tasks（可按工具配置）。
* 将 [MCP 通信](../mcp/client.md)包装为 Prefect tasks。

在 Prefect flow 内运行时，事件流处理器会被 Prefect **自动包装**。流中的每个事件都会在单独的 Prefect task 中处理，以实现持久化。创建 `PrefectAgent` 时，你可以使用 `event_stream_handler_task_config` 参数自定义 task 行为。**不要**手动用 `@task` 装饰事件流处理器。示例见[流式文档](../agent.md#streaming-all-events)。

原始 agent、model 和 MCP server 在 Prefect flow 之外仍然可以正常使用。

下面是一个简单但完整的示例，展示如何包装 agent 以获得持久化执行。它只需要安装带 Prefect 的 Pydantic AI：

```bash
pip/uv-add pydantic-ai[prefect]
```

或者，如果你使用 slim 包，可以安装 `prefect` 可选依赖组：

```bash
pip/uv-add pydantic-ai-slim[prefect]
```

```python {title="prefect_agent.py" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.durable_exec.prefect import PrefectAgent

agent = Agent(
    'gpt-5.2',
    instructions="You're an expert in geography.",
    name='geography',  # (1)!
)

prefect_agent = PrefectAgent(agent)  # (2)!

async def main():
    result = await prefect_agent.run('What is the capital of Mexico?')  # (3)!
    print(result.output)
    #> Mexico City (Ciudad de México, CDMX)
```

1. agent 的 `name` 用于唯一标识它的 flows 和 tasks。
2. 用 `PrefectAgent` 包装 agent 后，所有 agent 运行都会启用持久化执行。
3. [`PrefectAgent.run()`][pydantic_ai.durable_exec.prefect.PrefectAgent.run] 的工作方式类似 [`Agent.run()`][pydantic_ai.agent.Agent.run]，但会作为 Prefect flow 运行，并将模型请求、被装饰的工具调用和 MCP 通信作为 Prefect tasks 执行。

_（这个示例是完整的，可以直接运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

关于如何在 Python 应用中使用 Prefect，更多信息见其 [Python 文档](https://docs.prefect.io/v3/how-to-guides/workflows/write-and-run)。

## Prefect 集成注意事项 {#prefect-integration-considerations}

将 Prefect 与 Pydantic AI agents 一起使用时，有几个重要注意事项可以确保工作流行为正确。

### Agent 要求 {#agent-requirements}

每个 agent 实例都必须有唯一的 `name`，这样 Prefect 才能正确识别和跟踪它的 flows 与 tasks。

### 工具包装 {#tool-wrapping}

Agent tools 会自动包装为 Prefect tasks，这意味着它们可以受益于：

* **重试逻辑**：失败的工具调用可以自动重试
* **缓存**：工具结果会根据其输入缓存
* **可观测性**：工具执行会在 Prefect UI 中跟踪

你可以用 `tool_task_config`（应用于所有工具）或 `tool_task_config_by_name`（按工具配置）自定义工具 task 行为：

```python {title="prefect_agent_config.py" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.durable_exec.prefect import PrefectAgent, TaskConfig

agent = Agent('gpt-5.2', name='my_agent')

@agent.tool_plain
def fetch_data(url: str) -> str:
    # This tool will be wrapped as a Prefect task
    ...

prefect_agent = PrefectAgent(
    agent,
    tool_task_config=TaskConfig(retries=3),  # Default for all tools
    tool_task_config_by_name={
        'fetch_data': TaskConfig(timeout_seconds=10.0),  # Specific to fetch_data
        'simple_tool': None,  # Disable task wrapping for simple_tool
    },
)
```

在 `tool_task_config_by_name` 中把某个工具的 config 设置为 `None`，即可禁用该特定工具的 task 包装。

### 流式传输 {#streaming}

在 Prefect flow 内运行时，[`Agent.run_stream()`][pydantic_ai.agent.Agent.run_stream] 可以工作，但不会提供实时流式传输，因为 Prefect tasks 会在返回结果前消费完整执行。该方法会完整执行，并一次性返回完整结果。

如果想在 Prefect flows 内获得实时流式行为，可以在 `Agent` 或 `PrefectAgent` 实例上设置 [`event_stream_handler`][pydantic_ai.agent.EventStreamHandler]，并使用 [`PrefectAgent.run()`][pydantic_ai.durable_exec.prefect.PrefectAgent.run]。

**注意**：事件流处理器在 Prefect flow 内外行为不同：
- **flow 外部**：处理器会随着模型流式返回而接收事件
- **flow 内部**：每个事件都会被包装为 Prefect task 以获得持久化，这可能影响时序，但能保证可靠性

事件流处理器函数会接收 agent [run context][pydantic_ai.tools.RunContext]，以及来自模型流式响应和 agent 工具执行的异步事件迭代器。示例见[流式文档](../agent.md#streaming-all-events)。

## Task 配置 {#task-configuration}

你可以通过向 `PrefectAgent` 构造函数传入 [`TaskConfig`][pydantic_ai.durable_exec.prefect.TaskConfig] 对象，自定义 Prefect task 行为，例如重试和超时：

- `mcp_task_config`：MCP server 通信 tasks 的配置
- `model_task_config`：模型请求 tasks 的配置
- `tool_task_config`：所有工具调用的默认配置
- `tool_task_config_by_name`：按工具配置 task（覆盖 `tool_task_config`）
- `event_stream_handler_task_config`：事件流处理器 tasks 的配置（在 Prefect flow 内运行时应用）

可用的 `TaskConfig` 选项：

- `retries`：task 的最大重试次数（默认：`0`）
- `retry_delay_seconds`：重试之间的秒数延迟（可以是单个值，也可以是指数退避列表；默认：`1.0`）
- `timeout_seconds`：task 完成允许的最大秒数
- `cache_policy`：task 的自定义 Prefect 缓存策略
- `persist_result`：是否持久化 task 结果
- `result_storage`：task 的 Prefect 结果存储（例如 `'s3-bucket/my-storage'` 或 `WritableFileSystem` block）
- `log_prints`：是否记录 task 中的 print 语句（默认：`False`）

示例：

```python {title="prefect_agent_config.py" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.durable_exec.prefect import PrefectAgent, TaskConfig

agent = Agent(
    'gpt-5.2',
    instructions="You're an expert in geography.",
    name='geography',
)

prefect_agent = PrefectAgent(
    agent,
    model_task_config=TaskConfig(
        retries=3,
        retry_delay_seconds=[1.0, 2.0, 4.0],  # Exponential backoff
        timeout_seconds=30.0,
    ),
)

async def main():
    result = await prefect_agent.run('What is the capital of France?')
    print(result.output)
    #> Paris
```

_（这个示例是完整的，可以直接运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

### 重试注意事项 {#retry-considerations}

Pydantic AI 和 provider API clients 拥有自己的重试逻辑。使用 Prefect 时，你可能希望：

* 在 Pydantic AI 中禁用 [HTTP 请求重试](../retries.md)
* 关闭 provider API client 的重试逻辑（例如在[自定义 OpenAI client](../models/openai.md#custom-openai-client) 上设置 `max_retries=0`）
* 依赖 Prefect 的 task-level 重试配置以保持一致性

这可以避免请求在不同层被重复重试。

## 缓存和幂等性 {#caching-and-idempotency}

Prefect 3.0 提供内置缓存和事务语义。输入相同的 tasks 如果已有缓存结果，就不会重新执行，这让工作流天然具备幂等性，并能从失败中恢复。

* **Task 输入**：Messages、settings、parameters、tool arguments 和可序列化依赖

**注意**：如果要把用户依赖纳入缓存键，它们必须是可序列化的（例如 Pydantic models 或基础 Python 类型）。不可序列化依赖会自动从缓存计算中排除。

## 使用 Prefect 和 Logfire 进行可观测性 {#observability-with-prefect-and-logfire}

Prefect 提供内置 UI，用于监控 flow runs、task executions 和 failures。你可以：

* 查看实时 flow run 状态
* 用完整 stack traces 调试失败
* 设置 alerts 和 notifications

要访问 Prefect UI，可以：

1. 使用 [Prefect Cloud](https://www.prefect.io/cloud)（托管服务）
2. 用 `prefect server start` 运行本地 [Prefect server](https://docs.prefect.io/v3/how-to-guides/self-hosted/server-cli)

你也可以使用 [Pydantic Logfire](../logfire.md) 获得详细可观测性。同时使用 Prefect 和 Logfire 时，你会得到互补视图：

* **Prefect**：workflow-level 编排、task 状态和重试历史
* **Logfire**：agent runs、模型请求和工具调用的细粒度 tracing

将 Logfire 与 Prefect 一起使用时，可以启用 distributed tracing，在 agent runs、模型请求和工具调用中看到包含 Prefect runs 的 spans。

关于 Prefect 监控的更多信息，请参阅 [Prefect 文档](https://docs.prefect.io/)。

## 部署和调度 {#deployments-and-scheduling}

要部署和调度 `PrefectAgent`，请把它包装在 Prefect flow 中，并使用 flow 的 [`serve()`](https://docs.prefect.io/v3/how-to-guides/deployments/create-deployments#create-a-deployment-with-serve) 或 [`deploy()`](https://docs.prefect.io/v3/how-to-guides/deployments/deploy-via-python) 方法：

```python {title="serve_agent.py" test="skip"}
from prefect import flow

from pydantic_ai import Agent
from pydantic_ai.durable_exec.prefect import PrefectAgent


@flow
async def daily_report_flow(user_prompt: str):
    """Generate a daily report using the agent."""
    agent = Agent(  # (1)!
        'openai:gpt-5.2',
        name='daily_report_agent',
        instructions='Generate a daily summary report.',
    )

    prefect_agent = PrefectAgent(agent)

    result = await prefect_agent.run(user_prompt)
    return result.output



# Serve the flow with a daily schedule
if __name__ == '__main__':
    daily_report_flow.serve(
        name='daily-report-deployment',
        cron='0 9 * * *',  # Run daily at 9am
        parameters={'user_prompt': "Generate today's report"},
        tags=['production', 'reports'],
    )
```

1. 每次 flow run 都在隔离进程中执行，所有输入和依赖都必须可序列化。由于 Agent 实例无法序列化，请在 flow 内实例化 agent，而不是在模块级实例化。

`serve()` 方法接受调度选项：

- **`cron`**：Cron 调度字符串（例如 `'0 9 * * *'` 表示每天上午 9 点运行）
- **`interval`**：以秒数或 timedelta 表示的调度间隔
- **`rrule`**：iCalendar RRule 调度字符串

对于使用 Docker、Kubernetes 或其他基础设施的生产部署，请使用 flow 的 [`deploy()`](https://docs.prefect.io/v3/how-to-guides/deployments/deploy-via-python) 方法。更多信息请参阅 [Prefect 部署文档](https://docs.prefect.io/v3/how-to-guides/deployments/create-deploymentsy)。
