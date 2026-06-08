# Agent-User Interaction（AG-UI）协议

[Agent-User Interaction（AG-UI）Protocol](https://docs.ag-ui.com/introduction) 是一个开放标准，由
[CopilotKit](https://webflow.copilotkit.ai/blog/introducing-ag-ui-the-protocol-where-agents-meet-users)
团队提出，用于标准化前端应用如何与 AI agents 通信，并支持 streaming、frontend tools、shared state 和 custom events。

!!! note
    AG-UI 集成最初由 [Rocket Science](https://www.rocketscience.gg/) 团队构建，并与 Pydantic AI 和 CopilotKit 团队协作贡献。感谢 Rocket Science！

!!! warning "正在使用 1.x 并迁移到 2.0？"
    [`Agent.to_ag_ui()`][pydantic_ai.agent.AbstractAgent.to_ag_ui]、[`AGUIApp`][pydantic_ai.ui.ag_ui.app.AGUIApp] 和 `pydantic_ai.ag_ui` shim module 在 1.x 中已弃用，并将在 2.0 中移除。请直接跳到页面底部的[从已弃用 API 迁移](#migrating-from-deprecated-apis)，查看 before/after 示例。

## 安装 {#installation}

唯一依赖是：

- [ag-ui-protocol](https://docs.ag-ui.com/introduction)：提供 AG-UI 类型和 encoder。
- [starlette](https://www.starlette.io)：处理来自 FastAPI 等框架的 [ASGI](https://asgi.readthedocs.io/en/latest/) 请求。

你可以安装带 `ag-ui` extra 的 Pydantic AI，以确保拥有所有必需的 AG-UI 依赖：

```bash
pip/uv-add 'pydantic-ai-slim[ag-ui]'
```

要运行示例，还需要：

- [uvicorn](https://www.uvicorn.org/) 或其他 ASGI 兼容服务器

```bash
pip/uv-add uvicorn
```

## 用法 {#usage}

有三种方式可以基于 AG-UI run input 运行 Pydantic AI agent，并以流式 AG-UI events 作为输出；从最灵活到最简便依次如下。如果你使用的是基于 Starlette 的 Web 框架（如 FastAPI），通常会选择第二种方式。

1. 在用 agent 和 AG-UI [`RunAgentInput`](https://docs.ag-ui.com/sdk/python/core/types#runagentinput) 对象实例化的 [`AGUIAdapter`][pydantic_ai.ui.ag_ui.AGUIAdapter] 上调用 [`AGUIAdapter.run_stream()`][pydantic_ai.ui.ag_ui.AGUIAdapter.run_stream] 方法，会运行 agent 并返回 AG-UI events 流。它还接受可选的 [`Agent.iter()`][pydantic_ai.agent.Agent.iter] 参数，包括 `deps`。如果你使用的 Web 框架不是基于 Starlette（例如 Django 或 Flask），或想以某种方式修改输入或输出，请使用这种方式。
2. [`AGUIAdapter.dispatch_request()`][pydantic_ai.ui.ag_ui.AGUIAdapter.dispatch_request] 类方法接收一个 agent 和来自 AG-UI 前端的 Starlette request（例如 FastAPI 中的 request），并返回一个可直接从 endpoint 返回的 AG-UI events 流式 Starlette response。它也接受可选的 [`Agent.iter()`][pydantic_ai.agent.Agent.iter] 参数，包括 `deps`，你可以对每个请求使用不同的值（例如基于已认证用户）。这是一个便利方法，组合了 [`AGUIAdapter.from_request()`][pydantic_ai.ui.ag_ui.AGUIAdapter.from_request]、[`AGUIAdapter.run_stream()`][pydantic_ai.ui.ag_ui.AGUIAdapter.run_stream] 和 [`AGUIAdapter.streaming_response()`][pydantic_ai.ui.ag_ui.AGUIAdapter.streaming_response]。
3. 构建一个独立的 [`Starlette`](https://www.starlette.io/applications/) app，其中只有一个 `/` route 调用 [`AGUIAdapter.dispatch_request()`][pydantic_ai.ui.ag_ui.AGUIAdapter.dispatch_request]。同一个 Starlette app 可以[挂载](https://fastapi.tiangolo.com/advanced/sub-applications/)到现有 FastAPI app 的某个路径上。

### 直接处理 run input 和 output {#handle-run-input-and-output-directly}

这个示例使用 [`AGUIAdapter.run_stream()`][pydantic_ai.ui.ag_ui.AGUIAdapter.run_stream]，并自行完成请求解析和响应生成。
它可以修改为适配任何 Web 框架。

```py {title="run_ag_ui.py"}
import json
from http import HTTPStatus

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response, StreamingResponse
from pydantic import ValidationError

from pydantic_ai import Agent
from pydantic_ai.ui import SSE_CONTENT_TYPE
from pydantic_ai.ui.ag_ui import AGUIAdapter

agent = Agent('openai:gpt-5.2', instructions='Be fun!')

app = FastAPI()


@app.post('/')
async def run_agent(request: Request) -> Response:
    accept = request.headers.get('accept', SSE_CONTENT_TYPE)
    try:
        run_input = AGUIAdapter.build_run_input(await request.body())  # (1)
    except ValidationError as e:
        return Response(
            content=json.dumps(e.json()),
            media_type='application/json',
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    adapter = AGUIAdapter(agent=agent, run_input=run_input, accept=accept)
    event_stream = adapter.run_stream() # (2)

    sse_event_stream = adapter.encode_stream(event_stream)
    return StreamingResponse(sse_event_stream, media_type=accept) # (3)
```

1. [`AGUIAdapter.build_run_input()`][pydantic_ai.ui.ag_ui.AGUIAdapter.build_run_input] 接收 request body bytes，并返回 AG-UI [`RunAgentInput`](https://docs.ag-ui.com/sdk/python/core/types#runagentinput) 对象。你也可以使用 [`AGUIAdapter.from_request()`][pydantic_ai.ui.ag_ui.AGUIAdapter.from_request] 类方法，直接从 request 构建 adapter。
2. [`AGUIAdapter.run_stream()`][pydantic_ai.ui.ag_ui.AGUIAdapter.run_stream] 运行 agent 并返回 AG-UI events 流。它支持与 [`Agent.run_stream_events()`](../agent.md#running-agents) 相同的可选参数，包括 `deps`。你也可以使用 [`AGUIAdapter.run_stream_native()`][pydantic_ai.ui.ag_ui.AGUIAdapter.run_stream_native] 运行 agent 并返回 Pydantic AI events 流，然后使用 [`AGUIAdapter.transform_stream()`][pydantic_ai.ui.ag_ui.AGUIAdapter.transform_stream] 将其转换为 AG-UI events。
3. [`AGUIAdapter.encode_stream()`][pydantic_ai.ui.ag_ui.AGUIAdapter.encode_stream] 根据 accept header 的值，将 AG-UI events 流编码为字符串。你也可以使用 [`AGUIAdapter.streaming_response()`][pydantic_ai.ui.ag_ui.AGUIAdapter.streaming_response]，直接从 `run_stream()` 返回的 AG-UI event stream 生成流式 response。

由于 `app` 是 ASGI application，可与任何 ASGI server 一起使用：

```shell
uvicorn run_ag_ui:app
```

这会把 agent 暴露为 AG-UI server，你的前端就可以开始向它发送请求。

### 处理 Starlette request {#handle-a-starlette-request}

这个示例使用 [`AGUIAdapter.dispatch_request()`][pydantic_ai.ui.ag_ui.AGUIAdapter.dispatch_request] 直接处理 FastAPI request 并返回 response。任何基于 Starlette 的 Web 框架都可以使用类似方式。

```py {title="handle_ag_ui_request.py"}
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui import AGUIAdapter

agent = Agent('openai:gpt-5.2', instructions='Be fun!')

app = FastAPI()

@app.post('/')
async def run_agent(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=agent) # (1)
```

1. 这个方法本质上与上一个示例相同，但当你已经使用 Starlette/FastAPI app 时更方便。

由于 `app` 是 ASGI application，可与任何 ASGI server 一起使用：

```shell
uvicorn handle_ag_ui_request:app
```

这会把 agent 暴露为 AG-UI server，你的前端就可以开始向它发送请求。

### 独立 ASGI app {#stand-alone-asgi-app}

如果你还没有可挂载 route 的 Starlette/FastAPI app，可以构建一个最小 [`Starlette`](https://www.starlette.io/applications/) app，让它唯一的 `/` route 调用 [`AGUIAdapter.dispatch_request()`][pydantic_ai.ui.ag_ui.AGUIAdapter.dispatch_request]：

```py {title="ag_ui_app.py"}
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui import AGUIAdapter

agent = Agent('openai:gpt-5.2', instructions='Be fun!')


async def run_agent(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=agent)


app = Starlette(routes=[Route('/', run_agent, methods=['POST'])])
```

由于 `app` 是 ASGI application，可与任何 ASGI server 一起使用：

```shell
uvicorn ag_ui_app:app
```

这会把 agent 暴露为 AG-UI server，你的前端就可以开始向它发送请求。

## 设计 {#design}

Pydantic AI AG-UI 集成支持该 spec 的所有功能：

- [Events](https://docs.ag-ui.com/concepts/events)
- [Messages](https://docs.ag-ui.com/concepts/messages)
- [State Management](https://docs.ag-ui.com/concepts/state)
- [Tools](https://docs.ag-ui.com/concepts/tools)

该集成以
[`RunAgentInput`](https://docs.ag-ui.com/sdk/python/core/types#runagentinput) 对象形式接收 messages，
该对象描述所请求 agent run 的细节，包括 message history、state 和 available tools。

这些内容会转换为 Pydantic AI 类型，并传给 agent 的 run 方法。来自 agent 的事件（包括 tool calls）会转换为 AG-UI events，并以 Server-Sent Events（SSE）的形式流回调用方。

根据所需 tools 和 events 的不同，一个用户请求可能需要在 client UI 和 Pydantic AI server 之间进行多次往返。

## 功能 {#features}

### State management {#state-management}

该集成为 [AG-UI state management](https://docs.ag-ui.com/concepts/state) 提供完整支持，从而支持 agents 与前端应用之间的实时同步。

下面示例中有一个 document state，它在 UI 和 server 之间共享；示例使用 [`StateDeps`][pydantic_ai.ui.StateDeps] [dependencies type](../dependencies.md)，可以通过作为泛型参数指定的 Pydantic `BaseModel` 自动验证 [`RunAgentInput.state`](https://docs.ag-ui.com/sdk/js/core/types#runagentinput) 中包含的 state。

!!! note "带 AG-UI state 的自定义 dependencies type"
    如果你希望用自己的 dependencies type 同时保存 AG-UI state 和其他内容，它需要实现
    [`StateHandler`][pydantic_ai.ui.StateHandler] protocol，也就是说它需要是一个带有非可选 `state` 字段的 [dataclass](https://docs.python.org/3/library/dataclasses.html)。这让 Pydantic AI 能通过每次构建新的 dependencies 对象，确保 state 在请求之间正确隔离。

    如果 `state` 字段的类型是 Pydantic `BaseModel` 子类，请求中的原始 state dictionary 会自动验证。否则，你可以在 dependencies dataclass 的 `__post_init__` 方法中自行验证原始值。

    如果提供了 AG-UI state，但你的 dependencies 没有实现 [`StateHandler`][pydantic_ai.ui.StateHandler]，Pydantic AI 会发出警告并忽略该 state。请使用 [`StateDeps`][pydantic_ai.ui.StateDeps] 或自定义 [`StateHandler`][pydantic_ai.ui.StateHandler] 实现来接收并验证传入 state。


```python {title="ag_ui_state.py"}
from dataclasses import replace

from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from pydantic_ai import Agent
from pydantic_ai.ui import StateDeps
from pydantic_ai.ui.ag_ui import AGUIAdapter


class DocumentState(BaseModel):
    """State for the document being written."""

    document: str = ''


agent = Agent(
    'openai:gpt-5.2',
    instructions='Be fun!',
    deps_type=StateDeps[DocumentState],
)
deps = StateDeps(DocumentState())


async def run_agent(request: Request) -> Response:
    # `dispatch_request` mutates `deps.state` from the request, so give each request its own copy.
    return await AGUIAdapter.dispatch_request(request, agent=agent, deps=replace(deps))


app = Starlette(routes=[Route('/', run_agent, methods=['POST'])])
```

由于 `app` 是 ASGI application，可与任何 ASGI server 一起使用：

```bash
uvicorn ag_ui_state:app --host 0.0.0.0 --port 9000
```

### Tools

AG-UI frontend tools 会无缝提供给 Pydantic AI agent，从而支持带前端用户界面的丰富用户体验。

### Events

Pydantic AI tools 只需返回一个
[`ToolReturn`](../tools-advanced.md#advanced-tool-returns) 对象，并把
[`BaseEvent`](https://docs.ag-ui.com/sdk/python/core/events#baseevent)（或 events 列表）放在 `metadata` 中，就可以发送 [AG-UI events](https://docs.ag-ui.com/concepts/events)，从而支持 custom events 和 state updates。

```python {title="ag_ui_tool_events.py"}
from dataclasses import replace

from ag_ui.core import CustomEvent, EventType, StateSnapshotEvent
from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from pydantic_ai import Agent, RunContext, ToolReturn
from pydantic_ai.ui import StateDeps
from pydantic_ai.ui.ag_ui import AGUIAdapter


class DocumentState(BaseModel):
    """State for the document being written."""

    document: str = ''


agent = Agent(
    'openai:gpt-5.2',
    instructions='Be fun!',
    deps_type=StateDeps[DocumentState],
)
deps = StateDeps(DocumentState())


async def run_agent(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=agent, deps=replace(deps))


app = Starlette(routes=[Route('/', run_agent, methods=['POST'])])


@agent.tool
async def update_state(ctx: RunContext[StateDeps[DocumentState]]) -> ToolReturn:
    return ToolReturn(
        return_value='State updated',
        metadata=[
            StateSnapshotEvent(
                type=EventType.STATE_SNAPSHOT,
                snapshot=ctx.deps.state,
            ),
        ],
    )


@agent.tool_plain
async def custom_events() -> ToolReturn:
    return ToolReturn(
        return_value='Count events sent',
        metadata=[
            CustomEvent(
                type=EventType.CUSTOM,
                name='count',
                value=1,
            ),
            CustomEvent(
                type=EventType.CUSTOM,
                name='count',
                value=2,
            ),
        ]
    )
```

由于 `app` 是 ASGI application，可与任何 ASGI server 一起使用：

```bash
uvicorn ag_ui_tool_events:app --host 0.0.0.0 --port 9000
```

### 信任模型 {#trust-model}

AG-UI 的 `RunAgentInput.messages` 完全由 client 控制。[`AGUIAdapter`][pydantic_ai.ui.ag_ui.AGUIAdapter] 会默认剥离不可信 parts 后再运行 agent；请参阅 UI adapter 概览中的[客户端提交 messages 的信任模型](./overview.md#trust-model-for-client-submitted-messages)。

### System prompts 与 instructions {#system-prompts-and-instructions}

Pydantic AI 支持两种向模型提供指引的方式：[`system_prompt`](../agent.md#system-prompts)（作为 [`SystemPromptPart`][pydantic_ai.messages.SystemPromptPart]s 存储在消息历史中）和 [`instructions`](../agent.md#instructions)（每次请求都重新注入，永不持久化）。当你控制服务端时，推荐默认使用 `instructions`。

本节其余内容只在你使用 `system_prompt` 时有意义。如果你只使用 `instructions`，无需任何配置，它们总会应用，不受 AG-UI message history 影响。

对于 `system_prompt`，你可以通过 [`AGUIAdapter`][pydantic_ai.ui.ag_ui.AGUIAdapter] 上的 `manage_system_prompt` 参数选择由谁持有它：

- `'server'`（默认）：agent 配置的 `system_prompt` 是权威来源。前端发送的任何 `SystemMessage` 都会被剥离并发出警告（否则恶意 client 可以通过构造 API 请求注入任意 instructions），agent 自己的 system prompt 会通过 [`ReinjectSystemPrompt`][pydantic_ai.capabilities.ReinjectSystemPrompt] capability 重新注入到第一次请求的开头。
- `'client'`：前端持有 system prompt。前端 `SystemMessage`s 会原样保留，agent 配置的 `system_prompt` 不会注入；如果需要，调用方完全负责在每一轮都发送它。若要选择回退到已配置行为，请向 agent 添加 [`ReinjectSystemPrompt`][pydantic_ai.capabilities.ReinjectSystemPrompt] capability。

```python {title="ag_ui_client_managed_system_prompt.py"}
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui import AGUIAdapter

agent = Agent('openai:gpt-5.2')

app = FastAPI()


@app.post('/')
async def run_agent(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(
        request, agent=agent, manage_system_prompt='client'
    )
```

## 示例 {#examples}

更多示例见
[`pydantic_ai_examples.ag_ui`](https://github.com/pydantic/pydantic-ai/tree/main/examples/pydantic_ai_examples/ag_ui)，
其中包含一个可与
[AG-UI Dojo](https://docs.ag-ui.com/tutorials/debugging#the-ag-ui-dojo) 配合使用的 server。

## 从已弃用 API 迁移 {#migrating-from-deprecated-apis}

[`Agent.to_ag_ui()`][pydantic_ai.agent.AbstractAgent.to_ag_ui]、[`AGUIApp`][pydantic_ai.ui.ag_ui.app.AGUIApp] 和 `pydantic_ai.ag_ui` shim module 在 1.x 中已弃用，并将在 2.0 中移除。每个 API 都可直接映射到[用法](#usage)中展示的 [`AGUIAdapter`][pydantic_ai.ui.ag_ui.AGUIAdapter] 组合方式。下面的迁移方式今天在 1.x 中也可以使用。

### `pydantic_ai.ag_ui` -> `pydantic_ai.ui.ag_ui` + `pydantic_ai.ui`

shim module 会重新导出在 2.0 中位于两个不同位置的符号：

- [`AGUIAdapter`][pydantic_ai.ui.ag_ui.AGUIAdapter] 位于 [`pydantic_ai.ui.ag_ui`][pydantic_ai.ui.ag_ui]。
- [`SSE_CONTENT_TYPE`][pydantic_ai.ui.SSE_CONTENT_TYPE]、[`StateDeps`][pydantic_ai.ui.StateDeps]、[`StateHandler`][pydantic_ai.ui.StateHandler] 和 [`OnCompleteFunc`][pydantic_ai.ui.OnCompleteFunc] 位于 [`pydantic_ai.ui`][pydantic_ai.ui]。
- `handle_ag_ui_request` 和 `run_ag_ui` helpers 会在 2.0 中移除。请直接调用 [`AGUIAdapter.dispatch_request()`][pydantic_ai.ui.ag_ui.AGUIAdapter.dispatch_request]，或像[用法](#usage)中展示的那样直接组合 [`AGUIAdapter`][pydantic_ai.ui.ag_ui.AGUIAdapter]。

=== "Before (deprecated)"

    ```python {title="ag_ui_shim_before.py" test="skip" noqa="F401 I001"}
    from pydantic_ai.ag_ui import AGUIAdapter, SSE_CONTENT_TYPE, StateDeps
    ```

=== "After"

    ```python {title="ag_ui_shim_after.py" noqa="F401 I001"}
    from pydantic_ai.ui import SSE_CONTENT_TYPE, StateDeps
    from pydantic_ai.ui.ag_ui import AGUIAdapter
    ```

### `Agent.to_ag_ui()` -> `AGUIAdapter.dispatch_request`

挂载一个 Starlette/FastAPI route，调用 [`AGUIAdapter.dispatch_request()`][pydantic_ai.ui.ag_ui.AGUIAdapter.dispatch_request]（形状与[处理 Starlette request](#handle-a-starlette-request) 相同）：

=== "Before (deprecated)"

    ```python {title="agent_to_ag_ui_before.py" test="skip"}
    from pydantic_ai import Agent

    agent = Agent('openai:gpt-5.2', instructions='Be fun!')
    app = agent.to_ag_ui()
    ```

=== "After"

    ```python {title="agent_to_ag_ui_after.py"}
    from fastapi import FastAPI
    from starlette.requests import Request
    from starlette.responses import Response

    from pydantic_ai import Agent
    from pydantic_ai.ui.ag_ui import AGUIAdapter

    agent = Agent('openai:gpt-5.2', instructions='Be fun!')

    app = FastAPI()

    @app.post('/')
    async def run_agent(request: Request) -> Response:
        return await AGUIAdapter.dispatch_request(request, agent=agent)
    ```

### `AGUIApp` -> `Starlette` + `AGUIAdapter.dispatch_request`

直接用 [`Starlette`](https://www.starlette.io/applications/) route 构建 ASGI app，并调用 [`AGUIAdapter.dispatch_request()`][pydantic_ai.ui.ag_ui.AGUIAdapter.dispatch_request]：

=== "Before (deprecated)"

    ```python {title="agui_app_before.py" test="skip"}
    from pydantic_ai import Agent
    from pydantic_ai.ui.ag_ui.app import AGUIApp

    agent = Agent('openai:gpt-5.2', instructions='Be fun!')
    app = AGUIApp(agent)
    ```

=== "After"

    ```python {title="agui_app_after.py"}
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.routing import Route

    from pydantic_ai import Agent
    from pydantic_ai.ui.ag_ui import AGUIAdapter

    agent = Agent('openai:gpt-5.2', instructions='Be fun!')


    async def run_agent(request: Request) -> Response:
        return await AGUIAdapter.dispatch_request(request, agent=agent)


    app = Starlette(routes=[Route('/', run_agent, methods=['POST'])])
    ```
