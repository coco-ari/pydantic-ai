# UI Event Streams {#ui-event-streams}

如果你正在为 AI agent 构建聊天应用或其他交互式前端，后端需要从前端接收 agent run input（例如聊天消息或完整[消息历史](../message-history.md)），并需要将 [agent events](../agent.md#streaming-all-events)（例如文本、thinking 和 tool calls）流式传输到前端，让用户实时了解正在发生什么。

虽然前端可以直接使用 Pydantic AI 的 [`ModelRequest`][pydantic_ai.messages.ModelRequest] 和 [`AgentStreamEvent`][pydantic_ai.messages.AgentStreamEvent]，但通常你会想使用前端框架原生支持的 UI event stream protocol。

Pydantic AI 原生支持两种 UI event stream protocols：

- [Agent-User Interaction (AG-UI) Protocol](./ag-ui.md)
- [Vercel AI Data Stream Protocol](./vercel-ai.md)

这些集成都实现为抽象 [`UIAdapter`][pydantic_ai.ui.UIAdapter] 类的子类，因此也可以作为集成其他 UI event stream protocols 的参考。

## 用法 {#usage}

协议特定的 [`UIAdapter`][pydantic_ai.ui.UIAdapter] 子类（即 [`AGUIAdapter`][pydantic_ai.ui.ag_ui.AGUIAdapter] 或 [`VercelAIAdapter`][pydantic_ai.ui.vercel_ai.VercelAIAdapter]）负责将前端收到的 agent run input 转换为 [`Agent.run_stream_events()`](../agent.md#running-agents) 的参数，运行 agent，然后将 Pydantic AI events 转换为协议特定 events。event stream 转换由协议特定的 [`UIEventStream`][pydantic_ai.ui.UIEventStream] 子类处理，但你通常不会直接使用它。

如果你使用 FastAPI 这类基于 Starlette 的 web framework，可以在 endpoint function 中使用 [`UIAdapter.dispatch_request()`][pydantic_ai.ui.UIAdapter.dispatch_request] 类方法直接处理请求，并返回协议特定 events 的 streaming response。下一节会演示这一点。

如果你使用的 web framework 不基于 Starlette（例如 Django 或 Flask），或需要更精细地控制 input 或 output，可以创建 `UIAdapter` 实例并直接使用其方法。下方"高级用法"章节会演示这一点。

### 与 Starlette/FastAPI 一起使用 {#usage-with-starlettefastapi}

除了 request，[`UIAdapter.dispatch_request()`][pydantic_ai.ui.UIAdapter.dispatch_request] 还接受 agent、与 [`Agent.run_stream_events()`](../agent.md#running-agents) 相同的可选参数，以及可选的 `on_complete` callback function。该 callback 会接收已完成的 [`AgentRunResult`][pydantic_ai.agent.AgentRunResult]，并可选择 yield 额外的协议特定 events。

!!! note
    这些示例使用 `VercelAIAdapter`，但相同模式适用于所有 `UIAdapter` 子类。

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

如果你使用的 web framework 不基于 Starlette（例如 Django 或 Flask），或需要更精细地控制 input 或 output，可以创建 `UIAdapter` 实例并直接使用其方法。这些方法可以串联起来，完成与上方 `UIAdapter.dispatch_request()` 类方法相同的事情：

1. [`UIAdapter.build_run_input()`][pydantic_ai.ui.UIAdapter.build_run_input] 类方法接受 bytes 形式的 request body，并返回协议特定 run input 对象；随后可以将它与 agent 一起传给 [`UIAdapter()`][pydantic_ai.ui.UIAdapter] 构造函数。
    - 你也可以使用 [`UIAdapter.from_request()`][pydantic_ai.ui.UIAdapter.from_request] 类方法，直接从 Starlette/FastAPI request 构建 adapter。
2. [`UIAdapter.run_stream()`][pydantic_ai.ui.UIAdapter.run_stream] 方法运行 agent，并返回协议特定 events 的 stream。它支持与 [`Agent.run_stream_events()`](../agent.md#running-agents) 相同的可选参数，以及可选的 `on_complete` callback function；该 callback 会接收已完成的 [`AgentRunResult`][pydantic_ai.agent.AgentRunResult]，并可选择 yield 额外的协议特定 events。
    - 你也可以使用 [`UIAdapter.run_stream_native()`][pydantic_ai.ui.UIAdapter.run_stream_native] 运行 agent，并返回 Pydantic AI events 的 stream；然后可用 [`UIAdapter.transform_stream()`][pydantic_ai.ui.UIAdapter.transform_stream] 将其转换为协议特定 events。
3. [`UIAdapter.encode_stream()`][pydantic_ai.ui.UIAdapter.encode_stream] 方法将协议特定 events 的 stream 编码为 SSE（HTTP Server-Sent Events）字符串，随后可以将它作为 streaming response 返回。
    - 你也可以使用 [`UIAdapter.streaming_response()`][pydantic_ai.ui.UIAdapter.streaming_response]，直接根据 `run_stream()` 返回的协议特定 event stream 生成 Starlette/FastAPI streaming response。

!!! note
    此示例使用 FastAPI，但可以修改为适用于任何 web framework。

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

## Client-submitted messages 的信任模型 {#trust-model-for-client-submitted-messages}

UI adapter endpoints 不是认证边界。AG-UI 和 Vercel AI protocols 的设计都要求 client 在每个请求中传输完整 conversation history，因此 protocol 中 `message_history` 里的任何内容，包括 assistant messages、tool calls、file URLs 和 tool results，都在调用方控制之下。请将 adapter endpoint 视为内部 backend service，并在你自己的已认证 route handler 内运行它。关于这两个 protocols 假定的部署模型，请参见 [AG-UI security considerations](https://learn.microsoft.com/en-us/agent-framework/integrations/ag-ui/security-considerations) 页面。

adapters 会应用一些默认行为，让权威状态保留在你这一侧：

- **System prompts**：client-submitted [`SystemPromptPart`][pydantic_ai.messages.SystemPromptPart] 默认会被移除，并替换为 agent 配置的 prompt。可通过 [`UIAdapter.manage_system_prompt`][pydantic_ai.ui.UIAdapter.manage_system_prompt] 控制；详情请参见各 adapter 文档。
- **Dangling tool calls**：如果 client-submitted history 以包含未解析 [`ToolCallPart`][pydantic_ai.messages.ToolCallPart] 且没有匹配 `deferred_tool_results` 的 [`ModelResponse`][pydantic_ai.messages.ModelResponse] 结尾，这些 tool calls 会被丢弃并发出 warning，避免 agent 执行模型从未发出的 tool calls。对于 human-in-the-loop resumption，请向 run 方法传入显式 `deferred_tool_results`，由这些结果解析的 tool calls 会被保留。
- **File URL schemes**：默认情况下，client-submitted messages 中的 [`FileUrl`][pydantic_ai.messages.FileUrl] parts 只接受 `http` 和 `https`。`s3://` 或 `gs://` 等非 HTTP schemes 会被丢弃，因为它们会导致 provider 使用你 server 的 IAM role 或 service account 获取对象。请参见 [`UIAdapter.allowed_file_url_schemes`][pydantic_ai.ui.UIAdapter.allowed_file_url_schemes]。
- **File URL download mode**：默认情况下，client-submitted messages 中 [`FileUrl.force_download`][pydantic_ai.messages.FileUrl.force_download] 不为 `False` 的值会被重置为 `False`。这可以防止 clients 强制 server 获取某个 URL，或使用 `'allow-local'` 绕过 SSRF private-IP block。审计你的前端后，可用 [`UIAdapter.allowed_file_url_force_download`][pydantic_ai.ui.UIAdapter.allowed_file_url_force_download] 选择允许额外值。

若需要更严格的 conversation integrity（例如确保先前 assistant turns 和 tool returns 与 server 实际生成内容匹配），请按 thread/session ID 在 server-side 持久化 history，并通过 `message_history` 将其传给 adapter。调用方提供的 history 会被视为来自 server-side persistence，因此不受此 sanitization 影响。
