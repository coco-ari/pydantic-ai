# Messages 和聊天历史 {#messages-and-chat-history}

Pydantic AI 提供了访问 agent run 期间交换消息的能力。这些消息既可以用于延续连贯对话，也可以用于理解 agent 的执行表现。

### 从 Results 访问 Messages {#accessing-messages-from-results}

运行 agent 后，可以从 `result` 对象访问该 run 期间交换的 messages。

[`RunResult`][pydantic_ai.agent.AgentRunResult]
（由 [`Agent.run`][pydantic_ai.agent.AbstractAgent.run]、[`Agent.run_sync`][pydantic_ai.agent.AbstractAgent.run_sync] 返回）
和 [`StreamedRunResult`][pydantic_ai.result.StreamedRunResult]（由 [`Agent.run_stream`][pydantic_ai.agent.AbstractAgent.run_stream] 返回）都提供以下方法：

- [`all_messages()`][pydantic_ai.agent.AgentRunResult.all_messages]：返回所有 messages，包括 prior runs 中的 messages。还有一个返回 JSON bytes 的变体 [`all_messages_json()`][pydantic_ai.agent.AgentRunResult.all_messages_json]。
- [`new_messages()`][pydantic_ai.agent.AgentRunResult.new_messages]：只返回当前 run 中的 messages。还有一个返回 JSON bytes 的变体 [`new_messages_json()`][pydantic_ai.agent.AgentRunResult.new_messages_json]。

!!! info "`StreamedRunResult` 和完整 messages"
    在 [`StreamedRunResult`][pydantic_ai.result.StreamedRunResult] 上，这些方法返回的 messages 只有在 stream 结束后才会包含最终 result message。

    例如，你已经 await 了以下 coroutines 之一：

    * [`StreamedRunResult.stream_output()`][pydantic_ai.result.StreamedRunResult.stream_output]
    * [`StreamedRunResult.stream_text()`][pydantic_ai.result.StreamedRunResult.stream_text]
    * [`StreamedRunResult.stream_response()`][pydantic_ai.result.StreamedRunResult.stream_response]
    * [`StreamedRunResult.get_output()`][pydantic_ai.result.StreamedRunResult.get_output]

    **注意：** 如果你使用 [`.stream_text(delta=True)`][pydantic_ai.result.StreamedRunResult.stream_text]，最终 result message **不会**添加到 result messages 中，因为在这种情况下 result content 从未被构建成一个完整字符串。

在 [`RunResult`][pydantic_ai.agent.AgentRunResult] 上访问这些方法的示例：

```python {title="run_result_messages.py" hl_lines="10"}
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2', instructions='Be a helpful assistant.')

result = agent.run_sync('Tell me a joke.')
print(result.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.

# all messages from the run
print(result.all_messages())
"""
[
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Tell me a joke.',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        instructions='Be a helpful assistant.',
        run_id='...',
        conversation_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='Did you hear about the toothpaste scandal? They called it Colgate.'
            )
        ],
        usage=RequestUsage(input_tokens=55, output_tokens=12),
        model_name='gpt-5.2',
        timestamp=datetime.datetime(...),
        run_id='...',
        conversation_id='...',
    ),
]
"""
```

_（这个示例是完整的，可以"原样"运行）_

在 [`StreamedRunResult`][pydantic_ai.result.StreamedRunResult] 上访问这些方法的示例：

