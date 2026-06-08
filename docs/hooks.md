
# Hooks

Hooks 让你可以在一次运行的每个阶段拦截和修改智能体行为，包括模型请求、工具调用、流式事件等；可以使用简单的装饰器或构造参数完成，不需要子类化。

[`Hooks`][pydantic_ai.capabilities.Hooks] capability 是添加[生命周期 hooks](capabilities.md#hooking-into-the-lifecycle) 的推荐方式，适合日志、指标、轻量验证等应用层关注点。对于把 hooks 与工具、instructions 或模型设置组合起来的可复用 capability，请改为继承 [`AbstractCapability`][pydantic_ai.capabilities.AbstractCapability]，参见[构建自定义 capabilities](capabilities.md#building-custom-capabilities)。

## 快速开始

创建一个 [`Hooks`][pydantic_ai.capabilities.Hooks] 实例，通过 `@hooks.on.*` 装饰器注册 hooks，然后把它传给智能体：

```python {title="hooks_decorator.py"}
from pydantic_ai import Agent, ModelRequestContext, RunContext
from pydantic_ai.capabilities import Hooks

hooks = Hooks()


@hooks.on.before_model_request
async def log_request(ctx: RunContext[None], request_context: ModelRequestContext) -> ModelRequestContext:
    print(f'Sending {len(request_context.messages)} messages to the model')
    #> Sending 1 messages to the model
    return request_context


agent = Agent('test', capabilities=[hooks])
result = agent.run_sync('Hello!')
print(result.output)
#> success (no tool calls)
```

## 注册 hooks

### 装饰器注册

`hooks.on` 命名空间为每种生命周期 hook 提供装饰器方法。它们既可以作为裸装饰器使用，也可以带参数使用：

```python {test="skip" lint="skip"}
# Bare decorator
@hooks.on.before_model_request
async def my_hook(ctx, request_context):
    return request_context

# With parameters (timeout, tool filter)
@hooks.on.before_model_request(timeout=5.0)
async def my_timed_hook(ctx, request_context):
    return request_context
```

同一个事件可以注册多个 hooks，它们会按注册顺序触发。

### 构造函数 kwargs

你也可以把 hook 函数直接传给 [`Hooks`][pydantic_ai.capabilities.Hooks] 构造函数：

```python {title="hooks_constructor.py"}
from pydantic_ai import Agent, ModelRequestContext, RunContext
from pydantic_ai.capabilities import Hooks


async def log_request(ctx: RunContext[None], request_context: ModelRequestContext) -> ModelRequestContext:
    print(f'Sending {len(request_context.messages)} messages to the model')
    #> Sending 1 messages to the model
    return request_context


agent = Agent('test', capabilities=[Hooks(before_model_request=log_request)])
result = agent.run_sync('Hello!')
print(result.output)
#> success (no tool calls)
```

同步和异步 hook 函数都可以使用。同步函数会自动包装为异步执行。

## Hook 类型

### Run hooks

| `hooks.on.` | 构造函数 kwarg | `AbstractCapability` 方法 |
|---|---|---|
| `before_run` | `before_run=` | `before_run` |
| `after_run` | `after_run=` | `after_run` |
| `run` | `run=` | `wrap_run` |
| `run_error` | `run_error=` | `on_run_error` |

Run hooks 在每次智能体运行时触发一次。`wrap_run`（通过 `hooks.on.run` 注册）会包装整个运行过程，并支持错误恢复。

### Node hooks

| `hooks.on.` | 构造函数 kwarg | `AbstractCapability` 方法 |
|---|---|---|
| `before_node_run` | `before_node_run=` | `before_node_run` |
| `after_node_run` | `after_node_run=` | `after_node_run` |
| `node_run` | `node_run=` | `wrap_node_run` |
| `node_run_error` | `node_run_error=` | `on_node_run_error` |

Node hooks 会在每个图步骤触发（[`UserPromptNode`][pydantic_ai.UserPromptNode]、[`ModelRequestNode`][pydantic_ai.ModelRequestNode]、[`CallToolsNode`][pydantic_ai.CallToolsNode]）。

!!! note
    `wrap_node_run` hooks 会由 [`agent.run()`][pydantic_ai.agent.AbstractAgent.run]、[`agent.run_stream()`][pydantic_ai.agent.AbstractAgent.run_stream] 和 [`agent_run.next()`][pydantic_ai.run.AgentRun.next] 自动调用，但在用裸 `async for node in agent_run:` 迭代时**不会**调用。

### 模型请求 hooks

| `hooks.on.` | 构造函数 kwarg | `AbstractCapability` 方法 |
|---|---|---|
| `before_model_request` | `before_model_request=` | `before_model_request` |
| `after_model_request` | `after_model_request=` | `after_model_request` |
| `model_request` | `model_request=` | `wrap_model_request` |
| `model_request_error` | `model_request_error=` | `on_model_request_error` |

模型请求 hooks 会围绕每次 LLM 调用触发。[`ModelRequestContext`][pydantic_ai.models.ModelRequestContext] 会打包 `model`、`messages`、`model_settings` 和 `model_request_parameters`。要为某个请求替换模型，请把 `request_context.model` 设置为另一个 [`Model`][pydantic_ai.models.Model] 实例。

要完全跳过模型调用，请从 `before_model_request` 或 `model_request`（wrap）抛出 [`SkipModelRequest(response)`][pydantic_ai.exceptions.SkipModelRequest]。

### 工具验证 hooks

| `hooks.on.` | 构造函数 kwarg | `AbstractCapability` 方法 |
|---|---|---|
| `before_tool_validate` | `before_tool_validate=` | `before_tool_validate` |
| `after_tool_validate` | `after_tool_validate=` | `after_tool_validate` |
| `tool_validate` | `tool_validate=` | `wrap_tool_validate` |
| `tool_validate_error` | `tool_validate_error=` | `on_tool_validate_error` |

当模型的 JSON 参数被解析和验证时，会触发验证 hooks。所有工具 hooks 都会接收 `call`（[`ToolCallPart`][pydantic_ai.messages.ToolCallPart]）和 `tool_def`（[`ToolDefinition`][pydantic_ai.tools.ToolDefinition]）参数。

!!! note
    工具验证和执行 hooks 只会对 function tools 触发。内部 output tools（用于交付结构化输出）不是面向用户的工具，因此会跳过。

要跳过验证，请从 `before_tool_validate` 或 `tool_validate`（wrap）抛出 [`SkipToolValidation(args)`][pydantic_ai.exceptions.SkipToolValidation]。

### 工具执行 hooks

| `hooks.on.` | 构造函数 kwarg | `AbstractCapability` 方法 |
|---|---|---|
| `before_tool_execute` | `before_tool_execute=` | `before_tool_execute` |
| `after_tool_execute` | `after_tool_execute=` | `after_tool_execute` |
| `tool_execute` | `tool_execute=` | `wrap_tool_execute` |
| `tool_execute_error` | `tool_execute_error=` | `on_tool_execute_error` |

当工具函数运行时，会触发执行 hooks。`args` 始终是验证后的 `dict[str, Any]`。

要跳过执行，请从 `before_tool_execute` 或 `tool_execute`（wrap）抛出 [`SkipToolExecution(result)`][pydantic_ai.exceptions.SkipToolExecution]。

### 输出验证 hooks

| `hooks.on.` | 构造函数 kwarg | `AbstractCapability` 方法 |
|---|---|---|
| `before_output_validate` | `before_output_validate=` | `before_output_validate` |
| `after_output_validate` | `after_output_validate=` | `after_output_validate` |
| `output_validate` | `output_validate=` | `wrap_output_validate` |
| `output_validate_error` | `output_validate_error=` | `on_output_validate_error` |

当结构化输出按输出 schema 解析时，会触发输出验证 hooks。它们不会对纯文本或图像输出触发。所有输出 hooks 都会接收 `output_context`（[`OutputContext`][pydantic_ai.capabilities.OutputContext]）参数。

!!! note
    在流式输出期间，输出**验证** hooks 会在每次部分验证尝试以及最终结果时触发。输出**处理** hooks 只会在部分验证成功时以及最终结果时触发。在 hooks 中检查 `ctx.partial_output`，以区分部分结果和最终结果，并避免在部分结果上执行昂贵工作。

### 输出处理 hooks

| `hooks.on.` | 构造函数 kwarg | `AbstractCapability` 方法 |
|---|---|---|
| `before_output_process` | `before_output_process=` | `before_output_process` |
| `after_output_process` | `after_output_process=` | `after_output_process` |
| `output_process` | `output_process=` | `wrap_output_process` |
| `output_process_error` | `output_process_error=` | `on_output_process_error` |

当输出被处理时，会触发输出处理 hooks，包括提取值、调用输出函数以及运行输出验证器。

完整生命周期、签名，以及输出验证器如何与处理 hooks 交互，请参阅[输出 hooks](capabilities.md#output-hooks)。

### 工具准备

| `hooks.on.` | 构造函数 kwarg | `AbstractCapability` 方法 |
|---|---|---|
| `prepare_tools` | `prepare_tools=` | `prepare_tools` |
| `prepare_output_tools` | `prepare_output_tools=` | `prepare_output_tools` |

过滤或修改模型在每一步看到的工具定义。

`prepare_tools` 处理 **function** tools；`prepare_output_tools` 单独处理 [output tools][pydantic_ai.output.ToolOutput]，其中 `ctx.max_retries` 反映的是**输出**重试预算。二者都以 `PreparedToolset` 包装器形式运行，结果会同时流入模型请求和 `ToolManager.tools`，因此过滤也会阻止工具执行。

### 延迟工具调用 hook {#deferred-tool-call-hook}

| `hooks.on.` | 构造函数 kwarg | `AbstractCapability` 方法 |
|---|---|---|
| `deferred_tool_calls` | `deferred_tool_calls=` | `handle_deferred_tool_calls` |

在一次运行中内联解析[延迟工具调用](deferred-tools.md)（需要批准或外部执行）。该 hook 接收 [`DeferredToolRequests`][pydantic_ai.tools.DeferredToolRequests]，并返回 [`DeferredToolResults`][pydantic_ai.tools.DeferredToolResults]（或返回 `None` 表示拒绝处理）。多个已注册 hooks 会累积执行：每个 hook 都会接收仍未解析的请求，并可以解析其中一部分或全部。

```python {title="hooks_deferred_tool_calls.py"}
from pydantic_ai import Agent, DeferredToolRequests, DeferredToolResults, RunContext
from pydantic_ai.capabilities import Hooks

hooks = Hooks()


@hooks.on.deferred_tool_calls
async def auto_approve(
    ctx: RunContext[None], *, requests: DeferredToolRequests
) -> DeferredToolResults:
    return requests.build_results(approve_all=True)


agent = Agent('test', capabilities=[hooks])


@agent.tool_plain(requires_approval=True)
def delete_file(path: str) -> str:
    return f'File {path!r} deleted'
```

如果只是为应用层注册处理器，而不需要其他 hooks，专用的 [`HandleDeferredToolCalls`][pydantic_ai.capabilities.HandleDeferredToolCalls] capability 会更简洁；参见[使用处理器解析延迟调用](deferred-tools.md#resolving-deferred-calls-with-a-handler)。

### 事件流 hooks

| `hooks.on.` | 构造函数 kwarg | `AbstractCapability` 方法 |
|---|---|---|
| `run_event_stream` | `run_event_stream=` | `wrap_run_event_stream` |
| `event` | `event=` | _（逐事件便利形式）_ |

`run_event_stream` 会以异步生成器形式包装完整事件流。`event` 是一种便利形式，会在流式运行期间针对每个单独事件触发：

```python {title="hooks_event.py"}
from pydantic_ai import Agent, AgentStreamEvent, RunContext
from pydantic_ai.capabilities import Hooks

hooks = Hooks()
event_count = 0


@hooks.on.event
async def count_events(ctx: RunContext[None], event: AgentStreamEvent) -> AgentStreamEvent:
    global event_count
    event_count += 1
    return event


agent = Agent('test', capabilities=[hooks])
```

## 工具 hook 过滤

工具 hooks（验证和执行）支持 `tools` 参数，可按名称定位特定工具：

```python {title="hooks_tool_filter.py"}
from typing import Any

from pydantic_ai import Agent, RunContext, ToolDefinition
from pydantic_ai.capabilities import Hooks
from pydantic_ai.messages import ToolCallPart

hooks = Hooks()
call_log: list[str] = []


@hooks.on.before_tool_execute(tools=['send_email'])
async def audit_dangerous_tools(
    ctx: RunContext[None],
    *,
    call: ToolCallPart,
    tool_def: ToolDefinition,
    args: dict[str, Any],
) -> dict[str, Any]:
    call_log.append(f'audit: {call.tool_name}')
    return args


agent = Agent('test', capabilities=[hooks])


@agent.tool_plain
def send_email(to: str) -> str:
    return f'sent to {to}'


result = agent.run_sync('Send an email to test@example.com')
print(call_log)
#> ['audit: send_email']
```

`tools` 参数接受一个工具名称序列。hook 只会对匹配的工具触发，其他工具调用会不受影响地通过。

## 超时

每个 hook 都支持可选的 `timeout`，单位为秒。如果 hook 超过该超时时间，会抛出 [`HookTimeoutError`][pydantic_ai.capabilities.HookTimeoutError]：

```python {title="hooks_timeout.py"}
import asyncio

from pydantic_ai import Agent, ModelRequestContext, RunContext
from pydantic_ai.capabilities import Hooks, HookTimeoutError

hooks = Hooks()


@hooks.on.before_model_request(timeout=0.01)
async def slow_hook(
    ctx: RunContext[None], request_context: ModelRequestContext
) -> ModelRequestContext:
    await asyncio.sleep(10)  # Will be interrupted by timeout
    return request_context  # pragma: no cover


agent = Agent('test', capabilities=[hooks])
try:
    agent.run_sync('Hello')
except HookTimeoutError as e:
    print(f'Hook timed out: {e.hook_name} after {e.timeout}s')
    #> Hook timed out: before_model_request after 0.01s
```

超时可以通过装饰器参数（`@hooks.on.before_model_request(timeout=5.0)`）设置，也可以在使用 kwargs 时通过构造函数设置。

## Wrap hooks

Wrap hooks 让你可以用设置/清理逻辑包围某个操作。在 `hooks.on` 命名空间中，wrap hooks 会去掉 `wrap_` 前缀；`hooks.on.model_request` 对应 `wrap_model_request`：

```python {title="hooks_wrap.py"}
from pydantic_ai import Agent, ModelRequestContext, RunContext
from pydantic_ai.capabilities import Hooks, WrapModelRequestHandler
from pydantic_ai.messages import ModelResponse

hooks = Hooks()
wrap_log: list[str] = []


@hooks.on.model_request
async def log_request(
    ctx: RunContext[None], *, request_context: ModelRequestContext, handler: WrapModelRequestHandler
) -> ModelResponse:
    wrap_log.append('before')
    response = await handler(request_context)
    wrap_log.append('after')
    return response


agent = Agent('test', capabilities=[hooks])
result = agent.run_sync('Hello!')
print(wrap_log)
#> ['before', 'after']
```

## Hook 顺序

当多个 hooks 注册到同一事件时（无论是在同一个 `Hooks` 实例上，还是跨多个 capabilities）：

* **`before_*`** hooks 按注册/capability 顺序触发
* **`after_*`** hooks 按反向顺序触发
* **`wrap_*`** hooks 像中间件一样嵌套；第一个注册的 hook 是最外层

多个 capabilities 的 hooks 如何交互，详见[组合](capabilities.md#composition)。

## 错误 hooks

错误 hooks（`hooks.on` 命名空间中的 `*_error`，以及 `AbstractCapability` 上的 `on_*_error`）采用**抛出即传播，返回即恢复**的语义：

- **抛出原始错误** - 原样传播（默认）
- **抛出另一个异常** - 转换错误
- **返回结果** - 抑制错误

完整模式和恢复类型请参阅[错误 hooks](capabilities.md#error-hooks)。

## 使用 `ModelRetry` 触发重试 {#triggering-retries-with-modelretry}

Hooks 可以抛出 [`ModelRetry`][pydantic_ai.exceptions.ModelRetry]，要求模型带着自定义消息重试。这与[工具函数](tools.md#model-retry)和输出验证器中使用的是同一个异常。

**模型请求 hooks**（`after_model_request`、`wrap_model_request`、`on_model_request_error`）：

- 重试消息会作为 [`RetryPromptPart`][pydantic_ai.messages.RetryPromptPart] 发回给模型
- `after_model_request`：原始响应会保留在消息历史中，因此模型能看到自己刚才说了什么
- `wrap_model_request`：只有调用了 handler 时，响应才会保留
- 重试计入智能体输出侧的重试预算

**工具 hooks**（`before/after_tool_validate`、`before/after_tool_execute`、`wrap_tool_execute`、`on_tool_execute_error`）：

- 会转换为工具重试提示，与工具函数抛出 `ModelRetry` 时相同
- 重试计入工具的 `max_retries` 限制

**输出 hooks**（`before/after_output_validate`、`before/after_output_process`、`wrap_output_process`、`on_output_process_error`）：

- 会转换为重试提示，与输出函数抛出 `ModelRetry` 时相同
- 对于工具输出，重试计入工具的 `max_retries` 限制
- 对于文本输出，重试计入智能体输出侧的重试预算

来自 `wrap_model_request`、`wrap_tool_execute` 和 `wrap_output_process` 的 `ModelRetry` 会被视为控制流，因此会绕过对应的 `on_*_error` hook。

```python {title="hooks_model_retry.py"}
from pydantic_ai import Agent, RunContext
from pydantic_ai.capabilities import Hooks
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.messages import ModelResponse
from pydantic_ai.models import ModelRequestContext

hooks = Hooks()


@hooks.on.after_model_request
async def check_response(
    ctx: RunContext[None],
    *,
    request_context: ModelRequestContext,
    response: ModelResponse,
) -> ModelResponse:
    if 'PLACEHOLDER' in str(response.parts):
        raise ModelRetry('Response contains placeholder text. Please provide real data.')
    return response


agent = Agent('test', capabilities=[hooks])
result = agent.run_sync('Hello')
print(result.output)
#> success (no tool calls)
```

## 何时使用 `Hooks`，何时使用 `AbstractCapability`

| 使用 [`Hooks`][pydantic_ai.capabilities.Hooks] | 使用 [`AbstractCapability`][pydantic_ai.capabilities.AbstractCapability] |
|---|---|
| 应用层 hooks（日志、指标） | 可复用、可打包的 capabilities |
| 快速的一次性拦截器 | 工具 + hooks + instructions + settings 的组合 |
| 不需要配置状态 | 复杂的逐运行状态管理 |
| 单文件脚本 | 多智能体共享行为 |
