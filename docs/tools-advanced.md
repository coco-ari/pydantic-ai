# 高级工具功能 {#advanced-tool-features}

本页介绍 Pydantic AI 中 function tools 的高级功能。基础工具用法请参阅 [Function Tools](tools.md) 文档。

## 工具输出 {#function-tool-output}

工具可以返回任何 Pydantic 能序列化为 JSON 的值；根据模型支持的 [multi-modal input](input.md) 类型，也可以返回音频、视频、图片或文档内容：

```python {title="function_tool_output.py"}
from datetime import datetime

from pydantic import BaseModel

from pydantic_ai import Agent, DocumentUrl, ImageUrl
from pydantic_ai.models.openai import OpenAIResponsesModel


class User(BaseModel):
    name: str
    age: int


agent = Agent(model=OpenAIResponsesModel('gpt-5.2'))


@agent.tool_plain
def get_current_time() -> datetime:
    return datetime.now()


@agent.tool_plain
def get_user() -> User:
    return User(name='John', age=30)


@agent.tool_plain
def get_company_logo() -> ImageUrl:
    return ImageUrl(url='https://iili.io/3Hs4FMg.png')


@agent.tool_plain
def get_document() -> DocumentUrl:
    return DocumentUrl(url='https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf')


result = agent.run_sync('What time is it?')
print(result.output)
#> The current time is 10:45 PM on April 17, 2025.

result = agent.run_sync('What is the user name?')
print(result.output)
#> The user's name is John.

result = agent.run_sync('What is the company name in the logo?')
print(result.output)
#> The company name in the logo is "Pydantic."

result = agent.run_sync('What is the main content of the document?')
print(result.output)
#> The document contains just the text "Dummy PDF file."
```

_（这个示例是完整的，可以"原样"运行）_

有些模型（例如 Gemini）原生支持半结构化返回值，而有些模型期望文本（OpenAI），但似乎同样能从数据中提取含义。如果返回 Python object 而模型期望字符串，该值会被序列化为 JSON。

### 高级工具返回值 {#advanced-tool-returns}

当你需要更细粒度控制工具返回值以及发送给模型的内容时，可以使用 [`ToolReturn`][pydantic_ai.messages.ToolReturn]。它在以下场景尤其有用：

- 将结构化返回值与发送给模型的额外内容分离
- 将内容作为单独 user message 显式发送，而不是放进 tool result
- 包含不应发送给 LLM 的额外 metadata

下面是一个 computer automation tool 示例，它捕获 screenshots 并提供视觉反馈：

```python {title="advanced_tool_return.py"}
from pydantic_ai import Agent, BinaryContent, ToolReturn
from pydantic_ai.models.test import TestModel

agent = Agent(TestModel())

@agent.tool_plain
def click_and_capture(x: int, y: int) -> ToolReturn:
    """Click at coordinates and show before/after screenshots."""
    before_screenshot = BinaryContent(data=b'\x89PNG', media_type='image/png')
    # perform_click(x, y)
    after_screenshot = BinaryContent(data=b'\x89PNG', media_type='image/png')
    return ToolReturn(
        return_value=f'Successfully clicked at ({x}, {y})',
        content=[
            'Before:',
            before_screenshot,
            'After:',
            after_screenshot,
        ],
        metadata={
            'coordinates': {'x': x, 'y': y},
            'action_type': 'click_and_capture',
        },
    )

# The model receives the rich visual content for analysis
# while your application can access the structured return_value and metadata
result = agent.run_sync('Click on the submit button and tell me what happened')
print(result.output)
#> {"click_and_capture":"Successfully clicked at (0, 0)"}
```

