# 使用 Temporal 实现持久化执行

[Temporal](https://temporal.io) 是一个流行的[持久化执行](https://docs.temporal.io/evaluate/understanding-temporal#durable-execution)平台，Pydantic AI 对它提供原生支持。

## 持久化执行 {#durable-execution}

在 Temporal 的持久化执行实现中，如果程序在与模型或 API 交互时崩溃或遇到异常，它会一直重试，直到能够成功完成。

Temporal 主要依赖 replay 机制从故障中恢复。
随着程序推进，Temporal 会保存关键输入和决策，让重新启动的程序能够从中断处继续。

让这一机制生效的关键，是把应用中可重复（确定性）和不可重复（非确定性）的部分分开：

1. 确定性部分称为 [**workflows**](https://docs.temporal.io/workflow-definition)，在相同输入下重新运行时会以相同方式执行。
2. 非确定性部分称为 [**activities**](https://docs.temporal.io/activities)，可以运行任意代码，执行 I/O 和其他操作。

Workflow 代码可以长时间运行；如果被中断，可以从中断处精确恢复。
关键是，workflow 代码通常_不能_包含任何类型的 I/O，包括网络、磁盘等。
Activity 代码对 I/O 或外部交互没有限制，但如果一个 activity 中途失败，会从头重新启动。


!!! note

    如果你熟悉 celery，把 Temporal activities 理解为类似 celery tasks 可能会有帮助，只是你会等待 task 完成并取得结果，然后再进入 workflow 的下一步。
    但 Temporal workflows 和 activities 比 celery tasks 提供了更多灵活性和功能。

    更多信息请参阅 [Temporal 文档](https://docs.temporal.io/evaluate/understanding-temporal#temporal-application-the-building-blocks)。

对于 Pydantic AI agents，与 Temporal 集成意味着由于 I/O 要求，[模型请求](../models/overview.md)、可能需要 I/O 的[工具调用](../tools.md)，以及 [MCP server 通信](../mcp/client.md)都需要卸载到 Temporal activities，而协调它们的逻辑（也就是 agent run）位于 workflow 中。处理计划任务或 Web 请求的代码随后可以执行 workflow，而 workflow 会按需执行 activities。

下图展示了 Temporal 中 agentic application 的整体架构。
Temporal Server 负责跟踪程序执行，并确保相关状态被可靠保存（即存储到内部数据库，并且可能跨云区域复制）。
Temporal Server 以加密形式管理数据，因此所有数据处理都发生在 Worker 上，Worker 负责运行 workflow 和 activities。


```text
            +---------------------+
            |   Temporal Server   |      (Stores workflow state,
            +---------------------+       schedules activities,
                     ^                    persists progress)
                     |
        Save state,  |   Schedule Tasks,
        progress,    |   load state on resume
        timeouts     |
                     |
+------------------------------------------------------+
|                      Worker                          |
|   +----------------------------------------------+   |
|   |              Workflow Code                   |   |
|   |       (Agent Run Loop)                       |   |
|   +----------------------------------------------+   |
|          |          |                |               |
|          v          v                v               |
|   +-----------+ +------------+ +-------------+       |
|   | Activity  | | Activity   | |  Activity   |       |
|   | (Tool)    | | (MCP Tool) | | (Model API) |       |
|   +-----------+ +------------+ +-------------+       |
|         |           |                |               |
+------------------------------------------------------+
          |           |                |
          v           v                v
      [External APIs, services, databases, etc.]
```

更多信息请参阅 [Temporal 文档](https://docs.temporal.io/evaluate/understanding-temporal#temporal-application-the-building-blocks)。

## 持久化 Agent {#durable-agent}

任何 agent 都可以包装成 [`TemporalAgent`][pydantic_ai.durable_exec.temporal.TemporalAgent]，得到可在确定性 Temporal workflow 中使用的持久化 agent；它会自动把所有需要 I/O 的工作（即模型请求、工具调用和 MCP server 通信）卸载到非确定性 activities。

包装时，agent 的[模型](../models/overview.md)和 [toolsets](../toolsets.md)（包括注册在 agent 上的 function tools 和 MCP servers）会被冻结，为每个项目动态创建 activities，并把原始模型和 toolsets 包装成调用 worker 执行对应 activities，而不是在 workflow 内直接执行动作。原始 agent 在 Temporal workflow 外仍可照常使用，但包装后对它的模型或 toolsets 所做的任何修改，都不会反映到持久化 agent 中。

下面是一个简单但完整的示例，展示如何包装 agent 以进行持久化执行、创建带持久化执行逻辑的 Temporal workflow、连接到 Temporal server，并从非持久化代码运行 workflow。它唯一需要的是一个[本地运行的](https://github.com/temporalio/temporal#download-and-start-temporal-server-locally) Temporal server：

```sh
brew install temporal
temporal server start-dev
```

```python {title="temporal_agent.py" test="skip"}
import uuid

from temporalio import workflow
from temporalio.client import Client
from temporalio.worker import Worker

from pydantic_ai import Agent
from pydantic_ai.durable_exec.temporal import (
    PydanticAIPlugin,
    PydanticAIWorkflow,
    TemporalAgent,
)

agent = Agent(
    'openai:gpt-5.2',
    instructions="You're an expert in geography.",
    name='geography',  # (10)!
)

temporal_agent = TemporalAgent(agent)  # (1)!


@workflow.defn
class GeographyWorkflow(PydanticAIWorkflow):  # (2)!
    __pydantic_ai_agents__ = [temporal_agent]  # (3)!

    @workflow.run
    async def run(self, prompt: str) -> str:
        result = await temporal_agent.run(prompt)  # (4)!
        return result.output


async def main():
    client = await Client.connect(  # (5)!
        'localhost:7233',  # (6)!
        plugins=[PydanticAIPlugin()],  # (7)!
    )

    async with Worker(  # (8)!
        client,
        task_queue='geography',
        workflows=[GeographyWorkflow],
    ):
        output = await client.execute_workflow(  # (10)!
            GeographyWorkflow.run,
            args=['What is the capital of Mexico?'],
            id=f'geography-{uuid.uuid4()}',
            task_queue='geography',
        )
        print(output)
        #> Mexico City (Ciudad de México, CDMX)
```

1. 原始 `Agent` 不能在确定性 Temporal workflow 中使用，但 `TemporalAgent` 可以。
2. 如上所述，workflow 表示一段确定性代码，可为需要 I/O 的操作使用非确定性 activities。继承 [`PydanticAIWorkflow`][pydantic_ai.durable_exec.temporal.PydanticAIWorkflow] 是可选的，但它能为 `__pydantic_ai_agents__` 类变量提供正确类型。
3. 列出该 workflow 使用的 `TemporalAgent`s。[`PydanticAIPlugin`][pydantic_ai.durable_exec.temporal.PydanticAIPlugin] 会自动把它们的 activities 注册到 worker。或者，如果修改 worker 初始化比修改 workflow 类更容易，可以使用 [`AgentPlugin`][pydantic_ai.durable_exec.temporal.AgentPlugin] 直接在 worker 上注册 agents。
4. [`TemporalAgent.run()`][pydantic_ai.durable_exec.temporal.TemporalAgent.run] 的工作方式与 [`Agent.run()`][pydantic_ai.agent.Agent.run] 相同，但会自动把模型请求、工具调用和 MCP server 通信卸载到 Temporal activities。
5. 我们连接到 Temporal server，它会跟踪 workflow 和 activity 执行。
6. 这里假设 Temporal server 正在[本地运行](https://github.com/temporalio/temporal#download-and-start-temporal-server-locally)。
7. [`PydanticAIPlugin`][pydantic_ai.durable_exec.temporal.PydanticAIPlugin] 告诉 Temporal 使用 Pydantic 进行序列化和反序列化，把 [`UserError`][pydantic_ai.exceptions.UserError] 异常视为不可重试，并自动为 `__pydantic_ai_agents__` 中列出的 agents 注册 activities。
8. 我们启动 worker，它会监听指定 task queue，并运行 workflows 和 activities。在真实应用中，它可能运行在单独服务里。
9. agent 的 `name` 用于唯一标识其 activities。
10. 我们要求 server 在监听指定 task queue 的 worker 上执行 workflow。

_（这个示例是完整的，可以"按原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

在真实应用中，agent、workflow 和 worker 通常与请求执行 workflow 的代码分开定义。
由于 Temporal workflows 必须定义在文件顶层，并且 workflow 内部和启动 worker（用于注册 activities）时都需要 `TemporalAgent` 实例，因此它也需要定义在文件顶层。

关于如何在 Python 应用中使用 Temporal 的更多信息，请参阅它们的 [Python SDK 指南](https://docs.temporal.io/develop/python)。

## Temporal 集成注意事项 {#temporal-integration-considerations}

使用 Temporal 进行持久化执行时，有一些特定于 agents 和 toolsets 的注意事项。理解这些内容很重要，可以确保你的 agents 和 toolsets 正确配合 Temporal 的 workflow 和 activity 模型。

### Agent Names 与 Toolset IDs {#agent-names-and-toolset-ids}

为确保当 activity 失败或被中断后重启时，即使期间代码发生变化，Temporal 也知道要运行哪段代码，每个 activity 都需要有稳定且唯一的名称。

当 `TemporalAgent` 为包装 agent 的模型请求和 toolsets（具体来说，是那些实现自己工具列表和调用逻辑的 toolsets，即 [`FunctionToolset`][pydantic_ai.toolsets.FunctionToolset] 和 [`MCPServer`][pydantic_ai.mcp.MCPServer]）动态创建 activities 时，它们的名称会派生自 agent 的 [`name`][pydantic_ai.agent.AbstractAgent.name] 和 toolsets 的 [`id`s][pydantic_ai.toolsets.AbstractToolset.id]。这些字段通常是可选的，但使用 Temporal 时必须设置。持久化 agent 部署到生产后，不应再修改这些字段，否则会破坏活跃 workflows。

对于用 [`@agent.toolset`][pydantic_ai.agent.Agent.toolset] 装饰器创建的动态 toolsets，必须显式设置 `id` 参数。注意，使用 Temporal 时不会遵守 `per_run_step=False`，因为 toolset 总是需要在 activity 中即时创建。

除此之外，任何 agent 和 toolset 都会正常工作。

### Agent Run Context 与 Dependencies {#agent-run-context-and-dependencies}

由于 workflows 和 activities 在不同进程中运行，它们之间传递的任何值都需要可序列化。由于这些 payload 会存储在 workflow execution event history 中，Temporal 将其大小限制为 2MB。

为适应这些限制，在 activities 内运行的工具函数和 [event stream handler](#streaming) 会收到 agent [`RunContext`][pydantic_ai.tools.RunContext] 的受限版本；你需要负责确保传给 [`TemporalAgent.run()`][pydantic_ai.durable_exec.temporal.TemporalAgent.run] 的 [dependencies](../dependencies.md) 对象可以用 Pydantic 序列化。

具体来说，默认只有 `deps`、`run_id`、`metadata`、`retries`、`tool_call_id`、`tool_name`、`tool_call_approved`、`tool_call_metadata`、`retry`、`max_retries`、`run_step`、`usage` 和 `partial_output` 字段可用；尝试访问 `model`、`prompt`、`messages` 或 `tracer` 会抛出错误。
如果你需要在 activities 内访问其中一个或多个属性，可以创建 [`TemporalRunContext`][pydantic_ai.durable_exec.temporal.TemporalRunContext] 子类，实现自定义 `serialize_run_context` 和 `deserialize_run_context` 类方法，并把它作为 `run_context_type` 传给 [`TemporalAgent`][pydantic_ai.durable_exec.temporal.TemporalAgent]。

### Streaming 流式传输 {#streaming}

因为 Temporal activities 不能直接向 activity 调用位置 streaming 输出，所以不支持 [`Agent.run_stream()`][pydantic_ai.agent.Agent.run_stream]、[`Agent.run_stream_events()`][pydantic_ai.agent.Agent.run_stream_events] 和 [`Agent.iter()`][pydantic_ai.agent.Agent.iter]。

可以改为在 `Agent` 或 `TemporalAgent` 实例上设置 [`event_stream_handler`][pydantic_ai.agent.EventStreamHandler]，并在 workflow 内使用 [`TemporalAgent.run()`][pydantic_ai.durable_exec.temporal.TemporalAgent.run] 来实现 streaming。
event stream handler 函数会接收 agent [run context][pydantic_ai.tools.RunContext]，以及来自模型 streaming response 和 agent 工具执行的事件异步 iterable。示例请参阅 [streaming docs](../agent.md#streaming-all-events)。

由于 streaming 模型请求 activity、workflow 和 workflow execution call 都发生在不同进程中，在它们之间传递数据需要小心处理：

- 要从 workflow 调用位置或 workflow 向 event stream handler 传递数据，可以使用 [dependencies object](#agent-run-context-and-dependencies)。
- 要从 event stream handler 向 workflow、workflow 调用位置或前端传递数据，需要使用外部系统，event stream handler 可以写入该系统，而事件消费者可以从中读取，例如消息队列。你可以使用 dependency object，确保所有需要它的地方都拥有相同连接字符串或其他唯一 ID。

### 运行时模型选择 {#model-selection-at-runtime}

[`Agent.run(model=...)`][pydantic_ai.agent.Agent.run] 通常同时支持模型字符串（如 `'openai:gpt-5.2'`）和模型实例。但是，`TemporalAgent` 不支持任意模型实例，因为它们无法为 Temporal 的 replay 机制序列化。

要在 `TemporalAgent` 中使用模型实例，需要通过 `TemporalAgent(models={...})` 传入模型实例字典来预注册它们。之后你可以按名称引用它们，或直接传入已注册实例。如果包装的 agent 没有设置模型，第一个注册模型会用作默认模型。

模型字符串会按预期工作。在需要自定义模型字符串所用 provider 的场景（例如从 deps 注入 API keys）中，可以向 `TemporalAgent` 传入 `provider_factory`，它会接收 [`RunContext`][pydantic_ai.tools.RunContext] 和 provider name。

下面示例展示如何预注册并使用多个模型：

```python {title="multi_model_temporal.py" test="skip"}
from dataclasses import dataclass
from typing import Any

from temporalio import workflow

from pydantic_ai import Agent, RunContext
from pydantic_ai.durable_exec.temporal import TemporalAgent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers import Provider


@dataclass
class Deps:
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None


# Create models from different providers
default_model = OpenAIResponsesModel('gpt-5.2')
fast_model = AnthropicModel('claude-sonnet-4-5')
reasoning_model = GoogleModel('gemini-3-pro-preview')


# Optional: provider factory for dynamic model configuration
def my_provider_factory(run_context: RunContext[Deps], provider_name: str) -> Provider[Any]:
    """Create providers with custom configuration based on run context."""
    if provider_name == 'openai':
        from pydantic_ai.providers.openai import OpenAIProvider

        return OpenAIProvider(api_key=run_context.deps.openai_api_key)
    elif provider_name == 'anthropic':
        from pydantic_ai.providers.anthropic import AnthropicProvider

        return AnthropicProvider(api_key=run_context.deps.anthropic_api_key)
    else:
        raise ValueError(f'Unknown provider: {provider_name}')


agent = Agent(default_model, name='multi_model_agent', deps_type=Deps)

temporal_agent = TemporalAgent(
    agent,
    models={
        'fast': fast_model,
        'reasoning': reasoning_model,
    },
    provider_factory=my_provider_factory,  # Optional
)


@workflow.defn
class MultiModelWorkflow:
    @workflow.run
    async def run(self, prompt: str, use_reasoning: bool, use_fast: bool) -> str:
        if use_reasoning:
            # Select by registered name
            result = await temporal_agent.run(prompt, model='reasoning')
        elif use_fast:
            # Or pass the registered instance directly
            result = await temporal_agent.run(prompt, model=fast_model)
        else:
            # Or pass a model string (uses provider_factory if set)
            result = await temporal_agent.run(prompt, model='openai:gpt-5-mini')
        return result.output
```

## Activity 配置 {#activity-configuration}

Temporal activity 配置（如 timeouts 和 retry policies）可以通过向 `TemporalAgent` 构造函数传入 [`temporalio.workflow.ActivityConfig`](https://python.temporal.io/temporalio.workflow.ActivityConfig.html) 对象来定制：

- `activity_config`：所有 activities 使用的基础 Temporal activity config。如果不提供 config，会使用 60 秒的 `start_to_close_timeout`。
- `model_activity_config`：模型请求 activities 使用的 Temporal activity config。它会与基础 activity config 合并。
- `toolset_activity_config`：特定 toolsets（按 ID 标识）的 get-tools 和 call-tool activities 使用的 Temporal activity config。它会与基础 activity config 合并。
- `tool_activity_config`：特定 tool call activities（按 toolset ID 和 tool name 标识）使用的 Temporal activity config。
    它会与基础和 toolset-specific activity configs 合并。

    如果某个工具不使用 I/O，可以指定 `False` 来禁用 activity。注意，该工具必须定义为 `async` 函数，因为非 async 工具会在线程中运行，而线程是非确定性的，因此不支持在 activities 外运行。

## Activity 重试 {#activity-retries}

除了 Temporal 会执行的请求失败自动重试之外，Pydantic AI 和各种 provider API clients 也有自己的请求重试逻辑。同时启用这些机制，可能会导致请求重试次数超出预期，并且 `Retry-After` 处理不正确。

使用 Temporal 时，建议不要使用 [HTTP Request Retries](../retries.md)，并关闭 provider API client 自身的重试逻辑，例如在[自定义 `OpenAIProvider` API client](../models/openai.md#custom-openai-client) 上设置 `max_retries=0`。

你可以使用 [activity 配置](#activity-configuration)自定义 Temporal 的 retry policy。

## 使用 Logfire 进行可观测性 {#observability-with-logfire}

Temporal 会为每次 workflow 和 activity 执行生成 telemetry events 和 metrics，Pydantic AI 会为每次 agent run、模型请求和工具调用生成 events。这些都可以发送到 [Pydantic Logfire](../logfire.md)，以完整了解应用中正在发生的事情。

要将 Logfire 与 Temporal 一起使用，需要向 Temporal 的 `Client.connect()` 传入 [`LogfirePlugin`][pydantic_ai.durable_exec.temporal.LogfirePlugin] 对象：

```py {title="logfire_plugin.py" test="skip" noqa="F841"}
from temporalio.client import Client

from pydantic_ai.durable_exec.temporal import LogfirePlugin, PydanticAIPlugin


async def main():
    client = await Client.connect(
        'localhost:7233',
        plugins=[PydanticAIPlugin(), LogfirePlugin()],
    )
```

默认情况下，`LogfirePlugin` 会为 Temporal（包括 metrics）和 Pydantic AI 插桩，并把所有数据发送到 Logfire。要自定义 Logfire 配置和插桩，可以向 `LogfirePlugin` 构造函数传入 `logfire_setup` 函数，并返回一个自定义 `Logfire` 实例（即 `logfire.configure()` 的结果）。要禁用向 Logfire 发送 Temporal metrics，可以向 `LogfirePlugin` 构造函数传入 `metrics=False`。

## 已知问题 {#known-issues}

### Pandas

当在 activity 内使用 `logfire.info`，且 `pandas` 包位于项目依赖中时，你可能会遇到下面这个错误，看起来是 import race condition 导致的：

```
AttributeError: partially initialized module 'pandas' has no attribute '_pandas_parser_CAPI' (most likely due to a circular import)
```

要修复这个问题，可以使用 [`temporalio.workflow.unsafe.imports_passed_through()`](https://python.temporal.io/temporalio.workflow.unsafe.html#imports_passed_through) context manager 主动导入该包，并避免它在 workflow sandbox 中被重新加载：

```python {title="temporal_activity.py" test="skip" noqa="F401"}
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    import pandas
```
