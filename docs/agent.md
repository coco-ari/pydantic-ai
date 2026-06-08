## 介绍 {#introduction}

Agents 是 Pydantic AI 与 LLMs 交互的主要接口。

在某些使用场景中，单个 Agent 会控制整个应用或组件；
多个 agents 也可以相互交互，以体现更复杂的 workflows。

[`Agent`][pydantic_ai.Agent] class 有完整的 API 文档，但从概念上看，你可以把 agent 理解为以下内容的容器：

| **组件**                                                  | **说明**                                                                                                  |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| [Instructions](#instructions)                             | 开发者为 LLM 编写的一组 instructions。                                                                    |
| [Function tool(s)](tools.md) 和 [toolsets](toolsets.md)   | LLM 在生成响应时可以调用以获取信息的 functions。                                                          |
| [Structured output type](output.md)                       | 如有指定，LLM 必须在 run 结束时返回的结构化数据类型。                                                     |
| [Dependency type constraint](dependencies.md)             | Dynamic instructions functions、tools 和 output functions 运行时都可以使用 dependencies。                 |
| [LLM model](api/models/base.md)                           | 与 agent 关联的可选默认 LLM model。也可以在运行 agent 时指定。                                            |
| [Model Settings](#additional-configuration)               | 用于微调请求的可选默认 model settings。也可以在运行 agent 时指定。                                        |
| [Capabilities](capabilities.md)                           | 可复用的 tools、hooks、instructions 和 model settings bundle，用于扩展 agent 行为。                       |

虽然这些内容都可以单独配置，[capabilities](capabilities.md) 允许你把相关行为打包成可复用单元，使其更容易组合、共享，并可[从配置文件加载](agent-spec.md)。

从类型角度看，agents 以 dependency type 和 output type 作为泛型参数。例如，一个需要 `#!python Foobar` 类型 dependencies、并生成 `#!python list[str]` 类型 outputs 的 agent，其类型会是 `Agent[Foobar, list[str]]`。实际使用中，你通常不需要关心这一点；它只是意味着 IDE 能在你使用正确类型时提供帮助，而且如果你选择使用[静态类型检查](#static-type-checking)，它会与 Pydantic AI 良好配合。

下面是一个模拟轮盘的 agent 玩具示例：

```python {title="roulette_wheel.py"}
from pydantic_ai import Agent, RunContext

roulette_agent = Agent(  # (1)!
    'openai:gpt-5.2',
    deps_type=int,
    output_type=bool,
    system_prompt=(
        'Use the `roulette_wheel` function to see if the '
        'customer has won based on the number they provide.'
    ),
)


@roulette_agent.tool
async def roulette_wheel(ctx: RunContext[int], square: int) -> str:  # (2)!
    """check if the square is a winner"""
    return 'winner' if square == ctx.deps else 'loser'


# Run the agent
success_number = 18  # (3)!
result = roulette_agent.run_sync('Put my money on square eighteen', deps=success_number)
print(result.output)  # (4)!
#> True

result = roulette_agent.run_sync('I bet five is the winner', deps=success_number)
print(result.output)
#> False
```

1. 创建一个 agent，它期望 integer dependency，并生成 boolean output。这个 agent 的类型会是 `#!python Agent[int, bool]`。
2. 定义一个 tool，用于检查某个 square 是否中奖。这里 [`RunContext`][pydantic_ai.tools.RunContext] 以 dependency type `int` 参数化；如果 dependency type 写错，就会得到 typing error。
3. 实际场景中，你可能会在这里使用随机数，例如 `random.randint(0, 36)`。
4. `result.output` 会是 boolean，表示该 square 是否中奖。Pydantic 会执行 output validation；由于其类型来自 agent 的 `output_type` 泛型参数，它会被标注为 `bool`。

!!! tip "Agents 被设计为可复用，类似 FastAPI Apps"
    你可以实例化一个 agent，并像使用小型 [FastAPI][fastapi.FastAPI] app 或 [APIRouter][fastapi.APIRouter] 一样在整个应用中全局使用它；也可以按需动态创建任意数量的 agents。这两种都是有效且受支持的 agent 使用方式。

## 运行 Agents {#running-agents}

运行 agent 有五种方式：

1. [`agent.run()`][pydantic_ai.agent.AbstractAgent.run]：async function，返回包含完整响应的 [`RunResult`][pydantic_ai.agent.AgentRunResult]。
2. [`agent.run_sync()`][pydantic_ai.agent.AbstractAgent.run_sync]：普通同步 function，返回包含完整响应的 [`RunResult`][pydantic_ai.agent.AgentRunResult]（内部只是调用 `loop.run_until_complete(self.run())`）。
3. [`agent.run_stream()`][pydantic_ai.agent.AbstractAgent.run_stream]：async context manager，返回 [`StreamedRunResult`][pydantic_ai.result.StreamedRunResult]，其中包含把文本和结构化 output 作为 async iterable 进行 stream 的 methods。[`agent.run_stream_sync()`][pydantic_ai.agent.AbstractAgent.run_stream_sync] 是同步变体，返回 [`StreamedRunResultSync`][pydantic_ai.result.StreamedRunResultSync]，其中包含同样 methods 的同步版本。
4. [`agent.run_stream_events()`][pydantic_ai.agent.AbstractAgent.run_stream_events]：返回 [`AgentEventStream`][pydantic_ai.result.AgentEventStream] async context manager 的 function；该 context manager 会 yield [`AgentStreamEvent`s][pydantic_ai.messages.AgentStreamEvent]，以及包含最终 run result 的 [`AgentRunResultEvent`][pydantic_ai.run.AgentRunResultEvent]。
5. [`agent.iter()`][pydantic_ai.agent.Agent.iter]：context manager，返回 [`AgentRun`][pydantic_ai.agent.AgentRun]，它是对 agent 底层 [`Graph`][pydantic_graph.graph_builder.Graph] nodes 的 async iterable。

下面用一个简单示例展示前四种方式：

```python {title="run_agent.py"}
from pydantic_ai import Agent, AgentRunResultEvent, AgentStreamEvent

agent = Agent('openai:gpt-5.2')

result_sync = agent.run_sync('What is the capital of Italy?')
print(result_sync.output)
#> The capital of Italy is Rome.


async def main():
    result = await agent.run('What is the capital of France?')
    print(result.output)
    #> The capital of France is Paris.

    async with agent.run_stream('What is the capital of the UK?') as response:
        async for text in response.stream_text():
            print(text)
            #> The capital of
            #> The capital of the UK is
            #> The capital of the UK is London.

    events: list[AgentStreamEvent | AgentRunResultEvent] = []
    async with agent.run_stream_events('What is the capital of Mexico?') as stream:
        async for event in stream:
            events.append(event)
    print(events)
    """
    [
        PartStartEvent(index=0, part=TextPart(content='The capital of ')),
        FinalResultEvent(tool_name=None, tool_call_id=None),
        PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='Mexico is Mexico ')),
        PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='City.')),
        PartEndEvent(
            index=0, part=TextPart(content='The capital of Mexico is Mexico City.')
        ),
        AgentRunResultEvent(
            result=AgentRunResult(output='The capital of Mexico is Mexico City.')
        ),
    ]
    """
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

你也可以传入之前 runs 的 messages 来继续对话或提供上下文，参见 [Messages and Chat History](message-history.md)。

### 流式 Events 与最终 Output {#streaming-events-and-final-output}

如上例所示，[`run_stream()`][pydantic_ai.agent.AbstractAgent.run_stream] 让你可以方便地随着接收过程 stream agent 的最终 output。
它还接受可选的 `event_stream_handler` argument，你可以用它观察最终 output 生成之前 run 内部正在发生的事情。

下面的示例展示如何 stream events 和 text output。你也可以 [stream structured output](output.md#streaming-structured-output)。

!!! note "注意"
    `run_stream()` 和 `run_stream_sync()` methods 会把第一个匹配 [output type](output.md#structured-output) 的 output（可能是文本、[output tool](output.md#tool-output) call，或 [deferred](deferred-tools.md) tool call）视为 agent run 的最终 output，即使模型在这个"最终" output 之后又生成了（额外的）tool calls。

    除非 agent 的 [`end_strategy`][pydantic_ai.agent.Agent.end_strategy] 设置为 `'graceful'` 或 `'exhaustive'`，否则这些 "dangling" tool calls 不会被执行；即使被执行，它们的结果也不会发送回模型，因为 agent run 已经被视为完成。简而言之，如果模型同时返回 tool calls 和文本，而 agent 的 output type 是 `str`，那么在默认设置下，streaming mode 中**不会运行这些 tool calls**。

    如果希望 agent 执行 tool calls 时始终继续运行，并 stream 模型 streaming response 和 agent 执行 tools 产生的所有 events，
    请改用后续章节介绍的 [`agent.run_stream_events()`][pydantic_ai.agent.AbstractAgent.run_stream_events] 或 [`agent.iter()`][pydantic_ai.agent.AbstractAgent.iter]。

```python {title="run_stream_event_stream_handler.py"}
import asyncio
from collections.abc import AsyncIterable
from datetime import date

from pydantic_ai import (
    Agent,
    AgentStreamEvent,
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    RunContext,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
)

weather_agent = Agent(
    'openai:gpt-5.2',
    system_prompt='Providing a weather forecast at the locations the user provides.',
)


@weather_agent.tool
async def weather_forecast(
    ctx: RunContext,
    location: str,
    forecast_date: date,
) -> str:
    return f'The forecast in {location} on {forecast_date} is 24°C and sunny.'


output_messages: list[str] = []

async def handle_event(event: AgentStreamEvent):
    if isinstance(event, PartStartEvent):
        output_messages.append(f'[Request] Starting part {event.index}: {event.part!r}')
    elif isinstance(event, PartDeltaEvent):
        if isinstance(event.delta, TextPartDelta):
            output_messages.append(f'[Request] Part {event.index} text delta: {event.delta.content_delta!r}')
        elif isinstance(event.delta, ThinkingPartDelta):
            output_messages.append(f'[Request] Part {event.index} thinking delta: {event.delta.content_delta!r}')
        elif isinstance(event.delta, ToolCallPartDelta):
            output_messages.append(f'[Request] Part {event.index} args delta: {event.delta.args_delta}')
    elif isinstance(event, FunctionToolCallEvent):
        output_messages.append(
            f'[Tools] The LLM calls tool={event.part.tool_name!r} with args={event.part.args} (tool_call_id={event.part.tool_call_id!r})'
        )
    elif isinstance(event, FunctionToolResultEvent):
        output_messages.append(f'[Tools] Tool call {event.tool_call_id!r} returned => {event.part.content}')
    elif isinstance(event, FinalResultEvent):
        output_messages.append(f'[Result] The model starting producing a final result (tool_name={event.tool_name})')


async def event_stream_handler(
    ctx: RunContext,
    event_stream: AsyncIterable[AgentStreamEvent],
):
    async for event in event_stream:
        await handle_event(event)

async def main():
    user_prompt = 'What will the weather be like in Paris on Tuesday?'

    async with weather_agent.run_stream(user_prompt, event_stream_handler=event_stream_handler) as run:
        async for output in run.stream_text():
            output_messages.append(f'[Output] {output}')


if __name__ == '__main__':
    asyncio.run(main())

    print(output_messages)
    """
    [
        "[Request] Starting part 0: ToolCallPart(tool_name='weather_forecast', tool_call_id='0001')",
        '[Request] Part 0 args delta: {"location":"Pa',
        '[Request] Part 0 args delta: ris","forecast_',
        '[Request] Part 0 args delta: date":"2030-01-',
        '[Request] Part 0 args delta: 01"}',
        '[Tools] The LLM calls tool=\'weather_forecast\' with args={"location":"Paris","forecast_date":"2030-01-01"} (tool_call_id=\'0001\')',
        "[Tools] Tool call '0001' returned => The forecast in Paris on 2030-01-01 is 24°C and sunny.",
        "[Request] Starting part 0: TextPart(content='It will be ')",
        '[Result] The model starting producing a final result (tool_name=None)',
        '[Output] It will be ',
        '[Output] It will be warm and sunny ',
        '[Output] It will be warm and sunny in Paris on ',
        '[Output] It will be warm and sunny in Paris on Tuesday.',
    ]
    """
```

_（这个示例是完整的，可以"原样"运行）_

### 流式传输所有 Events {#streaming-all-events}

与 `agent.run_stream()` 类似，[`agent.run()`][pydantic_ai.agent.AbstractAgent.run_stream] 接受可选的 `event_stream_handler`
argument，让你可以 stream 模型 streaming response 和 agent 执行 tools 产生的所有 events。
不同于 `run_stream()`，即使在 tool calls 之前收到了看起来可能是最终结果的文本，它也始终会把 agent graph 运行到完成。

为方便使用，还提供了 [`agent.run_stream_events()`][pydantic_ai.agent.AbstractAgent.run_stream_events] method，它是 `run(event_stream_handler=...)` 的 wrapper，返回 [`AgentEventStream`][pydantic_ai.result.AgentEventStream] async context manager；该 context manager 会 yield [`AgentStreamEvent`s][pydantic_ai.messages.AgentStreamEvent]，以及包含最终 run result 的 [`AgentRunResultEvent`][pydantic_ai.run.AgentRunResultEvent]。

!!! note "注意"
    由于 `run_stream_events()` 和 `run(event_stream_handler=...)` methods 会按原始 events 到达顺序返回它们，因此你需要自行从 `PartStartEvent` 和后续 `PartDeltaEvent`s 拼接 streamed text 与 structured output。

    如果愿意接受一些额外复杂度，以同时获得两种方式的优点，可以使用下一节介绍的 [`agent.iter()`][pydantic_ai.agent.AbstractAgent.iter]；它允许你在每一步[遍历 agent graph](#iterating-over-an-agents-graph)，并[同时 stream events 和 output](#streaming-all-events-and-output)。

```python {title="run_events.py" requires="run_stream_event_stream_handler.py"}
import asyncio

from pydantic_ai import AgentRunResultEvent

from run_stream_event_stream_handler import handle_event, output_messages, weather_agent


async def main():
    user_prompt = 'What will the weather be like in Paris on Tuesday?'

    async with weather_agent.run_stream_events(user_prompt) as stream:
        async for event in stream:
            if isinstance(event, AgentRunResultEvent):
                output_messages.append(f'[Final Output] {event.result.output}')
            else:
                await handle_event(event)

if __name__ == '__main__':
    asyncio.run(main())

    print(output_messages)
    """
    [
        "[Request] Starting part 0: ToolCallPart(tool_name='weather_forecast', tool_call_id='0001')",
        '[Request] Part 0 args delta: {"location":"Pa',
        '[Request] Part 0 args delta: ris","forecast_',
        '[Request] Part 0 args delta: date":"2030-01-',
        '[Request] Part 0 args delta: 01"}',
        '[Tools] The LLM calls tool=\'weather_forecast\' with args={"location":"Paris","forecast_date":"2030-01-01"} (tool_call_id=\'0001\')',
        "[Tools] Tool call '0001' returned => The forecast in Paris on 2030-01-01 is 24°C and sunny.",
        "[Request] Starting part 0: TextPart(content='It will be ')",
        '[Result] The model starting producing a final result (tool_name=None)',
        "[Request] Part 0 text delta: 'warm and sunny '",
        "[Request] Part 0 text delta: 'in Paris on '",
        "[Request] Part 0 text delta: 'Tuesday.'",
        '[Final Output] It will be warm and sunny in Paris on Tuesday.',
    ]
    """
```

_（这个示例是完整的，可以"原样"运行）_

### 遍历 Agent 的 Graph {#iterating-over-an-agents-graph}

在底层，Pydantic AI 中的每个 `Agent` 都使用 **pydantic-graph** 管理其 execution flow。**pydantic-graph** 是一个通用、以类型为中心的库，用于在 Python 中构建并运行有限状态机。它实际上并不依赖 Pydantic AI；你可以在与 GenAI 无关的 workflows 中单独使用它。但 Pydantic AI 会利用它，在 agent run 中编排 model requests 和 model responses 的处理。

在很多场景中，你完全不需要关心 pydantic-graph；调用 `agent.run(...)` 会从头到尾遍历底层 graph。不过，如果你需要更深入的观察或控制，例如在特定阶段注入自己的逻辑，Pydantic AI 会通过 [`Agent.iter`][pydantic_ai.agent.Agent.iter] 暴露更底层的 iteration process。该 method 返回 [`AgentRun`][pydantic_ai.agent.AgentRun]，你可以对它进行 async iteration，也可以通过 [`next`][pydantic_ai.agent.AgentRun.next] method 逐 node 手动驱动。一旦 agent 的 graph 返回 [`End`][pydantic_graph.basenode.End]，你就会得到最终结果，以及所有步骤的详细 history。

#### `async for` iteration（异步遍历） {#async-for-iteration}

下面的示例使用 `async for` 配合 `iter` 记录 agent 执行的每个 node：

```python {title="agent_iter_async_for.py"}
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')


async def main():
    nodes = []
    # Begin an AgentRun, which is an async-iterable over the nodes of the agent's graph
    async with agent.iter('What is the capital of France?') as agent_run:
        async for node in agent_run:
            # Each node represents a step in the agent's execution
            nodes.append(node)
    print(nodes)
    """
    [
        UserPromptNode(
            user_prompt='What is the capital of France?',
            instructions_functions=[],
            system_prompts=(),
            system_prompt_functions=[],
            system_prompt_dynamic_functions={},
        ),
        ModelRequestNode(
            request=ModelRequest(
                parts=[
                    UserPromptPart(
                        content='What is the capital of France?',
                        timestamp=datetime.datetime(...),
                    )
                ],
                timestamp=datetime.datetime(...),
                run_id='...',
                conversation_id='...',
            )
        ),
        CallToolsNode(
            model_response=ModelResponse(
                parts=[TextPart(content='The capital of France is Paris.')],
                usage=RequestUsage(input_tokens=56, output_tokens=7),
                model_name='gpt-5.2',
                timestamp=datetime.datetime(...),
                run_id='...',
                conversation_id='...',
            )
        ),
        End(data=FinalResult(output='The capital of France is Paris.')),
    ]
    """
    print(agent_run.result.output)
    #> The capital of France is Paris.
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

- `AgentRun` 是 async iterator，会 yield flow 中的每个 node（`BaseNode` 或 `End`）。
- 当返回 `End` node 时，run 结束。

#### 手动使用 `.next(...)` {#using-next-manually}

也可以把下一个想要运行的 node 传给 `AgentRun.next(...)` method 来手动驱动 iteration。这允许你在 node 执行前检查或修改它，或基于自己的逻辑跳过 nodes，也更容易捕获 `next()` 中的错误：

```python {title="agent_iter_next.py"}
from pydantic_ai import Agent
from pydantic_graph import End

agent = Agent('openai:gpt-5.2')


async def main():
    async with agent.iter('What is the capital of France?') as agent_run:
        node = agent_run.next_node  # (1)!

        all_nodes = [node]

        # Drive the iteration manually:
        while not isinstance(node, End):  # (2)!
            node = await agent_run.next(node)  # (3)!
            all_nodes.append(node)  # (4)!

        print(all_nodes)
        """
        [
            UserPromptNode(
                user_prompt='What is the capital of France?',
                instructions_functions=[],
                system_prompts=(),
                system_prompt_functions=[],
                system_prompt_dynamic_functions={},
            ),
            ModelRequestNode(
                request=ModelRequest(
                    parts=[
                        UserPromptPart(
                            content='What is the capital of France?',
                            timestamp=datetime.datetime(...),
                        )
                    ],
                    timestamp=datetime.datetime(...),
                    run_id='...',
                    conversation_id='...',
                )
            ),
            CallToolsNode(
                model_response=ModelResponse(
                    parts=[TextPart(content='The capital of France is Paris.')],
                    usage=RequestUsage(input_tokens=56, output_tokens=7),
                    model_name='gpt-5.2',
                    timestamp=datetime.datetime(...),
                    run_id='...',
                    conversation_id='...',
                )
            ),
            End(data=FinalResult(output='The capital of France is Paris.')),
        ]
        """
```

1. 首先获取 agent graph 中将要运行的第一个 node。
2. 一旦产生 `End` node，agent run 就完成；`End` instances 不能传给 `next`。
3. 调用 `await agent_run.next(node)` 时，会在 agent graph 中执行该 node、更新 run 的 history，并返回要运行的_下一个_ node。
4. 你也可以按需在这里检查或修改新的 `node`。

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

#### 访问 usage 和最终 output {#accessing-usage-and-final-output}

你可以随时通过 `agent_run.usage` 从 [`AgentRun`][pydantic_ai.agent.AgentRun] object 获取 usage statistics（tokens、requests 等）。该 property 返回包含 usage data 的 [`RunUsage`][pydantic_ai.usage.RunUsage] object。

run 完成后，`agent_run.result` 会变成 [`AgentRunResult`][pydantic_ai.agent.AgentRunResult] object，其中包含最终 output（以及相关 metadata）。

#### 流式传输所有 Events 和 Output {#streaming-all-events-and-output}

下面是把 agent run streaming 与 `async for` iteration 结合使用的示例：

```python {title="streaming_iter.py"}
import asyncio
from dataclasses import dataclass
from datetime import date

from pydantic_ai import (
    Agent,
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    RunContext,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
)


@dataclass
class WeatherService:
    async def get_forecast(self, location: str, forecast_date: date) -> str:
        # In real code: call weather API, DB queries, etc.
        return f'The forecast in {location} on {forecast_date} is 24°C and sunny.'

    async def get_historic_weather(self, location: str, forecast_date: date) -> str:
        # In real code: call a historical weather API or DB
        return f'The weather in {location} on {forecast_date} was 18°C and partly cloudy.'


weather_agent = Agent[WeatherService, str](
    'openai:gpt-5.2',
    deps_type=WeatherService,
    output_type=str,  # We'll produce a final answer as plain text
    system_prompt='Providing a weather forecast at the locations the user provides.',
)


@weather_agent.tool
async def weather_forecast(
    ctx: RunContext[WeatherService],
    location: str,
    forecast_date: date,
) -> str:
    if forecast_date >= date.today():
        return await ctx.deps.get_forecast(location, forecast_date)
    else:
        return await ctx.deps.get_historic_weather(location, forecast_date)


output_messages: list[str] = []


async def main():
    user_prompt = 'What will the weather be like in Paris on Tuesday?'

    # Begin a node-by-node, streaming iteration
    async with weather_agent.iter(user_prompt, deps=WeatherService()) as run:
        async for node in run:
            if Agent.is_user_prompt_node(node):
                # A user prompt node => The user has provided input
                output_messages.append(f'=== UserPromptNode: {node.user_prompt} ===')
            elif Agent.is_model_request_node(node):
                # A model request node => We can stream tokens from the model's request
                output_messages.append('=== ModelRequestNode: streaming partial request tokens ===')
                async with node.stream(run.ctx) as request_stream:
                    final_result_found = False
                    async for event in request_stream:
                        if isinstance(event, PartStartEvent):
                            output_messages.append(f'[Request] Starting part {event.index}: {event.part!r}')
                        elif isinstance(event, PartDeltaEvent):
                            if isinstance(event.delta, TextPartDelta):
                                output_messages.append(
                                    f'[Request] Part {event.index} text delta: {event.delta.content_delta!r}'
                                )
                            elif isinstance(event.delta, ThinkingPartDelta):
                                output_messages.append(
                                    f'[Request] Part {event.index} thinking delta: {event.delta.content_delta!r}'
                                )
                            elif isinstance(event.delta, ToolCallPartDelta):
                                output_messages.append(
                                    f'[Request] Part {event.index} args delta: {event.delta.args_delta}'
                                )
                        elif isinstance(event, FinalResultEvent):
                            output_messages.append(
                                f'[Result] The model started producing a final result (tool_name={event.tool_name})'
                            )
                            final_result_found = True
                            break

                    if final_result_found:
                        # Once the final result is found, we can call `AgentStream.stream_text()` to stream the text.
                        # A similar `AgentStream.stream_output()` method is available to stream structured output.
                        async for output in request_stream.stream_text():
                            output_messages.append(f'[Output] {output}')
            elif Agent.is_call_tools_node(node):
                # A handle-response node => The model returned some data, potentially calls a tool
                output_messages.append('=== CallToolsNode: streaming partial response & tool usage ===')
                async with node.stream(run.ctx) as handle_stream:
                    async for event in handle_stream:
                        if isinstance(event, FunctionToolCallEvent):
                            output_messages.append(
                                f'[Tools] The LLM calls tool={event.part.tool_name!r} with args={event.part.args} (tool_call_id={event.part.tool_call_id!r})'
                            )
                        elif isinstance(event, FunctionToolResultEvent):
                            output_messages.append(
                                f'[Tools] Tool call {event.tool_call_id!r} returned => {event.part.content}'
                            )
            elif Agent.is_end_node(node):
                # Once an End node is reached, the agent run is complete
                assert run.result is not None
                assert run.result.output == node.data.output
                output_messages.append(f'=== Final Agent Output: {run.result.output} ===')


if __name__ == '__main__':
    asyncio.run(main())

    print(output_messages)
    """
    [
        '=== UserPromptNode: What will the weather be like in Paris on Tuesday? ===',
        '=== ModelRequestNode: streaming partial request tokens ===',
        "[Request] Starting part 0: ToolCallPart(tool_name='weather_forecast', tool_call_id='0001')",
        '[Request] Part 0 args delta: {"location":"Pa',
        '[Request] Part 0 args delta: ris","forecast_',
        '[Request] Part 0 args delta: date":"2030-01-',
        '[Request] Part 0 args delta: 01"}',
        '=== CallToolsNode: streaming partial response & tool usage ===',
        '[Tools] The LLM calls tool=\'weather_forecast\' with args={"location":"Paris","forecast_date":"2030-01-01"} (tool_call_id=\'0001\')',
        "[Tools] Tool call '0001' returned => The forecast in Paris on 2030-01-01 is 24°C and sunny.",
        '=== ModelRequestNode: streaming partial request tokens ===',
        "[Request] Starting part 0: TextPart(content='It will be ')",
        '[Result] The model started producing a final result (tool_name=None)',
        '[Output] It will be ',
        '[Output] It will be warm and sunny ',
        '[Output] It will be warm and sunny in Paris on ',
        '[Output] It will be warm and sunny in Paris on Tuesday.',
        '=== CallToolsNode: streaming partial response & tool usage ===',
        '=== Final Agent Output: It will be warm and sunny in Paris on Tuesday. ===',
    ]
    """
```

_（这个示例是完整的，可以"原样"运行）_

### 其他配置 {#additional-configuration}

#### Usage Limits（用量限制） {#usage-limits}

Pydantic AI 提供 [`UsageLimits`][pydantic_ai.usage.UsageLimits] structure，帮助你限制 model runs 中的
usage（tokens、requests 和 tool calls）。

可以通过向 `run{_sync,_stream}` functions 传入 `usage_limits` argument 来应用这些 settings。

看下面的示例，我们在其中限制 response tokens 数量：

```py
from pydantic_ai import Agent, UsageLimitExceeded, UsageLimits

agent = Agent('anthropic:claude-sonnet-4-6')

result_sync = agent.run_sync(
    'What is the capital of Italy? Answer with just the city.',
    usage_limits=UsageLimits(response_tokens_limit=10),
)
print(result_sync.output)
#> Rome
print(result_sync.usage)
#> RunUsage(input_tokens=62, output_tokens=1, requests=1)

try:
    result_sync = agent.run_sync(
        'What is the capital of Italy? Answer with a paragraph.',
        usage_limits=UsageLimits(response_tokens_limit=10),
    )
except UsageLimitExceeded as e:
    print(e)
    #> Exceeded the output_tokens_limit of 10 (output_tokens=32)
```

限制 requests 数量有助于防止无限循环或过度 tool calling：

```py
from typing_extensions import TypedDict

from pydantic_ai import Agent, ModelRetry, UsageLimitExceeded, UsageLimits


class NeverOutputType(TypedDict):
    """
    Never ever coerce data to this type.
    """

    never_use_this: str


agent = Agent(
    'anthropic:claude-sonnet-4-6',
    retries={'tools': 3},
    output_type=NeverOutputType,
    system_prompt='Any time you get a response, call the `infinite_retry_tool` to produce another response.',
)


@agent.tool_plain(retries=5)  # (1)!
def infinite_retry_tool() -> int:
    raise ModelRetry('Please try again.')


try:
    result_sync = agent.run_sync(
        'Begin infinite retry loop!', usage_limits=UsageLimits(request_limit=3)  # (2)!
    )
except UsageLimitExceeded as e:
    print(e)
    #> The next request would exceed the request_limit of 3
```

1. 这个 tool 在报错前可以 retry 5 次，用于模拟可能卡在循环中的 tool。
2. 这个 run 会在 3 次 requests 后报错，从而阻止无限 tool calling。

##### 限制 tool calls 数量 {#capping-tool-calls}

如果需要限制单次 run 中成功 tool invocations 的数量，请使用 `tool_calls_limit`：

```py
from pydantic_ai import Agent
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.usage import UsageLimits

agent = Agent('anthropic:claude-sonnet-4-6')

@agent.tool_plain
def do_work() -> str:
    return 'ok'

try:
    # Allow at most one executed tool call in this run
    agent.run_sync('Please call the tool twice', usage_limits=UsageLimits(tool_calls_limit=1))
except UsageLimitExceeded as e:
    print(e)
    #> The next tool call(s) would exceed the tool_calls_limit of 1 (tool_calls=2).
```

!!! note "注意"
    - 如果注册了很多 tools，usage limits 尤其重要。使用 `request_limit` 约束 model turns 数量，使用 `tool_calls_limit` 限制 run 内成功 tool executions 的数量。
    - `tool_calls_limit` 会在执行 tool calls 前检查。如果模型返回的并行 tool calls 会超过限制，则不会执行任何 tools。

#### Model (Run) Settings（模型运行设置） {#model-run-settings}

Pydantic AI 提供 [`settings.ModelSettings`][pydantic_ai.settings.ModelSettings] structure，帮助你 fine tune requests。
该 structure 允许你配置影响模型行为的常见 parameters，例如 `temperature`、`max_tokens`、
`timeout` 等。

应用这些 settings 有三种方式，并且有明确的优先级顺序：

1. **Model-level defaults**：创建 model instance 时通过 `settings` parameter 设置。它们作为该 model 的基础默认值。
2. **Agent-level defaults**：初始化 [`Agent`][pydantic_ai.agent.Agent] 时通过 `model_settings` argument 设置。它们会与 model defaults 合并，并且 agent settings 优先。
3. **Run-time overrides**：通过 `model_settings` argument 传给 `run{_sync,_stream}` functions。它们优先级最高，并会与合并后的 agent 和 model defaults 再次合并。

例如，如果想把 `temperature` setting 设置为 `0.0`，以确保行为随机性更低，
可以这样做：

```py
from pydantic_ai import Agent, ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel

# 1. Model-level defaults
model = OpenAIChatModel(
    'gpt-5.2',
    settings=ModelSettings(temperature=0.8, max_tokens=500)  # Base defaults
)

# 2. Agent-level defaults (overrides model defaults by merging)
agent = Agent(model, model_settings=ModelSettings(temperature=0.5))

# 3. Run-time overrides (highest priority)
result_sync = agent.run_sync(
    'What is the capital of Italy?',
    model_settings=ModelSettings(temperature=0.0)  # Final temperature: 0.0
)
print(result_sync.output)
#> The capital of Italy is Rome.
```

最终请求使用 `temperature=0.0`（run-time）和 `max_tokens=500`（来自 model），展示了 settings 如何合并且 run-time 优先。

##### Dynamic model settings（动态模型设置） {#dynamic-model-settings}

agent-level 和 run-level 的 `model_settings` 都接受一个 callable，该 callable 接收
[`RunContext`][pydantic_ai.tools.RunContext] 并返回 [`ModelSettings`][pydantic_ai.settings.ModelSettings]。
callable 会在每次 model request 之前调用，因此 settings 可以按 step 变化。
在 callable 内部，可通过 `ctx.model_settings` 获取当前已经解析出的 settings。

Settings 会按层解析，每一层都合并到上一层之上：

1. **Model defaults（模型默认值）**（`model.settings`）
2. **Agent-level（Agent 级别）**（`Agent(model_settings=...)`）
3. **Capability-level**（例如来自 [`Thinking()`][pydantic_ai.capabilities.Thinking]；参见 [Capabilities](capabilities.md#providing-model-settings)）
4. **Run-level（Run 级别）**（`agent.run(model_settings=...)`）

在 callable 内部，`ctx.model_settings` 包含所有*之前*层的合并结果（与位置有关）。例如，agent-level callable 只能看到 model defaults，而 run-level callable 可以看到 model defaults + agent-level + capability-level settings。要重置前一层设置的 field，请显式设置它（例如 `{'temperature': None}`）。

```python
from pydantic_ai import Agent, ModelSettings

agent = Agent(
    'test',
    model_settings=lambda ctx: ModelSettings(
        temperature=0.0 if ctx.run_step <= 1 else 0.7,
    ),
)
```

!!! note "Model Settings 支持"
    所有具体 model implementations（OpenAI、Anthropic、Google 等）都支持 model-level settings。[`FallbackModel`](models/overview.md#fallback-model) 和 [`WrapperModel`][pydantic_ai.models.wrapper.WrapperModel] 这类 wrapper models 没有自己的 settings；它们使用底层 models 的 settings。

#### Run metadata（运行元数据） {#run-metadata}

Run metadata 允许你给每次 agent execution 标记上下文细节（例如用于过滤 traces 和 logs 的 tenant ID），
并在完成后通过 [`AgentRun.metadata`][pydantic_ai.agent.AgentRun]、
[`AgentRunResult.metadata`][pydantic_ai.agent.AgentRunResult] 或
[`StreamedRunResult.metadata`][pydantic_ai.result.StreamedRunResult] 读取它。
解析后的 metadata 会在 run 期间附加到 [`RunContext`][pydantic_ai.tools.RunContext]；
启用 instrumentation 时，也会添加到 run span attributes，供 observability tools 使用。

可以在 [`Agent`][pydantic_ai.agent.Agent] 上配置 metadata，也可以把它传给某次 run。
二者都接受 static dictionary，或接收 [`RunContext`][pydantic_ai.tools.RunContext] 的 callable。
如果 metadata 是 callable，它会在 run 开始时计算并应用，然后在 run 成功结束后重新计算，
因此可以包含 end-of-run values。
Agent-level metadata 和 per-run metadata 会合并，其中 per-run values 会覆盖 agent-level values。

```python {title="run_metadata.py"}
from dataclasses import dataclass

from pydantic_ai import Agent


@dataclass
class Deps:
    tenant: str


agent = Agent[Deps](
    'openai:gpt-5.2',
    deps_type=Deps,
    metadata=lambda ctx: {'tenant': ctx.deps.tenant},  # agent-level metadata
)

result = agent.run_sync(
    'What is the capital of France?',
    deps=Deps(tenant='tenant-123'),
    metadata=lambda ctx: {'num_requests': ctx.usage.requests},  # per-run metadata
)
print(result.output)
#> The capital of France is Paris.
print(result.metadata)
#> {'tenant': 'tenant-123', 'num_requests': 1}
```

#### 并发限制 {#concurrency-limiting}

可以使用 `max_concurrency` parameter 限制 concurrent agent runs 的数量。
当你并行运行很多 agent instances，并希望避免压垮外部资源或强制执行 rate limits 时，这很有用。

```python {title="agent_concurrency.py"}
import asyncio

from pydantic_ai import Agent, ConcurrencyLimit

# Simple limit: allow up to 10 concurrent runs
agent = Agent('openai:gpt-5', max_concurrency=10)


# With backpressure: limit concurrent runs and queue depth
agent_with_backpressure = Agent(
    'openai:gpt-5',
    max_concurrency=ConcurrencyLimit(max_running=10, max_queued=100),
)


async def main():
    # These will be rate-limited to 10 concurrent runs
    results = await asyncio.gather(
        *[agent.run(f'Question {i}') for i in range(20)]
    )
    print(len(results))
    #> 20
```

达到 concurrency limit 后，对 [`agent.run()`][pydantic_ai.agent.AbstractAgent.run] 或 [`agent.iter()`][pydantic_ai.agent.Agent.iter] 的额外调用
会等待直到有可用 slot。如果配置了 `max_queued` 且队列已满，
则会 raise [`ConcurrencyLimitExceeded`][pydantic_ai.exceptions.ConcurrencyLimitExceeded] exception。

启用 instrumentation 后，等待操作会显示为 "waiting for concurrency" spans，
并带有展示 queue depth 和 limits 的 attributes。

### Model-specific settings（模型特定设置） {#model-specific-settings}

如果想进一步自定义模型行为，可以使用与所选模型关联的 [`ModelSettings`][pydantic_ai.settings.ModelSettings] subclass，
例如 [`GoogleModelSettings`][pydantic_ai.models.google.GoogleModelSettings]。

例如：

```py
from pydantic_ai import Agent, UnexpectedModelBehavior
from pydantic_ai.models.google import GoogleModelSettings

agent = Agent('google:gemini-3-flash-preview')

try:
    result = agent.run_sync(
        'Write a list of 5 very rude things that I might say to the universe after stubbing my toe in the dark:',
        model_settings=GoogleModelSettings(
            temperature=0.0,  # general model settings can also be specified
            gemini_safety_settings=[
                {
                    'category': 'HARM_CATEGORY_HARASSMENT',
                    'threshold': 'BLOCK_LOW_AND_ABOVE',
                },
                {
                    'category': 'HARM_CATEGORY_HATE_SPEECH',
                    'threshold': 'BLOCK_LOW_AND_ABOVE',
                },
            ],
        ),
    )
except UnexpectedModelBehavior as e:
    print(e)  # (1)!
    """
    Content filter 'SAFETY' triggered, body:
    <safety settings details>
    """
```

1. 由于 safety thresholds 被超过，因此会 raise 这个错误。

## Runs 与 Conversations {#runs-vs-conversations}

一个 agent **run** 可以代表整段 conversation；单次 run 中可以交换的 messages 数量没有限制。不过，一个 **conversation** 也可以由多个 runs 组成，尤其是在你需要在独立 interactions 或 API calls 之间维护 state 时。

下面是由多个 runs 组成 conversation 的示例：

```python {title="conversation_example.py" hl_lines="13"}
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')

# First run
result1 = agent.run_sync('Who was Albert Einstein?')
print(result1.output)
#> Albert Einstein was a German-born theoretical physicist.

# Second run, passing previous messages
result2 = agent.run_sync(
    'What was his most famous equation?',
    message_history=result1.new_messages(),  # (1)!
)
print(result2.output)
#> Albert Einstein's most famous equation is (E = mc^2).
```

1. 继续 conversation；如果没有 `message_history`，模型不会知道 "his" 指的是谁。

_（这个示例是完整的，可以"原样"运行）_

## 设计上类型安全 {#static-type-checking}

Pydantic AI 被设计为能很好地配合 mypy 和 pyright 这类静态类型检查器。

!!! tip "Typing 在一定程度上是可选的"
    如果你选择使用类型检查，Pydantic AI 会尽可能让它对你有帮助；但你不必始终在所有地方都使用类型。

    话虽如此，由于 Pydantic AI 使用 Pydantic，而 Pydantic 使用 type hints 作为 schema 和 validation 的定义，一些类型会在运行时使用（具体来说，是 tools parameters 上的 type hints，以及传给 [`Agent`][pydantic_ai.Agent] 的 `output_type` arguments）。

    如果 type hints 带来的困惑多于帮助，那就是我们（库开发者）做错了；如果你遇到这种情况，请创建一个 [issue](https://github.com/pydantic/pydantic-ai/issues)，说明哪里让你困扰。

尤其是，agents 同时以 dependencies type 和返回 outputs type 作为泛型参数，因此你可以使用 type hints 来确保使用了正确类型。

看下面这个带有类型错误的脚本：

```python {title="type_mistakes.py" hl_lines="18 28"}
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext


@dataclass
class User:
    name: str


agent = Agent(
    'test',
    deps_type=User,  # (1)!
    output_type=bool,
)


@agent.system_prompt
def add_user_name(ctx: RunContext[str]) -> str:  # (2)!
    return f"The user's name is {ctx.deps}."


def foobar(x: bytes) -> None:
    pass


result = agent.run_sync('Does their name start with "A"?', deps=User('Anne'))
foobar(result.output)  # (3)!
```

1. 这个 agent 被定义为期望 `User` instance 作为 `deps`。
2. 但这里 `add_user_name` 被定义为接收 `str` 作为 dependency，而不是 `User`。
3. 由于 agent 被定义为返回 `bool`，而 `foobar` 期望 `bytes`，因此这里会产生 type error。

对它运行 `mypy` 会得到以下输出：

```bash
➤ uv run mypy type_mistakes.py
type_mistakes.py:18: error: Argument 1 to "system_prompt" of "Agent" has incompatible type "Callable[[RunContext[str]], str]"; expected "Callable[[RunContext[User]], str]"  [arg-type]
type_mistakes.py:28: error: Argument 1 to "foobar" has incompatible type "bool"; expected "bytes"  [arg-type]
Found 2 errors in 1 file (checked 1 source file)
```

运行 `pyright` 也会识别出相同问题。

## System Prompts（系统提示） {#system-prompts}

System prompts 乍看似乎很简单，因为它们只是 strings（或会拼接起来的一系列 strings），但编写正确的 system prompt 是让模型按你期望行为运行的关键。

!!! tip "提示"
    对大多数使用场景，应使用 `instructions` 而不是 "system prompts"。

    不过，如果你明确知道自己在做什么，并希望在后续 completions requests 发送给
    LLM 的 message history 中保留 system prompt messages，可以使用 `system_prompt` argument/decorator 实现。

    更多信息请参阅下面的 [Instructions](#instructions) 章节。

一般来说，system prompts 分为两类：

1. **Static system prompts**：在编写代码时就已知，可通过 [`Agent` constructor][pydantic_ai.agent.Agent.__init__] 的 `system_prompt` parameter 定义。
2. **Dynamic system prompts**：以某种方式依赖运行前未知的 context，应通过带 [`@agent.system_prompt`][pydantic_ai.agent.Agent.system_prompt] decorator 的 functions 定义。

两者都可以添加到单个 agent；它们会按运行时定义顺序追加。

下面是同时使用两类 system prompts 的示例：

```python {title="system_prompts.py"}
from datetime import date

from pydantic_ai import Agent, RunContext

agent = Agent(
    'openai:gpt-5.2',
    deps_type=str,  # (1)!
    system_prompt="Use the customer's name while replying to them.",  # (2)!
)


@agent.system_prompt  # (3)!
def add_the_users_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."


@agent.system_prompt
def add_the_date() -> str:  # (4)!
    return f'The date is {date.today()}.'


result = agent.run_sync('What is the date?', deps='Frank')
print(result.output)
#> Hello Frank, the date today is 2032-01-02.
```

1. 这个 agent 期望 string dependency。
2. 在 agent 创建时定义的 static system prompt。
3. 通过带 [`RunContext`][pydantic_ai.tools.RunContext] 的 decorator 定义的 dynamic system prompt；它在 `run_sync` 之后调用，而不是在 agent 创建时调用，因此可以利用该 run 使用的 dependencies 等运行时信息。
4. 另一个 dynamic system prompt；system prompts 不一定要有 `RunContext` parameter。

_（这个示例是完整的，可以"原样"运行）_

## Instructions（指令） {#instructions}

Instructions 类似于 system prompts。主要区别在于，当调用 `Agent.run` 及类似 methods 时显式提供 `message_history`，
history 中任何已有 messages 的 _instructions_ 不会包含在发送给模型的 request 中；
只会包含_当前_ agent 的 instructions。

你应该这样选择：

- 当你希望发送给模型的 request 只包含_当前_ agent 的 system prompts 时，使用 `instructions`
- 当你希望发送给模型的 request _保留_之前 requests（可能由其他 agents 发出）使用的 system prompts 时，使用 `system_prompt`

一般来说，除非你有使用 `system_prompt` 的特定理由，否则建议使用 `instructions`。

Instructions 和 system prompts 一样，可以在不同时间指定：

1. **Static instructions**：在编写代码时就已知，可通过 [`Agent` constructor][pydantic_ai.agent.Agent.__init__] 的 `instructions` parameter 定义。
2. **Dynamic instructions**：依赖仅在运行时可用的 context，应使用带 [`@agent.instructions`][pydantic_ai.agent.Agent.instructions] decorator 的 functions 定义。与 dynamic system prompts 不同，后者在存在 `message_history` 时可能被复用，而 dynamic instructions 始终会重新求值。
3. **Runtime instructions**：针对特定 run 的额外 instructions，可以用 `instructions` argument 传给某个 [run methods](#running-agents)。

三种 instructions 都可以添加到单个 agent，并会按运行时定义顺序追加。每条 instruction 在内部会被分类为 **static**（来自 `instructions` parameter 的字面量 strings）或 **dynamic**（来自 `@agent.instructions` functions、runtime instructions 或 [toolset](toolsets.md) instructions）。Static instructions 始终排在 dynamic instructions 之前。这种顺序让支持 prompt caching 的 providers（例如 [Anthropic](models/anthropic.md#smart-instruction-caching) 和 [Bedrock](models/bedrock.md#prompt-caching)）可以缓存稳定的 static prefix，同时把 dynamic instructions 留在 cache boundary 外部。

下面是同时使用 static instruction 和 dynamic instructions 的示例：

```python {title="instructions.py"}
from datetime import date

from pydantic_ai import Agent, RunContext

agent = Agent(
    'openai:gpt-5.2',
    deps_type=str,  # (1)!
    instructions="Use the customer's name while replying to them.",  # (2)!
)


@agent.instructions  # (3)!
def add_the_users_name(ctx: RunContext[str]) -> str:
    return f"The user's name is {ctx.deps}."


@agent.instructions
def add_the_date() -> str:  # (4)!
    return f'The date is {date.today()}.'


result = agent.run_sync('What is the date?', deps='Frank')
print(result.output)
#> Hello Frank, the date today is 2032-01-02.
```

1. 这个 agent 期望 string dependency。
2. 在 agent 创建时定义的 static instructions。
3. 通过带 [`RunContext`][pydantic_ai.tools.RunContext] 的 decorator 定义的 dynamic instructions；
   它在 `run_sync` 之后调用，而不是在 agent 创建时调用，因此可以利用该 run 使用的 dependencies 等运行时信息。
4. 另一个 dynamic instruction；instructions 不一定要有 `RunContext` parameter。

_（这个示例是完整的，可以"原样"运行）_

请注意，返回空字符串不会添加 instruction message。

Instructions 也可以来自 [capabilities](capabilities.md) 的 [`get_instructions()`][pydantic_ai.capabilities.AbstractCapability.get_instructions]，或来自基于 agent dependencies 渲染的 [template strings](agent-spec.md#template-strings)。

## 反思与自我纠正 {#reflection-and-self-correction}

function tool parameter validation 和 [structured output validation](output.md#structured-output) 产生的 validation errors 都可以传回模型，并请求模型重试。

你也可以在 [tool](tools.md) 或 [output function](output.md#output-functions) 内 raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry]，告诉模型应该重试生成响应。

- 默认 retry count 是 **1**，但可以用 `retries` 或 [`AgentRetries`][pydantic_ai.agent.AgentRetries] 为[整个 agent][pydantic_ai.agent.Agent.__init__] 修改，也可以为[特定 tool][pydantic_ai.agent.Agent.tool] 或 [outputs][pydantic_ai.agent.Agent.__init__] 修改。agent retry budget 中 output 侧的预算也可以通过 `agent.run(retries={'output': ...})` 等方式按 run 覆盖。
- 可以在 tool、output validator 或 output function 内通过 [`ctx.retry`][pydantic_ai.tools.RunContext.retry] 访问当前 retry count。

### Output retries 如何执行 {#how-output-retries-are-enforced}

Pydantic AI 会根据模型返回最终 output 的方式，以不同方式执行 output retry budget：

- **Text output path**（`output_type=str`、text-only outputs、空或不可用 model responses）：整个 run 共享一个全局预算。每个无效响应消耗一个预算单位；耗尽后，run 会 raise [`UnexpectedModelBehavior`][pydantic_ai.exceptions.UnexpectedModelBehavior]，message 为 `'Exceeded maximum output retries (N)'`。
- **Tool output path**（[`output_type=ToolOutput(...)`](output.md#tool-output)、structured outputs）：output retry budget 是*默认 per-tool limit*。通过 [`ToolOutput(max_retries=N)`][pydantic_ai.output.ToolOutput.max_retries] 按 tool 覆盖限制的方式参见 [Tool Output](output.md#tool-output)。

关于预算在 [output validators](output.md#output-validator-functions) 内如何呈现，包括 `ctx.max_retries` 和 `ctx.retry` 在各路径上反映什么，请参见 [Output validators](output.md#output-validator-functions) 章节。

Tool retries 会按 tool 跟踪；per-tool counter model 和三个配置层级请参见 [Tool Execution and Retries](tools-advanced.md#tool-retries)。

示例如下：

```python {title="tool_retry.py"}
from pydantic import BaseModel

from pydantic_ai import Agent, RunContext, ModelRetry

from fake_database import DatabaseConn


class ChatResult(BaseModel):
    user_id: int
    message: str


agent = Agent(
    'openai:gpt-5.2',
    deps_type=DatabaseConn,
    output_type=ChatResult,
)


@agent.tool(retries=2)
def get_user_by_name(ctx: RunContext[DatabaseConn], name: str) -> int:
    """Get a user's ID from their full name."""
    print(name)
    #> John
    #> John Doe
    user_id = ctx.deps.users.get(name=name)
    if user_id is None:
        raise ModelRetry(
            f'No user found with name {name!r}, remember to provide their full name'
        )
    return user_id


result = agent.run_sync(
    'Send a message to John Doe asking for coffee next week', deps=DatabaseConn()
)
print(result.output)
"""
user_id=123 message='Hello John, would you be free for coffee sometime next week? Let me know what works for you!'
"""
```

## 调试与监控 {#debugging-and-monitoring}

Agents 对 observability 的要求不同于传统软件。对于传统 web endpoints 或 data pipelines，通常可以通过阅读代码大致预测行为。但对 agents 来说，这要困难得多。模型决策具有随机性；随着 agent 进行 reasoning、调用 tools、观察结果并再次 reasoning，这种随机性会在 agentic loop 中叠加。你需要真正看到发生了什么。

这意味着需要设置应用，以一种之后可以回顾的方式记录正在发生的事情；这既适用于开发期间（用于理解和迭代），也适用于生产环境（用于 debug issues 和 monitor behavior）。易用性也很重要：把所有发生过的事情以纯文本 dump 出来，并不是审查 agent behavior 的实用方式，即便是在开发期间也是如此。你需要能交互式逐步查看每个 decision 和 tool call 的工具。

我们推荐 [Pydantic Logfire](https://logfire.pydantic.dev/docs/)，它是围绕 Pydantic AI workflows 设计的。

### 使用 Logfire 进行 Tracing {#tracing-with-logfire}

```python
import logfire

logfire.configure()
logfire.instrument_pydantic_ai()
```

启用 Logfire instrumentation 后，每个 agent run 都会创建详细 trace，展示：

- 与模型交换的 **Messages**（system、user、assistant）
- **Tool calls**，包括 arguments 和 return values
- 每个 request 以及累计的 **Token usage**
- 每个操作的 **Latency**
- 带完整上下文的 **Errors**

这种可见性对以下工作非常有价值：

- 理解 agent 为什么做出特定 decision
- 调试 unexpected behavior
- 优化 performance 和 costs
- 监控 production deployments

### 使用 Evals 进行系统化测试 {#systematic-testing-with-evals}

如果需要在 runtime debugging 之外系统化评估 agent behavior，[Pydantic Evals](evals.md) 提供了 code-first 的 AI systems 测试框架：

```python {test="skip" lint="skip" format="skip"}
from pydantic_evals import Case, Dataset

dataset = Dataset(
    name='agent_eval',
    cases=[
        Case(name='capital_question', inputs='What is the capital of France?', expected_output='Paris'),
    ]
)
report = dataset.evaluate_sync(my_agent_function)
```

Evals 允许你定义 test cases、针对 agent 运行它们，并为结果评分。结合 Logfire 使用时，evaluation results 会显示在 web UI 中，便于可视化并跨 runs 比较。设置方式请参阅 [Logfire integration guide](evals/how-to/logfire-integration.md)。

### 使用其他 Backends {#using-other-backends}

Pydantic AI 的 instrumentation 构建在 [OpenTelemetry](https://opentelemetry.io/) 之上，因此你可以把 traces 发送到任何兼容 backend。即使为了方便使用 Logfire SDK，也可以配置它把数据发送到其他 backends。设置说明请参阅 [alternative backends](logfire.md#using-opentelemetry)。

[完整 Logfire 集成指南 →](logfire.md)

## Model errors（模型错误） {#model-errors}

如果模型行为异常（例如超过 retry limit，或其 API 返回 `503`），agent runs 会 raise [`UnexpectedModelBehavior`][pydantic_ai.exceptions.UnexpectedModelBehavior]。

在这些情况下，可以使用 [`capture_run_messages`][pydantic_ai.capture_run_messages] 访问 run 期间交换的 messages，以帮助诊断问题。

```python {title="agent_model_errors.py"}
from pydantic_ai import Agent, ModelRetry, UnexpectedModelBehavior, capture_run_messages

agent = Agent('openai:gpt-5.2')


@agent.tool_plain
def calc_volume(size: int) -> int:  # (1)!
    if size == 42:
        return size**3
    else:
        raise ModelRetry('Please try again.')


with capture_run_messages() as messages:  # (2)!
    try:
        result = agent.run_sync('Please get me the volume of a box with size 6.')
    except UnexpectedModelBehavior as e:
        print('An error occurred:', e)
        #> An error occurred: Tool 'calc_volume' exceeded max retries count of 1
        print('cause:', repr(e.__cause__))
        #> cause: ModelRetry('Please try again.')
        print('messages:', messages)
        """
        messages:
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='Please get me the volume of a box with size 6.',
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
                        tool_name='calc_volume',
                        args={'size': 6},
                        tool_call_id='pyd_ai_tool_call_id',
                    )
                ],
                usage=RequestUsage(input_tokens=62, output_tokens=4),
                model_name='gpt-5.2',
                timestamp=datetime.datetime(...),
                run_id='...',
                conversation_id='...',
            ),
            ModelRequest(
                parts=[
                    RetryPromptPart(
                        content='Please try again.',
                        tool_name='calc_volume',
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
                    ToolCallPart(
                        tool_name='calc_volume',
                        args={'size': 6},
                        tool_call_id='pyd_ai_tool_call_id',
                    )
                ],
                usage=RequestUsage(input_tokens=72, output_tokens=8),
                model_name='gpt-5.2',
                timestamp=datetime.datetime(...),
                run_id='...',
                conversation_id='...',
            ),
        ]
        """
    else:
        print(result.output)
```

1. 定义一个在这种情况下会反复 raise `ModelRetry` 的 tool。
2. [`capture_run_messages`][pydantic_ai.capture_run_messages] 用于捕获 run 期间交换的 messages。

_（这个示例是完整的，可以"原样"运行）_

!!! note "注意"
    如果在单个 `capture_run_messages` context 内多次调用 [`run`][pydantic_ai.agent.AbstractAgent.run]、[`run_sync`][pydantic_ai.agent.AbstractAgent.run_sync] 或 [`run_stream`][pydantic_ai.agent.AbstractAgent.run_stream]，`messages` 只会表示第一次调用期间交换的 messages。

## Agent Specs（Agent 规范） {#agent-specs}

Agents 也可以使用 [agent specs](agent-spec.md) 以 YAML 或 JSON 声明式定义。这会把 agent configuration 与 application code 分离：

```yaml {test="skip"}
model: anthropic:claude-opus-4-6
instructions: You are a helpful assistant.
capabilities:
  - WebSearch
  - Thinking:
      effort: high
```

```python {test="skip" lint="skip"}
from pydantic_ai import Agent

agent = Agent.from_file('agent.yaml')
```

完整 spec format、template strings 和 custom capability registration 请参阅 [Agent Specs](agent-spec.md)。