- **`return_value`**：tool response 中使用的实际返回值。它会被序列化，并作为工具结果发回给模型。它可以直接包含 multimodal content（见上面的[工具输出](#function-tool-output)）。
- **`content`**：在 tool result 之后作为**单独 user message** 发送的内容。当你明确希望内容位于 tool result 外部，或想组合结构化返回值和 rich content 时使用。
- **`metadata`**：应用可以访问、但不会发送给 LLM 的可选 metadata。它适合 logging、debugging 或额外处理。其他一些 AI frameworks 将此功能称为 "artifacts"。

这种分离让你既能向模型提供丰富上下文，也能为应用逻辑保留干净的结构化返回值。对于应该原生包含在 tool result 中的 multimodal content（当模型支持时），请直接从 tool function 返回，或放在 `return_value` 中（见上面的[工具输出](#function-tool-output)）。

## 自定义工具 Schema {#custom-tool-schema}

如果某个函数缺少合适文档（例如命名不佳、没有类型信息、docstring 很差、使用 `*args` 或 `**kwargs` 等），你仍然可以通过 [`Tool.from_schema`][pydantic_ai.tools.Tool.from_schema] 将它转换成 agent 能有效使用的工具。通过它，你可以直接为函数提供 name、description、JSON schema，以及函数是否接受 `RunContext`：

```python
from pydantic_ai import Agent, Tool
from pydantic_ai.models.test import TestModel


def foobar(**kwargs) -> str:
    return kwargs['a'] + kwargs['b']

tool = Tool.from_schema(
    function=foobar,
    name='sum',
    description='Sum two numbers.',
    json_schema={
        'additionalProperties': False,
        'properties': {
            'a': {'description': 'the first number', 'type': 'integer'},
            'b': {'description': 'the second number', 'type': 'integer'},
        },
        'required': ['a', 'b'],
        'type': 'object',
    },
    takes_ctx=False,
)

test_model = TestModel()
agent = Agent(test_model, tools=[tool])

result = agent.run_sync('testing...')
print(result.output)
#> {"sum":0}
```

请注意，工具参数不会执行验证，所有参数都会作为 keyword arguments 传入。

## 动态工具 {#tool-prepare}

工具可以选择定义另一个函数 `prepare`，它会在 run 的每一步被调用，用于定制传给模型的工具定义，或在该步骤完全省略该工具。

`prepare` method 可以通过任意工具注册机制的 `prepare` kwarg 注册：

- [`@agent.tool`][pydantic_ai.agent.Agent.tool] 装饰器
- [`@agent.tool_plain`][pydantic_ai.agent.Agent.tool_plain] 装饰器
- [`Tool`][pydantic_ai.tools.Tool] dataclass

`prepare` method 应为 [`ToolPrepareFunc`][pydantic_ai.tools.ToolPrepareFunc] 类型：一个接受 [`RunContext`][pydantic_ai.tools.RunContext] 和预构建 [`ToolDefinition`][pydantic_ai.tools.ToolDefinition] 的函数。它应返回原 `ToolDefinition`（可修改或不修改）、返回新的 `ToolDefinition`，或返回 `None` 表示该步骤不注册此工具。

下面是一个简单的 `prepare` method：仅当 dependency 值为 `42` 时才包含该工具。

与前一个示例一样，我们使用 [`TestModel`][pydantic_ai.models.test.TestModel] 演示行为，而不调用真实模型。

```python {title="tool_only_if_42.py"}

from pydantic_ai import Agent, RunContext, ToolDefinition

agent = Agent('test')


async def only_if_42(
    ctx: RunContext[int], tool_def: ToolDefinition
) -> ToolDefinition | None:
    if ctx.deps == 42:
        return tool_def


@agent.tool(prepare=only_if_42)
def hitchhiker(ctx: RunContext[int], answer: str) -> str:
    return f'{ctx.deps} {answer}'


result = agent.run_sync('testing...', deps=41)
print(result.output)
#> success (no tool calls)
result = agent.run_sync('testing...', deps=42)
print(result.output)
#> {"hitchhiker":"42 a"}
```

_（这个示例是完整的，可以"原样"运行）_

下面是一个更复杂的示例：根据 `deps` 的值修改 `name` 参数的 description。

为了展示不同写法，我们用 [`Tool`][pydantic_ai.tools.Tool] dataclass 创建这个工具。

```python {title="customize_name.py"}
from __future__ import annotations

from typing import Literal

from pydantic_ai import Agent, RunContext, Tool, ToolDefinition
from pydantic_ai.models.test import TestModel


def greet(name: str) -> str:
    return f'hello {name}'


async def prepare_greet(
    ctx: RunContext[Literal['human', 'machine']], tool_def: ToolDefinition
) -> ToolDefinition | None:
    d = f'Name of the {ctx.deps} to greet.'
    tool_def.parameters_json_schema['properties']['name']['description'] = d
    return tool_def


greet_tool = Tool(greet, prepare=prepare_greet)
test_model = TestModel()
agent = Agent(test_model, tools=[greet_tool], deps_type=Literal['human', 'machine'])

result = agent.run_sync('testing...', deps='human')
print(result.output)
#> {"greet":"hello a"}
print(test_model.last_model_request_parameters.function_tools)
"""
[
    ToolDefinition(
        name='greet',
        parameters_json_schema={
            'additionalProperties': False,
            'properties': {
                'name': {'type': 'string', 'description': 'Name of the human to greet.'}
            },
            'required': ['name'],
            'type': 'object',
        },
    )
]
"""
```

_（这个示例是完整的，可以"原样"运行）_

### Agent 级动态工具 {#prepare-tools}

除了 per-tool 的 `prepare` methods，你还可以定义 agent-wide 的 `prepare_tools` 函数。这个函数会在 run 的每一步被调用，并允许你过滤或修改该步骤 agent 可用的全部 tool definitions。若你想一次启用或禁用多个工具，或基于当前上下文应用全局逻辑，它尤其有用。

`prepare_tools` 函数应为 [`ToolsPrepareFunc`][pydantic_ai.tools.ToolsPrepareFunc] 类型，接受 [`RunContext`][pydantic_ai.tools.RunContext] 和 [`ToolDefinition`][pydantic_ai.tools.ToolDefinition] list，并返回新的 tool definitions list（或返回 `None` 以禁用该步骤的所有工具）。

!!! warning
    从 callback 返回 `None` 会禁用该步骤的**所有**工具，并发出 `PydanticAIDeprecationWarning`；它不是"保持不变并透传"的快捷方式。要保留所有工具，请返回 `tool_defs` 参数；若有意暴露零个工具，请返回 `[]`。

!!! note
    传给 `prepare_tools` 的 tool definitions list 包含普通 function tools 和 agent 上注册的任何 [toolsets](toolsets.md) 中的工具，但不包含 [output tools](output.md#tool-output)。
    要修改 output tools，可以改为设置 `prepare_output_tools` 函数。

下面是一个当模型是 OpenAI model 时让所有工具变为 strict 的示例：

```python {title="agent_prepare_tools_customize.py" noqa="I001"}
from dataclasses import replace

from pydantic_ai import Agent, RunContext, ToolDefinition
from pydantic_ai.capabilities import PrepareTools
from pydantic_ai.models.test import TestModel


async def turn_on_strict_if_openai(
    ctx: RunContext[None], tool_defs: list[ToolDefinition]
) -> list[ToolDefinition] | None:
    if ctx.model.system == 'openai':
        return [replace(tool_def, strict=True) for tool_def in tool_defs]
    return tool_defs


test_model = TestModel()
agent = Agent(test_model, capabilities=[PrepareTools(turn_on_strict_if_openai)])


@agent.tool_plain
def echo(message: str) -> str:
    return message


agent.run_sync('testing...')
assert test_model.last_model_request_parameters.function_tools[0].strict is None

# Set the system attribute of the test_model to 'openai'
test_model._system = 'openai'

agent.run_sync('testing with openai...')
assert test_model.last_model_request_parameters.function_tools[0].strict
```

_（这个示例是完整的，可以"原样"运行）_

下面是另一个示例：当 dependency（`ctx.deps`）为 `True` 时，按名称过滤掉工具：

```python {title="agent_prepare_tools_filter_out.py" noqa="I001"}

from pydantic_ai import Agent, RunContext, Tool, ToolDefinition
from pydantic_ai.capabilities import PrepareTools


def launch_potato(target: str) -> str:
    return f'Potato launched at {target}!'


async def filter_out_tools_by_name(
    ctx: RunContext[bool], tool_defs: list[ToolDefinition]
) -> list[ToolDefinition] | None:
    if ctx.deps:
        return [tool_def for tool_def in tool_defs if tool_def.name != 'launch_potato']
    return tool_defs


agent = Agent(
    'test',
    tools=[Tool(launch_potato)],
    capabilities=[PrepareTools(filter_out_tools_by_name)],
    deps_type=bool,
)

result = agent.run_sync('testing...', deps=False)
print(result.output)
#> {"launch_potato":"Potato launched at a!"}
result = agent.run_sync('testing...', deps=True)
print(result.output)
#> success (no tool calls)
```

_（这个示例是完整的，可以"原样"运行）_

你可以使用 `prepare_tools` 来：

- 根据当前 model、dependencies 或其他上下文动态启用或禁用工具
- 全局修改 tool definitions（例如将所有工具设置为 strict mode、修改 descriptions 等）

如果同时使用 per-tool `prepare` 和 agent-wide `prepare_tools`，会先对每个工具应用 per-tool `prepare`，然后用得到的 tool definitions list 调用 `prepare_tools`。

## Tool Choice 工具选择 {#tool-choice}

[`ModelSettings`][pydantic_ai.settings.ModelSettings] 中的 `tool_choice` 设置控制模型在请求期间可以使用哪些工具。它适合用于禁用工具、强制使用工具，或限制可用工具。

Pydantic AI 区分 **[function tools](tools.md)**（通过 `@agent.tool`、[toolsets](toolsets.md) 或 [MCP](mcp/client.md) 注册的工具）和 **output tools**（用于[结构化输出](output.md#tool-output)的内部工具）。

### 选项 {#options}

| 值 | 说明 |
| --- | --- |
| `'auto'`（默认） | 模型决定是否使用工具。所有工具可用。 |
| `'none'` | 禁用 function tools。模型可以返回文本或使用 output tools。 |
| `'required'` | 强制模型使用 function tool。它会排除 output tools，因此请通过 [capability](#dynamic-tool-choice-via-capabilities) 动态设置，或使用 [direct model requests](direct.md)；在 `agent.run()` 中静态设置会引发错误。 |
| `['tool_a', ...]` | 按名称限制为特定工具。它会排除 output tools，与 `'required'` 一样需要动态/直接请求。 |
| [`ToolOrOutput`][pydantic_ai.settings.ToolOrOutput]`(function_tools=['...'])` | 限制 function tools，同时自动包含所有 output tools。 |

### 示例 {#example}

```python
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_ai.settings import ToolOrOutput

agent = Agent(TestModel())


@agent.tool_plain
def get_weather(city: str) -> str:
    return f'Sunny in {city}'


@agent.tool_plain
def get_time(city: str) -> str:
    return f'12:00 in {city}'


# Pass tool_choice via model_settings
result = agent.run_sync('Hello', model_settings={'tool_choice': 'none'})

# Use ToolOrOutput to restrict to specific function tools while allowing output
result = agent.run_sync(
    'Hello', model_settings={'tool_choice': ToolOrOutput(function_tools=['get_weather'])}
)
```

### 通过 capabilities 动态选择工具 {#dynamic-tool-choice-via-capabilities}

`tool_choice='required'` 和 `['tool_a', ...]` 会排除 output tools，因此若*静态*设置任一值，会强制每一步都调用工具，让 agent 无法生成最终响应。当 Pydantic AI 在静态基线（[`Agent.run`][pydantic_ai.Agent.run] 的 `model_settings` 参数、agent 自身的 `model_settings`，或底层 model 的 defaults）上检测到这些值时，`agent.run()` 会引发 `UserError`。

要按步骤改变 `tool_choice`，例如第一步强制调用某个特定工具，然后让模型自行决定，请从 capability 的 [`get_model_settings`][pydantic_ai.capabilities.AbstractCapability.get_model_settings] 返回 callable。该 callable 会收到一个 [`RunContext`][pydantic_ai.tools.RunContext]，可完整访问 `ctx.messages` 和 `ctx.run_step`，因此可以检查 run 中已经发生的事情并自适应。

```python {title="force_first_call.py"}
from pydantic_ai import Agent, ModelSettings, RunContext
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.messages import ModelRequest, ToolReturnPart


class RequireFirstCall(AbstractCapability[None]):
    """Force `tool_name` to be called successfully before anything else."""

    def __init__(self, tool_name: str) -> None:
        self.tool_name = tool_name

    def get_model_settings(self):
        def settings(ctx: RunContext[None]) -> ModelSettings:
            called = any(
                isinstance(part, ToolReturnPart) and part.tool_name == self.tool_name
                for message in ctx.messages
                if isinstance(message, ModelRequest)
                for part in message.parts
            )
            if called:
                return ModelSettings()
            return ModelSettings(tool_choice=[self.tool_name])

        return settings


agent = Agent('openai:gpt-5.2', capabilities=[RequireFirstCall('get_weather')])


@agent.tool_plain
def get_weather(city: str) -> str:
    return f'Sunny in {city}'
```

由于 capability 提供的 settings 会按步骤解析，callable 返回的 `tool_choice` 被信任为可跨步骤变化，因此不会被 baseline validator 拒绝。对于没有 agent loop 的单次 model request，请改用 [`pydantic_ai.direct.model_request`][pydantic_ai.direct.model_request]。

### Provider 支持 {#provider-support}

所有 providers 都支持 `'auto'` 和 `'none'`。其他选项的关键差异如下：

| Provider | `'required'` | 特定工具 | 说明 |
| --- | :---: | :---: | --- |
| OpenAI | ✓ | ✓ | 完整支持 |
| Anthropic | ⚠️ | ⚠️ | thinking enabled 时不支持 |
| Google | ✓ | ✓ | |
| Bedrock | ✓ | Single only | 多个工具会 fallback 到 'any' mode |
| Groq/HuggingFace | ✓ | Single only | 多个工具会 fallback 到 'required' mode |
| Mistral | ✓ | ✓ | 将 `'required'` 映射到 `'any'` mode |
| xAI | ✓ | ✓ | 某些 models 可能不支持 forcing；会 fallback 到 'auto' |

### Prompt caching 影响 {#tool-choice-caching}

通过 `tool_choice` 限制可用工具集可能会让 provider prompt caches 失效，因为大多数 provider APIs 会基于完整 tools array 缓存。Pydantic AI 以两种方式限制工具集：

- **API-level filtering**（保留 cache）：发送完整 tools array，并告知 provider 只允许其中一个子集。OpenAI Responses（`allowed_tools`）、Google（`allowed_function_names`）以及 Bedrock 在强制单个工具时使用这种方式。
- **Client-side filtering**（破坏 cache）：在请求前裁剪 tools array。当 provider API 对给定情况没有原生 filter 时使用。

下表列出 Pydantic AI 必须 client-side filter、因此会破坏 cache 的情况：

| Provider | 会破坏 cache 的情况 |
| --- | --- |
| Anthropic | `tool_choice` 是多个工具的 list，或 thinking enabled 时的单个工具 |
| OpenAI Chat | `tool_choice` 是多个工具的 list，或模型不支持 forcing 时的单个工具 |
| Bedrock | `tool_choice` 是多个工具的 list，或 thinking enabled / 模型不支持 forcing 时的单个工具 |
| Groq / HuggingFace | `tool_choice` 是多个工具的 list |
| Mistral | `tool_choice` 是 list（任意大小），API 不接受特定 tool names |
| xAI | `tool_choice` 是多个工具的 list，或模型不支持 forcing 时的单个工具 |
| OpenAI Responses | 从不；`allowed_tools` 原生处理所有情况 |
| Google | 从不；`allowed_function_names` 原生处理所有情况 |

如果保留 cache hits 很重要，请优先选择标记为 "Never" 的 providers/cases，或使用 `ToolOrOutput`（它会保持完整集合），而不是 restrictive list。

## 工具执行和重试 {#tool-retries}

工具执行时，其参数（由 LLM 提供）会先使用 Pydantic 根据函数签名进行验证（可选使用 [validation context](output.md#validation-context)）。如果验证失败（例如类型错误或缺少必需参数），会引发 `ValidationError`，framework 会自动生成包含验证详情的 [`RetryPromptPart`][pydantic_ai.messages.RetryPromptPart]。该 prompt 会发回给 LLM，告知错误并允许它修正参数后重试 tool call。

除了自动验证错误，工具自己的内部逻辑也可以通过引发 [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] exception 显式请求重试。这适用于参数技术上有效，但执行期间出现问题的情况（例如 transient network error，或工具判断初次尝试需要修改）。

```python
from pydantic_ai import ModelRetry


def my_flaky_tool(query: str) -> str:
    if query == 'bad':
        # Tell the LLM the query was bad and it should try again
        raise ModelRetry("The query 'bad' is not allowed. Please provide a different query.")
    # ... process query ...
    return 'Success!'
```

引发 `ModelRetry` 也会生成包含 exception message 的 `RetryPromptPart`，并将其发回给 LLM 指导下一次尝试。`ValidationError` 和 `ModelRetry` 都遵守配置的 retry limit：可通过 [`Tool(max_retries=N)`][pydantic_ai.tools.Tool]（或 `@agent.tool(retries=N)`）按工具设置，通过 [`FunctionToolset(max_retries=N)`][pydantic_ai.toolsets.FunctionToolset] 按 toolset 设置，或通过 [`Agent(retries={'tools': N})`][pydantic_ai.agent.Agent.__init__] 按 agent 设置，并按此顺序确定优先级。

Tool retries 是**按工具**跟踪的：每个 function tool 都有自己的 counter，run 中没有共享的全局 "tool call" budget。当某个工具引发 `ModelRetry` 或其参数验证失败时，只会推进该工具自己的 counter。在 tool function 内部，[`ctx.max_retries`][pydantic_ai.tools.RunContext.max_retries] 反映该工具的 enforcement limit，而 [`ctx.retry`][pydantic_ai.tools.RunContext.retry] 是该工具自己的 counter。当工具耗尽 counter 时，run 会引发 [`UnexpectedModelBehavior`][pydantic_ai.exceptions.UnexpectedModelBehavior]，message 为 `'Tool {name!r} exceeded max retries count of {N}'`。用户提供的 toolsets 在未设置 per-toolset 值时，会继承 `Agent(retries={'tools': ...})` 作为默认值。

### 工具超时 {#tool-timeout}

你可以为工具执行设置 timeout，防止工具无限运行。如果工具超过 timeout，会被视为失败，并向模型发送 retry prompt（计入 retry limit）。

```python
import asyncio

from pydantic_ai import Agent

# Set a default timeout for all tools on the agent
agent = Agent('test', tool_timeout=30)


@agent.tool_plain
async def slow_tool() -> str:
    """This tool will use the agent's default timeout (30 seconds)."""
    await asyncio.sleep(10)
    return 'Done'


@agent.tool_plain(timeout=5)
async def fast_tool() -> str:
    """This tool has its own timeout (5 seconds) that overrides the agent default."""
    await asyncio.sleep(1)
    return 'Done'
```

- **Agent-level timeout**：在 [`Agent`][pydantic_ai.agent.Agent] 上设置 `tool_timeout`，为所有工具应用默认 timeout。
- **Per-tool timeout**：通过 [`@agent.tool`][pydantic_ai.agent.Agent.tool]、[`@agent.tool_plain`][pydantic_ai.agent.Agent.tool_plain] 或 [`Tool`][pydantic_ai.tools.Tool] dataclass 在单个工具上设置 `timeout`。它会覆盖 agent-level 默认值。

当 timeout 发生时，工具被视为失败，模型会收到 message 为 `"Timed out after {timeout} seconds."` 的 retry prompt。它和 validation errors 或显式 [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] exceptions 一样，会计入该工具的 retry limit。

### 自定义 Args Validator {#args-validator}

`args_validator` 参数允许你定义自定义验证：它会在 Pydantic schema validation 之后、工具执行之前运行。它适用于业务逻辑验证、跨字段验证，或在为 deferred tools 请求 [human approval](deferred-tools.md) 前验证参数。

Validator 的第一个参数是 [`RunContext`][pydantic_ai.tools.RunContext]，后面跟与 tool function 相同的参数。成功时返回 `None`，失败时引发 [`ModelRetry`][pydantic_ai.exceptions.ModelRetry]。

```python {title="args_validator_approval.py"}
from pydantic_ai import Agent, DeferredToolRequests, ModelRetry, RunContext

agent = Agent('test', deps_type=int, output_type=[str, DeferredToolRequests])


def validate_sum_limit(ctx: RunContext[int], x: int, y: int) -> None:
    """Validate that the sum doesn't exceed the limit from deps."""
    if x + y > ctx.deps:
        raise ModelRetry(f'Sum of x and y must not exceed {ctx.deps}')


# Validation runs *before* approval is requested, so the model can
# fix bad args without bothering the user.
@agent.tool(requires_approval=True, args_validator=validate_sum_limit)
def add_numbers(ctx: RunContext[int], x: int, y: int) -> int:
    """Add two numbers (sum must not exceed the configured limit)."""
    return x + y


result = agent.run_sync('add 5 and 3', deps=100)
assert isinstance(result.output, DeferredToolRequests)
# The validated args are ready for the user to approve
print(result.output.approvals[0].args)
#> {'x': 0, 'y': 0}
```

_（这个示例是完整的，可以"原样"运行）_

验证失败时，error message 会作为 retry prompt 发回给 LLM。它遵守工具上的 `retries` 设置。对于 [deferred tools](deferred-tools.md)，验证会在 deferral time 运行；只有参数有效的 tool calls 会被 deferred，验证失败会像普通工具一样触发 retry。

`args_validator` 参数可用于 [`@agent.tool`][pydantic_ai.agent.Agent.tool]、[`@agent.tool_plain`][pydantic_ai.agent.Agent.tool_plain]、[`Tool`][pydantic_ai.tools.Tool]、[`Tool.from_schema`][pydantic_ai.tools.Tool.from_schema] 和 [`FunctionToolset`][pydantic_ai.toolsets.function.FunctionToolset]。Validators 可以是同步或异步函数。

验证结果通过 [`FunctionToolCallEvent`][pydantic_ai.messages.FunctionToolCallEvent] 上的 `args_valid` 字段暴露。它反映所有验证：schema validation 和自定义 `args_validator` validation（如果已配置）。`True` 表示所有验证通过，`False` 表示验证失败，`None` 表示未执行验证（例如因为 `'early'` end strategy 跳过 tool calls，或 deferred tool calls 未执行就被解析）。

### 并行工具调用和并发 {#parallel-tool-calls-concurrency}

当模型在一个 response 中返回多个 tool calls 时，Pydantic AI 会使用 `asyncio.create_task` 并发调度它们。
如果工具需要 sequential/serial execution，可以在注册工具时传入 [`sequential`][pydantic_ai.tools.ToolDefinition.sequential] 标志，或用 [`with agent.parallel_tool_call_execution_mode('sequential')`][pydantic_ai.agent.AbstractAgent.parallel_tool_call_execution_mode] context manager 包裹 agent run。

Async functions 会在 event loop 上运行，sync functions 会被 offload 到 threads。为了获得最佳性能，除非你正在执行 blocking I/O（且没有办法使用 non-blocking library）或 CPU-bound work（例如 `numpy` 或 `scikit-learn` operations），请_始终_使用 async function，避免简单函数被不必要地 offload 到 threads。

#### 长运行 servers 的 thread executor {#thread-executor-for-long-running-servers}

默认情况下，sync functions 会通过 [`anyio.to_thread.run_sync`][anyio.to_thread.run_sync] offload 到 threads，这会按需创建短生命周期 threads。在长运行 servers（例如 FastAPI）中，这些 threads 在持续流量下可能累积，导致 memory growth。

要控制 thread lifecycle，请使用 [`ThreadExecutor`][pydantic_ai.capabilities.ThreadExecutor] capability（per-agent）或 [`Agent.using_thread_executor()`][pydantic_ai.agent.AbstractAgent.using_thread_executor] context manager（global）提供一个有界 [`ThreadPoolExecutor`][concurrent.futures.ThreadPoolExecutor]：

```python {test="skip"}
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from pydantic_ai import Agent
from pydantic_ai.capabilities import ThreadExecutor

# Per-agent: pass as a capability
executor = ThreadPoolExecutor(max_workers=16, thread_name_prefix='agent-worker')
agent = Agent('openai:gpt-5.2', capabilities=[ThreadExecutor(executor)])

# Global: wrap your server lifespan
@asynccontextmanager
async def lifespan(app):
    executor = ThreadPoolExecutor(max_workers=16)
    with Agent.using_thread_executor(executor):
        yield
    executor.shutdown(wait=True)
```

!!! note "限制工具执行"
    你可以使用 [`UsageLimits(tool_calls_limit=...)`](agent.md#usage-limits) 限制单次 run 内的 tool executions。Counter 只会在一次成功的工具调用后递增。用于[结构化输出](output.md)的 Output tools 不会计入 `tool_calls` metric。

#### Output Tool Calls {#output-tool-calls}

当模型在调用其他工具的同时并行调用 [output tool](output.md#tool-output) 时，agent 的 [`end_strategy`][pydantic_ai.agent.Agent.end_strategy] 参数会控制这些 tool calls 如何执行。
`'graceful'` strategy 确保即使找到 final result 后，也会执行所有 function tools，同时跳过剩余 output tools。`'exhaustive'` strategy 更进一步，也会执行所有 output tools。当工具有 side effects（例如 logging、发送 notifications 或更新 metrics）并且应始终执行时，两者都很有用。

有关 `end_strategy` 如何同时作用于 function tools 和 output tools 的更多信息，请参阅 [Output Tool](output.md#parallel-output-tool-calls) 文档。

## 工具搜索 {#tool-search}

拥有大量工具的 agents（例如暴露几十个 endpoints 的 [MCP servers](mcp/client.md)）会在真正工作前消耗大量 input tokens 来传递 tool definitions，而且当可用工具超过约 30-50 个时，tool selection accuracy 会明显下降。将工具标记为 deferred loading 会把它们从模型初始上下文中隐藏起来；当模型需要时，它会通过 keyword 发现 hidden tools。

适合在以下情况使用：

* agent 暴露约 10+ 个工具，或 tool definitions 超过约 10k tokens
* 工具覆盖不同领域（例如多个 MCP servers），且每个请求只相关其中一部分
* toolset 正在增长，你想保留余量

如果你只有少量高频工具，并且几乎每轮都会用到每个工具，则不要使用。把所有工具都 defer 只会增加一次 discovery round-trip，而没有收益。经验法则是：保持少数最常用工具 eager loaded，将长尾工具 defer。

要启用，请在单个 [`Tool`][pydantic_ai.tools.Tool] / [`@agent.tool`][pydantic_ai.agent.Agent.tool] / [`@agent.tool_plain`][pydantic_ai.agent.Agent.tool_plain] 注册上设置 `defer_loading=True`，或在整个 toolset（包括 [MCP servers](mcp/client.md) 和 [`FastMCPToolset`][pydantic_ai.toolsets.fastmcp.FastMCPToolset]）上使用 [`.defer_loading()`][pydantic_ai.toolsets.AbstractToolset.defer_loading]。传入 tool names list 可隐藏特定工具，传入 `None` 可隐藏所有工具。

一旦存在 deferred tools，search 会由自动注入的 [`ToolSearch`][pydantic_ai.capabilities.ToolSearch] capability 处理：

* **Native provider search**：支持模型上的原生搜索（Anthropic Sonnet 4.5+、Opus 4.5+、Haiku 4.5+ 通过 [BM25/regex](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)；OpenAI Responses on GPT-5.4+）。Deferred tools 会在 wire 上带着 `defer_loading` 发给 provider，由 provider 管理其可见性。
* **Custom callable**：通过 [`ToolSearch(strategy=...)`][pydantic_ai.capabilities.ToolSearch] 提供用户自定义 search function。它在我们这一侧执行，但在支持时会通过 provider 的 client-executed native surface（Anthropic `tool_reference` blocks、OpenAI `execution='client'`）路由，让模型看到 tool-search call，而不是普通 function tool。
* **Local fallback**：其他所有模型上使用 `search_tools` function tool，根据 tool names 和 descriptions 匹配 keywords。

Pydantic AI 优先使用 native search，因为 discovery exchange 是 append-only（一对 `tool_search_call` + `tool_search_output`）；deferred tools 永远不会进入 prompt prefix，因此 prompt caching 能跨 rounds 保留。相反，local fallback 会在 rounds 之间把每个已发现工具的 `defer_loading` 改为 `False`，从而改变 tool-definition prefix，并在每个 discovery turn 让 cached request prefix 失效。

为了让模型更好地找到工具，请使用描述性名称和一致 prefixes（`github_*`、`slack_*`、`mortgage_*`），并在工具 description 中放入用户可能搜索的 keywords。一次 search 会返回少量 matches，因此模型可能迭代（search -> discover -> call -> 再 search）；instructions 可以提示它："Search by topic when you don't see a tool you need."

```python {title="tool_search.py"}
from pydantic_ai import Agent

agent = Agent('anthropic:claude-sonnet-4-6')


@agent.tool_plain(defer_loading=True)
def mortgage_calculator(principal: float, rate: float, years: int) -> str:
    """Calculate monthly mortgage payment for a home loan."""
    monthly_rate = rate / 100 / 12
    n_payments = years * 12
    payment = principal * (monthly_rate * (1 + monthly_rate) ** n_payments) / ((1 + monthly_rate) ** n_payments - 1)
    return f'${payment:.2f}/month'
```

对于 MCP servers，使用 [`.defer_loading()`][pydantic_ai.toolsets.AbstractToolset.defer_loading] 将所有工具隐藏到 search 后面：

```python {title="tool_search_mcp.py" lint="skip" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerHTTP

mcp = MCPServerHTTP('http://localhost:8000/mcp')
agent = Agent('anthropic:claude-sonnet-4-6', toolsets=[mcp.defer_loading()])
```

### 配置 `ToolSearch` {#configuring-toolsearch}

传入显式 [`ToolSearch`][pydantic_ai.capabilities.ToolSearch] capability，可以控制 strategy 或提供自定义 search function：

```python {title="tool_search_custom.py"}
from collections.abc import Sequence

from pydantic_ai import Agent, RunContext
from pydantic_ai.capabilities import ToolSearch
from pydantic_ai.tools import ToolDefinition


def fuzzy_search(
    ctx: RunContext[None], queries: Sequence[str], tools: Sequence[ToolDefinition]
) -> list[str]:
    """Match tools whose name or description contains any query word."""
    needles = [n for q in queries for n in q.lower().split()]
    return [
        t.name
        for t in tools
        if any(n in t.name.lower() or n in (t.description or '').lower() for n in needles)
    ]


agent = Agent('anthropic:claude-sonnet-4-6', capabilities=[ToolSearch(strategy=fuzzy_search)])


@agent.tool_plain(defer_loading=True)
def mortgage_calculator(principal: float, rate: float, years: int) -> str:
    """Calculate monthly mortgage payment for a home loan."""
    monthly_rate = rate / 100 / 12
    n_payments = years * 12
    payment = principal * (monthly_rate * (1 + monthly_rate) ** n_payments) / ((1 + monthly_rate) ** n_payments - 1)
    return f'${payment:.2f}/month'
```

可用 strategy values：

| `strategy` | 算法 | 行为 |
| --- | --- | --- |
| `None`（默认） | provider 原生 algorithm（可用时），否则 local keyword matching | Anthropic 在 Sonnet 4.5+/Opus 4.5+/Haiku 4.5+ 上使用 native BM25；OpenAI 在 GPT-5.4+ 上使用 server-executed `tool_search`；其他地方使用 local keyword matching。 |
| `'keywords'` | Local keyword-overlap | keyword algorithm 在我们这一侧运行，但 wire shape 会适配：支持时使用 client-executed native（Anthropic、OpenAI），以保持 prompt cache 温热；其他地方使用普通 `search_tools` function tool。 |
| `'bm25'` / `'regex'` | Anthropic native | 由 Anthropic server-executed。其他 providers（OpenAI、Google 等）上的请求会失败，而不是静默替换成另一个 algorithm。 |
| Callable `(ctx, queries, tools) -> names` | User-defined | 与 `'keywords'` 相同的 execution-mode handling：支持 providers 上使用 client-executed native，其他地方使用 local `search_tools` function tool。 |

Execution mode（server-executed、client-executed-native 或 local fallback）会从所选 algorithm 和当前 provider 自动推导；用户不直接选择。只要可用，就优先使用 native execution，因为它能在 discovery rounds 之间保持模型看到的 tool list 稳定，从而保留 Anthropic 和 OpenAI prompt caching。

如果要在原生支持 tool search 的 provider 上强制使用 local `keywords` algorithm，请 override [`ModelProfile.supported_builtin_tools`][pydantic_ai.profiles.ModelProfile.supported_builtin_tools] 以排除 `ToolSearchTool`；该 capability 随后会 fall through 到 local `search_tools` function tool。

!!! note "跨 provider history replay"
    一个 turn 可以在某个 provider 上运行，而下一个 turn 在另一个 provider 上运行（例如通过 [`FallbackModel`][pydantic_ai.models.fallback.FallbackModel] 或在 runs 之间切换 `model=`）。Discovered-tool state 会跨切换保留：

    * Local-shape `search_tools` history 渲染到原生支持 provider（Anthropic、OpenAI）时，会提升为 provider 的 native tool-search wire，因此已发现工具的 schemas 会从 `defer_loading=True` 解锁，无需强制模型重新 search。
    * Native-shape `tool_search` history 渲染到不支持的 provider 时，会转换为 local `search_tools` function-tool exchange shape，让模型把 discoveries 看作普通 function-call exchange。

!!! note "工具发现和 message history"
    Discovered tools 通过 [message history](message-history.md) 中的 metadata 跟踪。如果 [history processor](message-history.md#processing-message-history) 截断了包含 discovery metadata 的 messages，之前发现的工具将需要重新 discovery。

更多细节请参阅 [`ToolDefinition.defer_loading`][pydantic_ai.tools.ToolDefinition.defer_loading] 和 [Deferred Loading](toolsets.md#deferred-loading)。

## 另请参阅 {#see-also}

- [Function Tools](tools.md) - 基础工具概念和注册
- [Toolsets](toolsets.md) - 管理工具集合
- [Deferred Tools](deferred-tools.md) - 需要 approval 或 external execution 的工具
- [Third-Party Tools](third-party-tools.md) - 与外部工具库的集成