```python {title="streamed_run_result_messages.py" hl_lines="9 40"}
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2', instructions='Be a helpful assistant.')


async def main():
    async with agent.run_stream('Tell me a joke.') as result:
        # incomplete messages before the stream finishes
        print(result.all_messages())
        """
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='Tell me a joke.',
                        timestamp=datetime.datetime(...),
                    )
                ],
                timestamp=datetime.datetime(...),
                instructions='Be a helpful assistant.',
                run_id='...',
                conversation_id='...',
            )
        ]
        """

        async for text in result.stream_text():
            print(text)
            #> Did you hear
            #> Did you hear about the toothpaste
            #> Did you hear about the toothpaste scandal? They called
            #> Did you hear about the toothpaste scandal? They called it Colgate.

        # complete messages once the stream finishes
        print(result.all_messages())
        """
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='Tell me a joke.',
                        timestamp=datetime.datetime(...),
                    )
                ],
                timestamp=datetime.datetime(...),
                instructions='Be a helpful assistant.',
                run_id='...',
                conversation_id='...',
            ),
            ModelResponse(
                parts=[
                    TextPart(
                        content='Did you hear about the toothpaste scandal? They called it Colgate.'
                    )
                ],
                usage=RequestUsage(input_tokens=50, output_tokens=12),
                model_name='gpt-5.2',
                timestamp=datetime.datetime(...),
                run_id='...',
                conversation_id='...',
            ),
        ]
        """
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

### 将 Messages 用作后续 Agent Runs 的输入 {#using-messages-as-input-for-further-agent-runs}

Pydantic AI 中 message histories 的主要用途，是在多个 agent runs 之间保持上下文。

要在 run 中使用已有 messages，请将它们传给
[`Agent.run`][pydantic_ai.agent.AbstractAgent.run]、[`Agent.run_sync`][pydantic_ai.agent.AbstractAgent.run_sync] 或
[`Agent.run_stream`][pydantic_ai.agent.AbstractAgent.run_stream] 的 `message_history` 参数。

如果 `message_history` 已设置且非空，就不会生成新的 system prompt，因为我们假定已有 message history 包含 system prompt。如果你的 history 来自无法 round-trip system prompts 的来源（UI frontend、未持久化 system prompts 的数据库、compaction pipeline），请添加 [`ReinjectSystemPrompt`][pydantic_ai.capabilities.ReinjectSystemPrompt] capability，这样当缺少 system prompt 时，agent 配置的 `system_prompt` 会在第一次请求头部重新注入。

对话中途的 `SystemPromptPart`（第一个之后任何 `ModelRequest` 中的 `SystemPromptPart`）会由 API 接受任意位置 system messages 的 providers 按原位置 inline 发送。对于 API 不支持的 providers，它们会改为在相同位置渲染为带 `<system>` 标签的 `UserPromptPart`，以保留 prefix cache 和位置意图。Leading `SystemPromptPart` 始终会 hoist 到 provider 的顶层 system 参数。

```python {title="Reusing messages in a conversation" hl_lines="9 13"}
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2', instructions='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
print(result1.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.

result2 = agent.run_sync('Explain?', message_history=result1.new_messages())
print(result2.output)
#> This is an excellent joke invented by Samuel Colvin, it needs no explanation.

print(result2.all_messages())
"""
[
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Tell me a joke.',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        instructions='Be a helpful assistant.',
        run_id='...',
        conversation_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='Did you hear about the toothpaste scandal? They called it Colgate.'
            )
        ],
        usage=RequestUsage(input_tokens=55, output_tokens=12),
        model_name='gpt-5.2',
        timestamp=datetime.datetime(...),
        run_id='...',
        conversation_id='...',
    ),
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Explain?',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        instructions='Be a helpful assistant.',
        run_id='...',
        conversation_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='This is an excellent joke invented by Samuel Colvin, it needs no explanation.'
            )
        ],
        usage=RequestUsage(input_tokens=56, output_tokens=26),
        model_name='gpt-5.2',
        timestamp=datetime.datetime(...),
        run_id='...',
        conversation_id='...',
    ),
]
"""
```

_（这个示例是完整的，可以"原样"运行）_

### 用 `conversation_id` 关联 runs {#correlating-runs-with-conversation-id}

每个 `ModelRequest` 和 `ModelResponse` 都携带两个标识符：

- [`run_id`][pydantic_ai.messages.ModelRequest.run_id]：每个 agent run 唯一；作为 `gen_ai.agent.call.id` 发到 OpenTelemetry agent run span 上。
- [`conversation_id`][pydantic_ai.messages.ModelRequest.conversation_id]：所有基于同一 `message_history` 构建的 runs 共享；作为 `gen_ai.conversation.id` 发出。

第一次 run 会生成新的 `conversation_id`，并标记到该 run 生成的每条 message 上；后续 runs 通过 `message_history` 把这些 messages 传回时，会继承这个 ID。这意味着你可以在 [Logfire](logfire.md)（或任何 OpenTelemetry backend）中关联多轮对话的 traces，而无需自行跟踪；只要 message history 完成 round-trip，conversation ID 也会随之传递。

```python {title="conversation_id is shared across runs in the same conversation"}
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')

result1 = agent.run_sync('Tell me a joke.')
result2 = agent.run_sync('Explain?', message_history=result1.all_messages())

assert result1.conversation_id == result2.conversation_id
```

要覆盖或 fork：

- 传入 `conversation_id='<your-id>'`，使用你自己应用中的 ID（例如数据库中存储的 chat thread ID）。
- 传入 `conversation_id='new'`，开始一个新的 conversation，忽略 `message_history` 上已有的任何 `conversation_id`；这适合从现有 thread 分支出去，而无需让调用方生成 ID。

```python {title="forking a conversation"}
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')

result1 = agent.run_sync('Tell me a joke.')
forked = agent.run_sync(
    'Tell me a different joke.',
    message_history=result1.all_messages(),
    conversation_id='new',
)

assert forked.conversation_id != result1.conversation_id
```

[UI adapters](ui/overview.md) 会从协议自身的 thread/chat ID 自动填充 `conversation_id`，因此使用这些协议的 frontends 可以免费获得 correlation。

## 存储和加载 messages（到 JSON）{#storing-and-loading-messages-to-json}

虽然对许多应用来说，在内存中维护 conversation state 已经足够，但你经常可能希望把 agent run 的 messages history 存储到磁盘或数据库中。这可能用于 evals、在 Python 和 JavaScript/TypeScript 之间共享数据，或其他任何用例。

预期做法是使用 `TypeAdapter`。

我们导出可用于此目的的 [`ModelMessagesTypeAdapter`][pydantic_ai.messages.ModelMessagesTypeAdapter]，你也可以创建自己的 adapter。

下面是一个示例：

```python {title="serialize messages to json"}
from pydantic_core import to_jsonable_python

from pydantic_ai import (
    Agent,
    ModelMessagesTypeAdapter,  # (1)!
)

agent = Agent('openai:gpt-5.2', instructions='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
history_step_1 = result1.all_messages()
as_python_objects = to_jsonable_python(history_step_1)  # (2)!
same_history_as_step_1 = ModelMessagesTypeAdapter.validate_python(as_python_objects)

result2 = agent.run_sync(  # (3)!
    'Tell me a different joke.', message_history=same_history_as_step_1
)
```

1. 或者，你可以从零创建一个 `TypeAdapter`：
   ```python {lint="skip" format="skip"}
   from pydantic import TypeAdapter
   from pydantic_ai import ModelMessage
   ModelMessagesTypeAdapter = TypeAdapter(list[ModelMessage])
   ```
2. 或者你也可以直接序列化到 JSON / 从 JSON 反序列化：
   ```python {test="skip" lint="skip" format="skip"}
   from pydantic_core import to_json
   ...
   as_json_objects = to_json(history_step_1)
   same_history_as_step_1 = ModelMessagesTypeAdapter.validate_json(as_json_objects)
   ```
3. 现在你可以用 history `same_history_as_step_1` 继续对话，即使它创建了新的 agent run。

_（这个示例是完整的，可以"原样"运行）_

## 使用 messages 的其他方式 {#other-ways-of-using-messages}

由于 messages 由简单 dataclasses 定义，你可以手动创建和操作它们，例如用于测试。

Message format 独立于所使用的模型，因此你可以在不同 agents 中使用 messages，或在同一个 agent 中使用不同模型。

在下面的示例中，我们将在第一个 agent run 中使用 `openai:gpt-5.2` 模型得到的 message，复用到第二个使用 `google:gemini-3-pro-preview` 模型的 agent run。

```python {title="Reusing messages with a different model" hl_lines="17"}
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2', instructions='Be a helpful assistant.')

result1 = agent.run_sync('Tell me a joke.')
print(result1.output)
#> Did you hear about the toothpaste scandal? They called it Colgate.

result2 = agent.run_sync(
    'Explain?',
    model='google:gemini-3-pro-preview',
    message_history=result1.new_messages(),
)
print(result2.output)
#> This is an excellent joke invented by Samuel Colvin, it needs no explanation.

print(result2.all_messages())
"""
[
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Tell me a joke.',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        instructions='Be a helpful assistant.',
        run_id='...',
        conversation_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='Did you hear about the toothpaste scandal? They called it Colgate.'
            )
        ],
        usage=RequestUsage(input_tokens=55, output_tokens=12),
        model_name='gpt-5.2',
        timestamp=datetime.datetime(...),
        run_id='...',
        conversation_id='...',
    ),
    ModelRequest(
        parts=[
            UserPromptPart(
                content='Explain?',
                timestamp=datetime.datetime(...),
            )
        ],
        timestamp=datetime.datetime(...),
        instructions='Be a helpful assistant.',
        run_id='...',
        conversation_id='...',
    ),
    ModelResponse(
        parts=[
            TextPart(
                content='This is an excellent joke invented by Samuel Colvin, it needs no explanation.'
            )
        ],
        usage=RequestUsage(input_tokens=56, output_tokens=26),
        model_name='gemini-3-pro-preview',
        timestamp=datetime.datetime(...),
        run_id='...',
        conversation_id='...',
    ),
]
"""
```

## 在 run 中途注入 messages {#injecting-messages-mid-run}

Tools、capability hooks 和驱动 agent run 的外部代码，可以使用 [`RunContext.enqueue`][pydantic_ai.tools.RunContext.enqueue]
（当 `RunContext` 在作用域中时，例如在 tool 或 capability hook 内）或
[`AgentRun.enqueue`][pydantic_ai.run.AgentRun.enqueue]（来自驱动
[`agent.iter()`][pydantic_ai.agent.AbstractAgent.iter] 的外部代码），在 run 中途向 conversation 注入额外内容。当 run 过程中发生了 agent 应该知道的事情时使用它：tool 想添加后续上下文、外部事件需要 *steer* agent 的计划，或后台工作完成后需要抵达 agent。

`priority` 控制 enqueued content 何时投递：

- `'asap'`（默认）：尽早投递；添加到下一个 [`ModelRequest`][pydantic_ai.messages.ModelRequest]，或者如果 agent 原本会在另一请求前终止，则用于将 run 重定向到再发起一次请求。当新上下文应尽快到达模型时使用；这也是其他 frameworks 常称为 in-flight agent **steering** 的行为。
- `'when_idle'`：仅当 agent 原本会终止时投递，在任何 `'asap'` messages 之后。当不应打断 agent，但希望它完成当前工作后接收新工作（一个 follow-up task）时使用。

`enqueue` 是 variadic 的；每个 positional argument 是一个 item，可以是：

- 一段 [`UserContent`][pydantic_ai.messages.UserContent]：`str` 或像 [`ImageUrl`][pydantic_ai.messages.ImageUrl] 这样的 multi-modal content。相邻的 user content 会聚合成单个 [`UserPromptPart`][pydantic_ai.messages.UserPromptPart]，因此 `enqueue('caption', image)` 会形成一个 user turn。要传入已有 list，请展开它：`enqueue(*items)`；
- 一个 [`ModelRequestPart`][pydantic_ai.messages.ModelRequestPart]，例如 [`SystemPromptPart`][pydantic_ai.messages.SystemPromptPart]；
- 一个完整的 [`ModelRequest`][pydantic_ai.messages.ModelRequest] 或 [`ModelResponse`][pydantic_ai.messages.ModelResponse]，用于控制 request-level fields（如 `instructions`/`metadata`）或注入 synthetic prior turn。

相邻的 part-style items（user content 和 [`ModelRequestPart`][pydantic_ai.messages.ModelRequestPart]s）会合并为一个 [`ModelRequest`][pydantic_ai.messages.ModelRequest]；完整 messages 会保持独立。这让一次调用可以注入交错 exchange，例如一个 synthetic tool call（[`ModelResponse`][pydantic_ai.messages.ModelResponse]）后跟它的结果（[`ModelRequest`][pydantic_ai.messages.ModelRequest]）。内容必须以 request 结束，这样 agent 才有内容可响应。

### 从 tool 或 hook 内部 {#from-inside-a-tool-or-hook}

当你有 `RunContext` 在作用域中时，使用 [`RunContext.enqueue`][pydantic_ai.tools.RunContext.enqueue]：

```python {title="enqueue_from_tool.py"}
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import SystemPromptPart

agent = Agent('anthropic:claude-opus-4-7')


@agent.tool
def trigger_alert(ctx: RunContext[None]) -> str:
    ctx.enqueue('Alert: production is degraded, prioritize triage.')
    return 'alert raised'


@agent.tool
def enter_incident_mode(ctx: RunContext[None]) -> str:
    # Enqueue a `SystemPromptPart` to adjust the agent's standing instructions mid-run.
    ctx.enqueue(SystemPromptPart(content='You are now in incident mode: be terse and action-oriented.'))
    return 'incident mode enabled'
```

`'asap'` message 会附加到 agent 的 message history 中，并在下一个请求中与同一步骤中的任何 tool returns 一起对模型可见。[`SystemPromptPart`][pydantic_ai.messages.SystemPromptPart] 也会以相同方式投递；在会 hoist system prompts 的 providers（例如 Anthropic、Google）上，非 leading 的 system prompt 会作为带 `<system>` 标签的 user-role message 发送，从而保留其中途对话位置，而不是被提升到顶部。

### 从驱动 `agent.iter()` 的外部代码 {#from-external-code-driving-agent-iter}

当你从外部驱动 run 时（例如从 webhook、chat platform 或 job queue 转发 events），使用 [`AgentRun.enqueue`][pydantic_ai.run.AgentRun.enqueue]：

```python {title="enqueue_from_agent_run.py"}
from pydantic_ai import Agent
from pydantic_graph import End

agent = Agent('anthropic:claude-opus-4-7')


async def main():
    async with agent.iter('Summarize the latest deploy report') as agent_run:
        # An external system pushes a follow-up while the agent is working.
        # When the agent would otherwise finish, the message redirects it
        # into a fresh model request so it can incorporate the new context.
        agent_run.enqueue(
            'A new error was just reported — include it in the summary.',
            priority='when_idle',
        )
        node = agent_run.next_node
        while not isinstance(node, End):
            node = await agent_run.next(node)
```

示例使用 [`agent.iter()`][pydantic_ai.agent.AbstractAgent.iter] +
[`AgentRun.next()`][pydantic_ai.run.AgentRun.next] 驱动 run，因为 `'when_idle'` messages 只有在 agent 原本会到达 `End` 时才会 drained；该 drain 发生在 `after_node_run` 中，
不会在裸 `async for node in agent_run:` loop 内触发。`'asap'` messages 在 `before_model_request` 中 drained（两种驱动方式都会触发），如果有内容在最终步骤期间到达，也会在同一个 end-of-run point drained。当一个裸 `async for` loop 结束时仍有未 drained pending messages，会引发 [`UndrainedPendingMessagesError`][pydantic_ai.exceptions.UndrainedPendingMessagesError]，
否则这些 messages 会被静默丢失。

!!! info "限制"
    - End-of-run redirects 需要 [`Agent.run`][pydantic_ai.agent.AbstractAgent.run] 或
      显式 [`AgentRun.next()`][pydantic_ai.run.AgentRun.next] 驱动；
      它们不会在裸 `async for node in agent_run:` loop 中 drained（如果以未 drained messages 结束，会引发
      [`UndrainedPendingMessagesError`][pydantic_ai.exceptions.UndrainedPendingMessagesError]）。
      投递到 `before_model_request` 的 messages 在两种情况下都可工作。
    - 在 [Temporal](durable_execution/temporal.md) workflow 内部，tools 运行在
      activities 中，并且不与 workflow 共享 state，因此 tool 中的 `ctx.enqueue`
      目前不会传播回 run。请改为从 workflow context（例如通过 `AgentRun.enqueue`）enqueue。
    - 每次 end-of-run redirect 都会打开新的 model request。如果某些东西在每个 step 都持续 enqueue
      （例如总是 enqueue 的 tool，或每次 reinjection 都重新 enqueue 的
      system-prompt callback），run 会无限循环。请在 run 上设置 [`UsageLimits`][pydantic_ai.usage.UsageLimits]
      作为安全网。
    - `enqueue` 设计为从驱动 agent run 的同一个 event loop 调用。
      在 run 内部这是自动的：async tools、sync tools（Pydantic AI 会自动用 thread executor 包装）和 capability hooks
      都可以安全 enqueue，因为 drain 只会在 graph nodes 之间迭代，从不会与 tool body 并发执行。
      如果你从*不同* thread 或 loop 转发 events（例如 webhook handler），请先把调用 marshal 到 agent 的
      loop 上，例如 `loop.call_soon_threadsafe(agent_run.enqueue, msg)`。
      drain 不会针对跨线程并发 append 保持 atomic。

## 处理 Message History {#processing-message-history}

有时你可能想在 message history 发送给模型前修改它。这可能出于隐私原因
（过滤敏感信息）、节省 token 成本、给 LLM 更少上下文，或自定义处理逻辑。

Pydantic AI 提供 [`ProcessHistory`][pydantic_ai.capabilities.ProcessHistory] capability，允许你在每次 model request 前拦截并修改 message history。

!!! note "`ProcessHistory` 是 `before_model_request` 上的一层薄包装"
    [`ProcessHistory`][pydantic_ai.capabilities.ProcessHistory] 是围绕 [`before_model_request`](hooks.md) lifecycle hook 的 migration-friendly wrapper。如果你想对 message history 进行更丰富的控制，例如访问完整的 [`RunContext`][pydantic_ai.tools.RunContext]
    和 [`ModelRequestContext`][pydantic_ai.models.ModelRequestContext]、短路 model call 等，请通过
    `capabilities=[Hooks(before_model_request=fn)]` 直接挂接事件。

!!! warning "History processors 会替换 message history"
    History processors 会用处理后的 messages 替换 state 中的 message history，包括新的 user prompt part。
    这意味着如果你想保留原始 message history，需要先复制一份。

!!! warning "History processors 可能影响 `new_messages()` 结果"
    [`new_messages()`][pydantic_ai.agent.AgentRunResult.new_messages] 返回当前 run 期间生成的 messages。
    通过 `message_history` 提供的 messages 会被排除，包括在没有 user prompt 的情况下继续时尾部的
    `ModelRequest`，即使 framework 可能为了 observability 给它标记当前 run 的 `run_id`。

    当 processor mutate 或添加 messages 时，为了保持这个行为可用：

    - 如果你重建尾部 `ModelRequest`，请保留其 `parts`、`timestamp`、
      `instructions` 和 `metadata`，以便它仍能被识别为 prior context。
    - 如果你插入的新 message 应该出现在 `new_messages()` 中，请使用
      [context-aware processor](#runcontext-parameter)，并在其上设置 `run_id=ctx.run_id`。

### 用法 {#history-processing-usage}

每个 [`ProcessHistory`][pydantic_ai.capabilities.ProcessHistory] 都包装一个 callable，该 callable 接受
[`ModelMessage`][pydantic_ai.messages.ModelMessage] list，并返回同类型的修改后 list。

Processors 会按顺序应用，并且可以是同步或异步的。

```python {title="simple_history_processor.py"}
from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.capabilities import ProcessHistory


def filter_responses(messages: list[ModelMessage]) -> list[ModelMessage]:
    """Remove all ModelResponse messages, keeping only ModelRequest messages."""
    return [msg for msg in messages if isinstance(msg, ModelRequest)]

# Create agent with history processor
agent = Agent('openai:gpt-5.2', capabilities=[ProcessHistory(filter_responses)])

# Example: Create some conversation history
message_history = [
    ModelRequest(parts=[UserPromptPart(content='What is 2+2?')]),
    ModelResponse(parts=[TextPart(content='2+2 equals 4')]),  # This will be filtered out
]

# When you run the agent, the history processor will filter out ModelResponse messages
# result = agent.run_sync('What about 3+3?', message_history=message_history)
```

#### 只保留最近 Messages {#keep-only-recent-messages}

你可以使用 `history_processor` 只保留最近 messages：

```python {title="keep_recent_messages.py"}
from pydantic_ai import Agent, ModelMessage
from pydantic_ai.capabilities import ProcessHistory


async def keep_recent_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    """Keep only the last 5 messages to manage token usage."""
    return messages[-5:] if len(messages) > 5 else messages

agent = Agent('openai:gpt-5.2', capabilities=[ProcessHistory(keep_recent_messages)])

# Example: Even with a long conversation history, only the last 5 messages are sent to the model
long_conversation_history: list[ModelMessage] = []  # Your long conversation history here
# result = agent.run_sync('What did we discuss?', message_history=long_conversation_history)
```

!!! warning "切片 message history 时要小心"
    切片 message history 时，需要确保 tool calls 和 returns 成对，否则 LLM 可能返回错误。更多细节请参阅[这个 GitHub issue](https://github.com/pydantic/pydantic-ai/issues/2050#issuecomment-3019976269)。

#### `RunContext` 参数 {#runcontext-parameter}

History processors 可以选择接受 [`RunContext`][pydantic_ai.tools.RunContext] 参数，以访问当前 run 的额外信息，例如 dependencies、model information 和 usage statistics：

```python {title="context_aware_processor.py"}
from pydantic_ai import Agent, ModelMessage, RunContext
from pydantic_ai.capabilities import ProcessHistory


def context_aware_processor(
    ctx: RunContext[None],
    messages: list[ModelMessage],
) -> list[ModelMessage]:
    # Access current usage
    current_tokens = ctx.usage.total_tokens

    # Filter messages based on context
    if current_tokens > 1000:
        return messages[-3:]  # Keep only recent messages when token usage is high
    return messages

agent = Agent('openai:gpt-5.2', capabilities=[ProcessHistory(context_aware_processor)])
```

这允许你根据 agent run 的当前 state 进行更复杂的 message processing。

#### 总结旧 Messages {#summarize-old-messages}

使用 LLM 总结较旧 messages，以在减少 tokens 的同时保留上下文。

```python {title="summarize_old_messages.py"}
from pydantic_ai import Agent, ModelMessage
from pydantic_ai.capabilities import ProcessHistory

# Use a cheaper model to summarize old messages.
summarize_agent = Agent(
    'openai:gpt-5-mini',
    instructions="""
Summarize this conversation, omitting small talk and unrelated topics.
Focus on the technical discussion and next steps.
""",
)


async def summarize_old_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    # Summarize the oldest 10 messages
    if len(messages) > 10:
        oldest_messages = messages[:10]
        summary = await summarize_agent.run(message_history=oldest_messages)
        # Return the last message and the summary
        return summary.new_messages() + messages[-1:]

    return messages


agent = Agent('openai:gpt-5.2', capabilities=[ProcessHistory(summarize_old_messages)])
```

!!! warning "总结 message history 时要小心"
    总结 message history 时，需要确保 tool calls 和 returns 成对，否则 LLM 可能返回错误。更多细节请参阅[这个 GitHub issue](https://github.com/pydantic/pydantic-ai/issues/2050#issuecomment-3019976269)，其中可以找到总结 message history 的示例。

### 测试 History Processors {#testing-history-processors}

你可以使用 [`FunctionModel`][pydantic_ai.models.function.FunctionModel] 测试实际发送给 model provider 的 messages：

```python {title="test_history_processor.py"}
import pytest

from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.capabilities import ProcessHistory
from pydantic_ai.models.function import AgentInfo, FunctionModel


@pytest.fixture
def received_messages() -> list[ModelMessage]:
    return []


@pytest.fixture
def function_model(received_messages: list[ModelMessage]) -> FunctionModel:
    def capture_model_function(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        # Capture the messages that the provider actually receives
        received_messages.clear()
        received_messages.extend(messages)
        return ModelResponse(parts=[TextPart(content='Provider response')])

    return FunctionModel(capture_model_function)


def test_history_processor(function_model: FunctionModel, received_messages: list[ModelMessage]):
    def filter_responses(messages: list[ModelMessage]) -> list[ModelMessage]:
        return [msg for msg in messages if isinstance(msg, ModelRequest)]

    agent = Agent(function_model, capabilities=[ProcessHistory(filter_responses)])

    message_history = [
        ModelRequest(parts=[UserPromptPart(content='Question 1')]),
        ModelResponse(parts=[TextPart(content='Answer 1')]),
    ]

    agent.run_sync('Question 2', message_history=message_history)
    assert received_messages == [
        ModelRequest(parts=[UserPromptPart(content='Question 1')]),
        ModelRequest(parts=[UserPromptPart(content='Question 2')]),
    ]
```

### 多个 Processors {#multiple-processors}

你也可以使用多个 processors：

```python {title="multiple_history_processors.py"}
from pydantic_ai import Agent, ModelMessage, ModelRequest
from pydantic_ai.capabilities import ProcessHistory


def filter_responses(messages: list[ModelMessage]) -> list[ModelMessage]:
    return [msg for msg in messages if isinstance(msg, ModelRequest)]


def summarize_old_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    return messages[-5:]


agent = Agent(
    'openai:gpt-5.2',
    capabilities=[ProcessHistory(filter_responses), ProcessHistory(summarize_old_messages)],
)
```

在这种情况下，会先应用 `filter_responses` processor，再应用
`summarize_old_messages` processor。

## 示例 {#examples}

有关在 conversations 中使用 messages 的更完整示例，请参阅 [chat app](examples/chat-app.md) 示例。
