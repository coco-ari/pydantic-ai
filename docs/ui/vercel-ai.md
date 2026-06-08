# Vercel AI Data Stream 协议 {#vercel-ai-data-stream-protocol}

Pydantic AI 原生支持 [Vercel AI Data Stream Protocol](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#data-stream-protocol)，可通过 [`useChat`](https://ai-sdk.dev/docs/reference/ai-sdk-ui/use-chat) 这类 [AI SDK UI](https://ai-sdk.dev/docs/ai-sdk-ui/overview) hooks 从前端接收 agent 运行输入，并向前端流式发送事件。你也可以选择使用 [AI Elements](https://ai-sdk.dev/elements) 提供的预构建 UI 组件。

!!! note
    默认情况下，适配器为了向后兼容会面向 AI SDK v5。要使用 AI SDK v6 引入的功能，请在适配器上设置 `sdk_version=6`。

## 用法 {#usage}

[`VercelAIAdapter`][pydantic_ai.ui.vercel_ai.VercelAIAdapter] 类负责把从前端收到的 agent 运行输入转换成 [`Agent.run_stream_events()`](../agent.md#running-agents) 的参数，运行 agent，然后再把 Pydantic AI 事件转换成 Vercel AI 事件。事件流转换由 [`VercelAIEventStream`][pydantic_ai.ui.vercel_ai.VercelAIEventStream] 类处理，但你通常不会直接使用它。

如果你使用的是基于 Starlette 的 Web 框架（例如 FastAPI），可以在端点函数中使用 [`VercelAIAdapter.dispatch_request()`][pydantic_ai.ui.UIAdapter.dispatch_request] 类方法直接处理请求，并返回 Vercel AI 事件的流式响应。下一节会演示这种用法。

如果你使用的 Web 框架不是基于 Starlette（例如 Django 或 Flask），或者需要对输入或输出进行细粒度控制，可以创建一个 `VercelAIAdapter` 实例并直接使用它的方法。下面"高级用法"一节会演示这种方式。

### 与 Starlette/FastAPI 一起使用 {#usage-with-starlettefastapi}

除了 request 之外，[`VercelAIAdapter.dispatch_request()`][pydantic_ai.ui.UIAdapter.dispatch_request] 还接收 agent、与 [`Agent.run_stream_events()`](../agent.md#running-agents) 相同的可选参数，以及一个可选的 `on_complete` 回调函数。该回调会收到完成后的 [`AgentRunResult`][pydantic_ai.agent.AgentRunResult]，并且可以选择继续 yield 额外的 Vercel AI 事件。

```py {title="dispatch_request.py"}
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from pydantic_ai import Agent
from pydantic_ai.ui.vercel_ai import VercelAIAdapter

agent = Agent('openai:gpt-5.2')

app = FastAPI()

@app.post('/chat')
async def chat(request: Request) -> Response:
    return await VercelAIAdapter.dispatch_request(request, agent=agent)
```

### 高级用法 {#advanced-usage}

如果你使用的 Web 框架不是基于 Starlette（例如 Django 或 Flask），或者需要对输入或输出进行细粒度控制，可以创建一个 `VercelAIAdapter` 实例并直接使用它的方法。这些方法可以串起来，实现与上面展示的 `VercelAIAdapter.dispatch_request()` 类方法相同的效果：

1. [`VercelAIAdapter.build_run_input()`][pydantic_ai.ui.vercel_ai.VercelAIAdapter.build_run_input] 类方法接收字节形式的请求体，并返回一个 Vercel AI [`RequestData`][pydantic_ai.ui.vercel_ai.request_types.RequestData] 运行输入对象。随后你可以把它与 agent 一起传给 [`VercelAIAdapter()`][pydantic_ai.ui.vercel_ai.VercelAIAdapter] 构造函数。
    - 也可以使用 [`VercelAIAdapter.from_request()`][pydantic_ai.ui.UIAdapter.from_request] 类方法，直接从 Starlette/FastAPI request 构建适配器。
2. [`VercelAIAdapter.run_stream()`][pydantic_ai.ui.UIAdapter.run_stream] 方法运行 agent 并返回 Vercel AI 事件流。它支持与 [`Agent.run_stream_events()`](../agent.md#running-agents) 相同的可选参数，以及一个可选的 `on_complete` 回调函数。该回调会收到完成后的 [`AgentRunResult`][pydantic_ai.agent.AgentRunResult]，并且可以选择继续 yield 额外的 Vercel AI 事件。
    - 也可以使用 [`VercelAIAdapter.run_stream_native()`][pydantic_ai.ui.UIAdapter.run_stream_native] 运行 agent 并返回 Pydantic AI 事件流，然后再用 [`VercelAIAdapter.transform_stream()`][pydantic_ai.ui.UIAdapter.transform_stream] 将其转换为 Vercel AI 事件。
3. [`VercelAIAdapter.encode_stream()`][pydantic_ai.ui.UIAdapter.encode_stream] 方法把 Vercel AI 事件流编码成 SSE（HTTP Server-Sent Events）字符串，然后你可以把它作为流式响应返回。
    - 也可以使用 [`VercelAIAdapter.streaming_response()`][pydantic_ai.ui.UIAdapter.streaming_response]，直接基于 `run_stream()` 返回的 Vercel AI 事件流生成 Starlette/FastAPI 流式响应。

!!! note
    这个示例使用 FastAPI，但可以改造成适用于任何 Web 框架。

```py {title="run_stream.py"}
import json
from http import HTTPStatus

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response, StreamingResponse
from pydantic import ValidationError

from pydantic_ai import Agent
from pydantic_ai.ui import SSE_CONTENT_TYPE
from pydantic_ai.ui.vercel_ai import VercelAIAdapter

agent = Agent('openai:gpt-5.2')

app = FastAPI()


@app.post('/chat')
async def chat(request: Request) -> Response:
    accept = request.headers.get('accept', SSE_CONTENT_TYPE)
    try:
        run_input = VercelAIAdapter.build_run_input(await request.body())
    except ValidationError as e:
        return Response(
            content=json.dumps(e.json()),
            media_type='application/json',
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )

    adapter = VercelAIAdapter(agent=agent, run_input=run_input, accept=accept)
    event_stream = adapter.run_stream()

    sse_event_stream = adapter.encode_stream(event_stream)
    return StreamingResponse(sse_event_stream, media_type=accept)
```

### 数据 chunk {#data-chunks}

Pydantic AI 工具可以通过返回 [`ToolReturn`](../tools-advanced.md#advanced-tool-returns) 对象，并在 `metadata` 中携带一个数据 chunk（或 chunk 列表），来发送 [Vercel AI data stream chunks](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol#data-stream-protocol)。
支持的 chunk 类型包括 [`DataChunk`][pydantic_ai.ui.vercel_ai.response_types.DataChunk]、[`SourceUrlChunk`][pydantic_ai.ui.vercel_ai.response_types.SourceUrlChunk]、[`SourceDocumentChunk`][pydantic_ai.ui.vercel_ai.response_types.SourceDocumentChunk] 和 [`FileChunk`][pydantic_ai.ui.vercel_ai.response_types.FileChunk]。
这适合在工具结果旁边给前端附加结构化数据，例如来源 URL 或自定义数据载荷。

```python {title="vercel_ai_tool_chunks.py"}
from pydantic_ai import Agent, ToolReturn
from pydantic_ai.ui.vercel_ai.response_types import DataChunk, SourceUrlChunk

agent = Agent('openai:gpt-5.2')


@agent.tool_plain
async def search_docs(query: str) -> ToolReturn:
    return ToolReturn(
        return_value=f'Found 2 results for "{query}"',
        metadata=[
            SourceUrlChunk(
                source_id='doc-1',
                url='https://example.com/docs/intro',
                title='Introduction',
            ),
            DataChunk(
                type='data-search-results',
                data={'query': query, 'count': 2},
            ),
        ],
    )
```

!!! note
    `StartChunk`、`FinishChunk`、`StartStepChunk` 或 `FinishStepChunk` 这类协议控制 chunk 会被自动过滤掉。只有上面列出的四种携带数据的 chunk 类型会被转发到流中，并在 `dump_messages` 中保留。

## 消息元数据 {#message-metadata}

[`VercelAIAdapter.dump_messages`][pydantic_ai.ui.vercel_ai.VercelAIAdapter.dump_messages] 会把 [`ModelRequest.metadata`][pydantic_ai.messages.ModelRequest.metadata] 和 [`ModelResponse.metadata`][pydantic_ai.messages.ModelResponse.metadata] 写入 Vercel AI [`UIMessage.metadata`](https://ai-sdk.dev/docs/ai-sdk-ui/message-metadata)，并把消息 `timestamp` 存储在保留的 `pydantic_ai` key 下，这样它就能在往返转换中保留下来。[`VercelAIAdapter.load_messages`][pydantic_ai.ui.vercel_ai.VercelAIAdapter.load_messages] 会在返回路径上恢复它。

流式传输时，timestamp 也会在最后一个 step 之后作为 Vercel AI `message-metadata` chunk 发出，因此使用 AI SDK UI 的前端可以把它和 assistant 消息一起持久化。请求侧消息没有类似 chunk：如果前端只从流式 chunk 重建历史，就只能在 assistant 响应上看到 timestamp，而 `dump_messages` 会填充双方消息。

`UIMessage.metadata` 完全由客户端控制，因此只有 `timestamp` 会往返传递：`usage`、`model_name` 和 `provider_*` 等服务端字段会被刻意排除。导出这些字段可能泄露基础设施细节，而恢复它们则意味着信任客户端提交的历史中本应由服务端拥有的值。通过显式、用户可控的 opt-in 扩展往返传递范围，已在 [issue #5174](https://github.com/pydantic/pydantic-ai/issues/5174) 中跟踪。

## 信任模型 {#trust-model}

Vercel AI 请求中的 `messages` 数组完全由客户端控制，并且协议会通过消息历史往返传递审批响应和工具结果。[`VercelAIAdapter`][pydantic_ai.ui.vercel_ai.VercelAIAdapter] 会应用默认设置，在 agent 运行前剥离不可信部分。详见 UI 适配器概览中的[客户端提交消息的信任模型](./overview.md#trust-model-for-client-submitted-messages)。

## 工具审批 {#tool-approval}

!!! note
    工具审批要求前端使用 AI SDK UI v6 或更高版本。

Pydantic AI 支持与 AI SDK UI 配合的人在环路工具审批工作流，允许用户在工具执行前批准或拒绝。关于如何设置需要审批的工具，详见[延迟工具调用文档](../deferred-tools.md#human-in-the-loop-tool-approval)。

要启用工具审批流式传输，请向 `dispatch_request` 传入 `sdk_version=6`：

```py {test="skip" lint="skip"}
@app.post('/chat')
async def chat(request: Request) -> Response:
    return await VercelAIAdapter.dispatch_request(request, agent=agent, sdk_version=6)
```

当 `sdk_version=6` 时，适配器会：

1. 在调用带有 `requires_approval=True` 的工具时发出 `tool-approval-request` chunk
2. 自动从后续请求中提取审批响应
3. 为被拒绝的工具发出 `tool-output-denied` chunk

在前端，AI SDK UI 的 [`useChat`](https://ai-sdk.dev/docs/reference/ai-sdk-ui/use-chat) hook 会处理审批流程。你可以使用 AI Elements 中的 [`Confirmation`](https://ai-sdk.dev/elements/components/confirmation) 组件作为预构建审批 UI，也可以用 hook 的 `addToolApprovalResponse` 函数构建自己的 UI。

按照协议通过 `useChat` 的 `addToolApprovalResponse` 和参考 Next.js 后端进行往返传递的设计，来自请求的工具审批响应会被信任。如果你的应用需要把审批决策绑定到服务端状态，而不是绑定到请求，请拦截 [`DeferredToolRequests`][pydantic_ai.DeferredToolRequests]，在服务端持久化审批 ID，并在恢复时传入显式的 `deferred_tool_results`。

## 工具输入验证 {#tool-input-validation}

`tool-input-available` 会在 agent 已根据工具 schema 和任何自定义 [`args_validator`](../tools-advanced.md#args-validator) 验证调用之后才发出，因此只有当 args 已知可接受时，该 chunk 才会触发。chunk 的 `input` 字段会携带模型发出的原始参数。

验证失败时，适配器会发出 `tool-input-error`，而不是 `tool-input-available`。该 chunk 携带相同的 `tool_call_id`、`tool_name` 和 `input`（原始参数），外加一个 `error_text` 字段；该字段由将要发回模型的重试提示渲染而来。agent 会重试该调用（受工具 `retries` 设置约束），并为每次尝试发出新的 `tool-input-(available|error)`。

## System prompts 和 instructions {#system-prompts-and-instructions}

Pydantic AI 支持两种向模型提供指导的方式：[`system_prompt`](../agent.md#system-prompts)（作为 [`SystemPromptPart`][pydantic_ai.messages.SystemPromptPart] 存储在消息历史中）和 [`instructions`](../agent.md#instructions)（每次请求都会重新注入，从不持久化）。当你控制服务端时，`instructions` 是推荐默认值。

本节剩余内容只有在你使用 `system_prompt` 时才重要。如果你只使用 `instructions`，则无需配置任何内容；无论前端消息历史如何，它们都会始终应用。

对于 `system_prompt`，你可以通过 [`VercelAIAdapter`][pydantic_ai.ui.vercel_ai.VercelAIAdapter] 上的 `manage_system_prompt` 参数选择所有权归属：

- `'server'`（默认）：agent 配置的 `system_prompt` 具有权威性。前端发送的任何 system message 都会被剥离并给出警告（否则恶意客户端可以通过构造的 API 请求注入任意指令），agent 自己的 system prompt 会通过 [`ReinjectSystemPrompt`][pydantic_ai.capabilities.ReinjectSystemPrompt] capability 重新注入到第一个请求的开头。
- `'client'`：前端拥有 system prompt。前端 system message 会原样保留，而 agent 配置的 `system_prompt` 不会被注入；如果需要，调用方需要完全负责在每一轮发送它。要选择启用回退到已配置内容的行为，请把 [`ReinjectSystemPrompt`][pydantic_ai.capabilities.ReinjectSystemPrompt] capability 添加到你的 agent。

```python {title="vercel_ai_client_managed_system_prompt.py"}
from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from pydantic_ai import Agent
from pydantic_ai.ui.vercel_ai import VercelAIAdapter

agent = Agent('openai:gpt-5.2')

app = FastAPI()


@app.post('/chat')
async def chat(request: Request) -> Response:
    return await VercelAIAdapter.dispatch_request(
        request, agent=agent, manage_system_prompt='client'
    )
```
