# 延迟工具 {#deferred-tools}

有一些场景中，模型应该能够调用某个工具，但该工具不应或不能在同一次 agent run、同一个 Python 进程中执行：

- 可能需要先由用户批准
- 可能依赖上游服务、前端或用户提供结果
- 生成结果所需时间可能长到不适合一直保持 agent 进程运行

为支持这些用例，Pydantic AI 提供了 deferred tools 的概念，分为下面记录的两种形式：

- [需要批准](#human-in-the-loop-tool-approval)的工具
- [外部执行](#external-tool-execution)的工具

当模型调用 deferred tool 时，有两种方式可以解析它：

- **内联解析**：使用带 handler 的 [`HandleDeferredToolCalls`][pydantic_ai.capabilities.HandleDeferredToolCalls] [capability](capabilities.md)，解析部分或全部 pending calls。agent run 会在一次调用中继续，不需要结束再重启。当 resolver（例如审批门禁、外部服务 client）与 agent 位于同一进程时，请使用这种方式。参见[使用 handler 解析延迟调用](#resolving-deferred-calls-with-a-handler)。
- **结束运行**：输出一个 [`DeferredToolRequests`][pydantic_ai.output.DeferredToolRequests] 对象，其中包含 deferred tool calls 的信息；调用方收集 approvals/results 后，使用原始 run 的[消息历史](message-history.md)加上 [`DeferredToolResults`][pydantic_ai.tools.DeferredToolResults] 对象启动新的 agent run。当 resolver 位于 agent 进程外时，请使用这种方式，例如 UI adapter 将 pending calls 暴露给用户，并在收到响应后启动后续 run。

这两种流程可以组合：handler 可以解析一部分 calls，并让剩余 calls 冒泡为 `DeferredToolRequests` 输出，交由外层调用方处理。

stop-the-world 流程要求 `DeferredToolRequests` 包含在 `Agent` 的 [`output_type`](output.md#structured-output) 中，这样 agent run 输出的可能类型才能被正确推断。如果你的 agent 也可能在没有 deferred tools 的上下文中使用，而你不想在所有使用该 agent 的地方都处理该类型，也可以在通过 [`agent.run()`][pydantic_ai.agent.AbstractAgent.run]、[`agent.run_sync()`][pydantic_ai.agent.AbstractAgent.run_sync]、[`agent.run_stream()`][pydantic_ai.agent.AbstractAgent.run_stream] 或 [`agent.iter()`][pydantic_ai.agent.Agent.iter] 运行 agent 时传入 `output_type` 参数。注意，运行时的 `output_type` 会覆盖构造时指定的类型（出于类型推断原因），因此你需要显式包含原始输出类型。

## 使用 handler 解析延迟调用 {#resolving-deferred-calls-with-a-handler}

处理 deferred tool calls 的推荐方式，是注册一个 [`HandleDeferredToolCalls`][pydantic_ai.capabilities.HandleDeferredToolCalls] [capability](capabilities.md)，它的 handler 接收 [`DeferredToolRequests`][pydantic_ai.tools.DeferredToolRequests]，并返回 [`DeferredToolResults`][pydantic_ai.tools.DeferredToolResults] 来解析其中部分或全部调用。工具执行 pipeline 会内联应用这些结果，agent run 会在同一次调用中继续，就像 deferred tools 正常返回一样。

有了 handler 之后，`DeferredToolRequests` 不再需要声明为输出类型，除非你也希望未解析 calls 冒泡给调用方（见下文）。

[`DeferredToolRequests.build_results()`][pydantic_ai.tools.DeferredToolRequests.build_results] 是一个便利构造器；它会验证每个 tool call ID 都指向正确类型的 pending request，并接受 `approve_all=True` 来自动批准所有未另行指定的 approval requests。

```python {title="deferred_tool_handler.py"}
from pydantic_ai import (
    Agent,
    ApprovalRequired,
    CallDeferred,
    DeferredToolRequests,
    DeferredToolResults,
    RunContext,
    ToolDenied,
)
from pydantic_ai.capabilities import HandleDeferredToolCalls


async def handle_deferred(
    ctx: RunContext[None], requests: DeferredToolRequests
) -> DeferredToolResults:
    approvals: dict[str, bool | ToolDenied] = {}
    for call in requests.approvals:
        if call.tool_name == 'delete_file':
            approvals[call.tool_call_id] = ToolDenied('Deleting files is not allowed')
        else:
            approvals[call.tool_call_id] = True

    calls = {call.tool_call_id: f'(external result for {call.tool_name})' for call in requests.calls}

    return requests.build_results(approvals=approvals, calls=calls)


agent = Agent(
    'openai:gpt-5.2',
    capabilities=[HandleDeferredToolCalls(handler=handle_deferred)],
)


@agent.tool_plain(requires_approval=True)
def delete_file(path: str) -> str:
    return f'File {path!r} deleted'  # (1)!


@agent.tool
def update_file(ctx: RunContext, path: str) -> str:
    if path == '.env' and not ctx.tool_call_approved:
        raise ApprovalRequired
    return f'File {path!r} updated'


@agent.tool_plain
async def send_to_worker(task: str) -> str:
    raise CallDeferred  # (2)!
```

1. 不会执行到这里；handler 会拒绝这个调用，所以模型会看到拒绝消息。
2. handler 会为这个 external call 提供结果，所以工具主体只负责发出 deferral 信号。

如果 handler 拒绝解析部分或全部 calls（通过在返回的 [`DeferredToolResults`][pydantic_ai.tools.DeferredToolResults] 中省略它们，或返回 `None`），下一个 [`HandleDeferredToolCalls`][pydantic_ai.capabilities.HandleDeferredToolCalls]（或任何其他覆盖 [`handle_deferred_tool_calls`][pydantic_ai.capabilities.AbstractCapability.handle_deferred_tool_calls] hook 的 capability）会获得机会，任何仍未解析的 calls 会作为 [`DeferredToolRequests`][pydantic_ai.output.DeferredToolRequests] 输出冒泡。要允许这种冒泡，请把 `DeferredToolRequests` 包含在 agent 的 `output_type` 中，这样就能在有意义时组合内联处理和 stop-the-world 流程。

如果你正在[构建自定义 capability](capabilities.md#building-custom-capabilities)，并且需要自行解析 approvals 或 external calls（例如暴露 deferred tools 的 sandbox），请直接在你的 capability 上覆盖 [`handle_deferred_tool_calls`][pydantic_ai.capabilities.AbstractCapability.handle_deferred_tool_calls] hook，而不是注册单独的 `HandleDeferredToolCalls`。同一个 hook 也可通过 [`Hooks`][pydantic_ai.capabilities.Hooks] capability 使用；参见 [Hooks](hooks.md#deferred-tool-call-hook)。

下面各节描述 handler 可以解析的两类 deferred tools，以及每类工具的替代 stop-the-world 流程。多个 capabilities 如何组合，包括 [`WrapperCapability`][pydantic_ai.capabilities.WrapperCapability] 和 `capabilities=[...]` 列表，请参阅 [Capabilities](capabilities.md)。

## Human-in-the-Loop 工具批准 {#human-in-the-loop-tool-approval}

如果某个工具函数总是需要批准，可以向 [`@agent.tool`][pydantic_ai.agent.Agent.tool] 装饰器、[`@agent.tool_plain`][pydantic_ai.agent.Agent.tool_plain] 装饰器、[`Tool`][pydantic_ai.tools.Tool] 类、[`FunctionToolset.tool`][pydantic_ai.toolsets.FunctionToolset.tool] 装饰器或 [`FunctionToolset.add_function()`][pydantic_ai.toolsets.FunctionToolset.add_function] 方法传入 `requires_approval=True` 参数。随后在函数内部，你可以假设该工具调用已经获批。

如果工具函数是否需要批准取决于 tool call arguments 或 agent [run context][pydantic_ai.tools.RunContext]（例如 [dependencies](dependencies.md) 或消息历史），可以从工具函数抛出 [`ApprovalRequired`][pydantic_ai.exceptions.ApprovalRequired] 异常。如果工具调用已经获批，[`RunContext.tool_call_approved`][pydantic_ai.tools.RunContext.tool_call_approved] 属性会是 `True`。

要对 [toolset](toolsets.md) 提供的工具（例如 [MCP server](mcp/client.md)）调用要求批准，请参阅 [`ApprovalRequiredToolset` 文档](toolsets.md#requiring-tool-approval)。

当模型调用需要批准的工具时，agent run 会以 [`DeferredToolRequests`][pydantic_ai.output.DeferredToolRequests] 输出对象结束，其中 `approvals` 列表保存 [`ToolCallPart`s][pydantic_ai.messages.ToolCallPart]，包含工具名、验证后的参数和唯一 tool call ID。

收集用户的批准或拒绝后，可以构建一个 [`DeferredToolResults`][pydantic_ai.tools.DeferredToolResults] 对象，其中 `approvals` 字典会把每个 tool call ID 映射到 boolean、[`ToolApproved`][pydantic_ai.tools.ToolApproved] 对象（可选 `override_args`），或 [`ToolDenied`][pydantic_ai.tools.ToolDenied] 对象（可选自定义 `message`，提供给模型）。你也可以在 `DeferredToolResults` 上提供 `metadata` 字典，把每个 tool call ID 映射到 metadata 字典；这些 metadata 会在工具的 [`RunContext.tool_call_metadata`][pydantic_ai.tools.RunContext.tool_call_metadata] 属性中可用。然后可以把这个 `DeferredToolResults` 对象作为 `deferred_tool_results` 提供给某个 agent run 方法，同时传入原始 run 的[消息历史](message-history.md)。

下面示例展示如何要求所有文件删除都需要批准，并要求特定受保护文件的更新需要批准：

```python {title="tool_requires_approval.py"}
from pydantic_ai import (
    Agent,
    ApprovalRequired,
    DeferredToolRequests,
    DeferredToolResults,
    RunContext,
    ToolDenied,
)

agent = Agent('openai:gpt-5.2', output_type=[str, DeferredToolRequests])

PROTECTED_FILES = {'.env'}


@agent.tool
def update_file(ctx: RunContext, path: str, content: str) -> str:
    if path in PROTECTED_FILES and not ctx.tool_call_approved:
        raise ApprovalRequired(metadata={'reason': 'protected'})  # (1)!
    return f'File {path!r} updated: {content!r}'


@agent.tool_plain(requires_approval=True)
def delete_file(path: str) -> str:
    return f'File {path!r} deleted'


result = agent.run_sync('Delete `__init__.py`, write `Hello, world!` to `README.md`, and clear `.env`')
messages = result.all_messages()

assert isinstance(result.output, DeferredToolRequests)
requests = result.output
print(requests)
"""
DeferredToolRequests(
    calls=[],
    approvals=[
        ToolCallPart(
            tool_name='update_file',
            args={'path': '.env', 'content': ''},
            tool_call_id='update_file_dotenv',
        ),
        ToolCallPart(
            tool_name='delete_file',
            args={'path': '__init__.py'},
            tool_call_id='delete_file',
        ),
    ],
    metadata={'update_file_dotenv': {'reason': 'protected'}},
)
"""

results = DeferredToolResults()
for call in requests.approvals:
    result = False
    if call.tool_name == 'update_file':
        # Approve all updates
        result = True
    elif call.tool_name == 'delete_file':
        # deny all deletes
        result = ToolDenied('Deleting files is not allowed')

    results.approvals[call.tool_call_id] = result

result = agent.run_sync(
    'Now create a backup of README.md',  # (2)!
    message_history=messages,
    deferred_tool_results=results,
)
print(result.output)
"""
Here's what I've done:
- Attempted to delete __init__.py, but deletion is not allowed.
- Updated README.md with: Hello, world!
- Cleared .env (set to empty).
- Created a backup at README.md.bak containing: Hello, world!

If you want a different backup name or format (e.g., timestamped like README_2025-11-24.bak), let me know.
"""
print(result.all_messages())
"""
[
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Delete `__init__.py`, write `Hello, world!` to `README.md`, and clear `.env`',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        run_id='...',
        conversation_id='...',
    ),
    ModelResponse(
        parts=[
            ToolCallPart(
                tool_name='delete_file',
                args={'path': '__init__.py'},
                tool_call_id='delete_file',
            ),
            ToolCallPart(
                tool_name='update_file',
                args={'path': 'README.md', 'content': 'Hello, world!'},
                tool_call_id='update_file_readme',
            ),
            ToolCallPart(
                tool_name='update_file',
                args={'path': '.env', 'content': ''},
                tool_call_id='update_file_dotenv',
            ),
        ],
        usage=RequestUsage(input_tokens=63, output_tokens=21),
        model_name='gpt-5.2',
        timestamp=datetime.datetime(...),
        run_id='...',
        conversation_id='...',
    ),
    ModelRequest(
        parts=[
            ToolReturnPart(
                tool_name='update_file',
                content="File 'README.md' updated: 'Hello, world!'",
                tool_call_id='update_file_readme',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        run_id='...',
        conversation_id='...',
    ),
    ModelRequest(
        parts=[
            ToolReturnPart(
                tool_name='update_file',
                content="File '.env' updated: ''",
                tool_call_id='update_file_dotenv',
                timestamp=datetime.datetime(...),
            ),
            ToolReturnPart(
                tool_name='delete_file',
                content='Deleting files is not allowed',
                tool_call_id='delete_file',
                timestamp=datetime.datetime(...),
                outcome='denied',
            ),
            UserPromptPart(
                content='Now create a backup of README.md',
                timestamp=datetime.datetime(...),
            ),
        ],
        timestamp=datetime.datetime(...),
        run_id='...',
        conversation_id='...',
    ),
    ModelResponse(
        parts=[
            ToolCallPart(
                tool_name='update_file',
                args={'path': 'README.md.bak', 'content': 'Hello, world!'},
                tool_call_id='update_file_backup',
            )
        ],
        usage=RequestUsage(input_tokens=86, output_tokens=31),
        model_name='gpt-5.2',
        timestamp=datetime.datetime(...),
        run_id='...',
        conversation_id='...',
    ),
    ModelRequest(
        parts=[
            ToolReturnPart(
                tool_name='update_file',
                content="File 'README.md.bak' updated: 'Hello, world!'",
                tool_call_id='update_file_backup',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        run_id='...',
        conversation_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content="Here's what I've done:\n- Attempted to delete __init__.py, but deletion is not allowed.\n- Updated README.md with: Hello, world!\n- Cleared .env (set to empty).\n- Created a backup at README.md.bak containing: Hello, world!\n\nIf you want a different backup name or format (e.g., timestamped like README_2025-11-24.bak), let me know."
            )
        ],
        usage=RequestUsage(input_tokens=93, output_tokens=89),
        model_name='gpt-5.2',
        timestamp=datetime.datetime(...),
        run_id='...',
        conversation_id='...',
    ),
]
"""
```

1. 可选的 `metadata` 参数可以为 deferred tool calls 附加任意上下文；这些内容可在 `DeferredToolRequests.metadata` 中按 `tool_call_id` 访问。
2. 第二次 agent run 会从第一次 run 停止的位置继续，提供工具批准结果，并可选地提供新的 `user_prompt`，让模型在 deferred results 之外获得额外指令。

_（这个示例是完整的，可以"按原样"运行）_

## 外部工具执行 {#external-tool-execution}

当工具调用结果无法在调用它的同一次 agent run 内生成时，该工具就被视为 external。
external tools 的示例包括由 Web 或 app 前端实现的 client-side tools，以及交给后台 worker 或外部服务处理、而不是让 agent 进程一直运行的慢任务。

如果某个工具调用是否应外部执行取决于 tool call arguments、agent [run context][pydantic_ai.tools.RunContext]（例如 [dependencies](dependencies.md) 或消息历史），或任务预期耗时，可以定义一个工具函数，并在满足条件时抛出 [`CallDeferred`][pydantic_ai.exceptions.CallDeferred] 异常。抛出异常之前，工具函数通常会调度某个后台任务，并传递 [`RunContext.tool_call_id`][pydantic_ai.tools.RunContext.tool_call_id]，以便稍后把结果匹配到 deferred tool call。

如果某个工具总是在外部执行，并且其定义与参数 JSON schema 一起提供给你的代码，可以使用 [`ExternalToolset`](toolsets.md#external-toolset)。如果 external tools 事先已知，但你手头没有 arguments JSON schema，也可以定义一个签名合适的工具函数，让它只做一件事：抛出 [`CallDeferred`][pydantic_ai.exceptions.CallDeferred] 异常。

当模型调用 external tool 时，agent run 会以 [`DeferredToolRequests`][pydantic_ai.output.DeferredToolRequests] 输出对象结束，其中 `calls` 列表保存 [`ToolCallPart`s][pydantic_ai.messages.ToolCallPart]，包含工具名、验证后的参数和唯一 tool call ID。

当 tool call results 准备好后，可以构建 [`DeferredToolResults`][pydantic_ai.tools.DeferredToolResults] 对象，其中 `calls` 字典会把每个 tool call ID 映射到要返回给模型的任意值、[`ToolReturn`](tools-advanced.md#advanced-tool-returns) 对象，或在工具调用失败并且希望模型[重试](tools-advanced.md#tool-retries)时映射到 [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] 异常。然后可以把这个 `DeferredToolResults` 对象作为 `deferred_tool_results` 提供给某个 agent run 方法，同时传入原始 run 的[消息历史](message-history.md)。

下面示例展示如何把需要一段时间才能完成的任务移动到后台，并在任务完成后把结果返回给模型：

```python {title="external_tool.py"}
import asyncio
from dataclasses import dataclass
from typing import Any

from pydantic_ai import (
    Agent,
    CallDeferred,
    DeferredToolRequests,
    DeferredToolResults,
    ModelRetry,
    RunContext,
)


@dataclass
class TaskResult:
    task_id: str
    result: Any


async def calculate_answer_task(task_id: str, question: str) -> TaskResult:
    await asyncio.sleep(1)
    return TaskResult(task_id=task_id, result=42)


agent = Agent('openai:gpt-5.2', output_type=[str, DeferredToolRequests])

tasks: list[asyncio.Task[TaskResult]] = []


@agent.tool
async def calculate_answer(ctx: RunContext, question: str) -> str:
    task_id = f'task_{len(tasks)}'  # (1)!
    task = asyncio.create_task(calculate_answer_task(task_id, question))
    tasks.append(task)

    raise CallDeferred(metadata={'task_id': task_id})  # (2)!


async def main():
    result = await agent.run('Calculate the answer to the ultimate question of life, the universe, and everything')
    messages = result.all_messages()

    assert isinstance(result.output, DeferredToolRequests)
    requests = result.output
    print(requests)
    """
    DeferredToolRequests(
        calls=[
            ToolCallPart(
                tool_name='calculate_answer',
                args={
                    'question': 'the ultimate question of life, the universe, and everything'
                },
                tool_call_id='pyd_ai_tool_call_id',
            )
        ],
        approvals=[],
        metadata={'pyd_ai_tool_call_id': {'task_id': 'task_0'}},
    )
    """

    done, _ = await asyncio.wait(tasks)  # (3)!
    task_results = [task.result() for task in done]
    task_results_by_task_id = {result.task_id: result.result for result in task_results}

    results = DeferredToolResults()
    for call in requests.calls:
        try:
            task_id = requests.metadata[call.tool_call_id]['task_id']
            result = task_results_by_task_id[task_id]
        except KeyError:
            result = ModelRetry('No result for this tool call was found.')

        results.calls[call.tool_call_id] = result

    result = await agent.run(message_history=messages, deferred_tool_results=results)
    print(result.output)
    #> The answer to the ultimate question of life, the universe, and everything is 42.
    print(result.all_messages())
    """
    [
        ModelRequest(
            parts=[
                UserPromptPart(
                    content='Calculate the answer to the ultimate question of life, the universe, and everything',
                    timestamp=datetime.datetime(...),
                )
            ],
            timestamp=datetime.datetime(...),
            run_id='...',
            conversation_id='...',
        ),
        ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name='calculate_answer',
                    args={
                        'question': 'the ultimate question of life, the universe, and everything'
                    },
                    tool_call_id='pyd_ai_tool_call_id',
                )
            ],
            usage=RequestUsage(input_tokens=63, output_tokens=13),
            model_name='gpt-5.2',
            timestamp=datetime.datetime(...),
            run_id='...',
            conversation_id='...',
        ),
        ModelRequest(
            parts=[
                ToolReturnPart(
                    tool_name='calculate_answer',
                    content=42,
                    tool_call_id='pyd_ai_tool_call_id',
                    timestamp=datetime.datetime(...),
                )
            ],
            timestamp=datetime.datetime(...),
            run_id='...',
            conversation_id='...',
        ),
        ModelResponse(
            parts=[
                TextPart(
                    content='The answer to the ultimate question of life, the universe, and everything is 42.'
                )
            ],
            usage=RequestUsage(input_tokens=64, output_tokens=28),
            model_name='gpt-5.2',
            timestamp=datetime.datetime(...),
            run_id='...',
            conversation_id='...',
        ),
    ]
    """
```

1. 生成一个可独立于 tool call ID 跟踪的 task ID。
2. 可选的 `metadata` 参数会传递 `task_id`，便于稍后与结果匹配；这些内容可在 `DeferredToolRequests.metadata` 中按 `tool_call_id` 访问。
3. 在真实场景中，这通常会发生在单独进程中，由该进程轮询任务状态，或在所有 pending tasks 完成时收到通知。

_（这个示例是完整的，可以"按原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

## 另请参阅 {#see-also}

- [Function Tools](tools.md) - 基础工具概念和注册
- [Advanced Tool Features](tools-advanced.md) - 自定义 schemas、动态工具和执行细节
- [Toolsets](toolsets.md) - 管理工具集合，包括用于 external tools 的 `ExternalToolset`
- [Message History](message-history.md) - 理解如何配合 deferred tools 使用消息历史
