
# Toolsets（工具集） {#toolsets}

Toolset 表示一组可以一次性注册到 agent 上的 [tools](tools.md)。它们可以被不同 agents 复用，在运行时或测试期间替换，也可以组合起来动态过滤可用工具、修改 tool definitions，或改变工具执行行为。Toolset 可以包含本地定义的函数，也可以依赖外部服务来提供工具，或实现自定义逻辑来列出可用工具并处理工具调用。Toolsets 也可以通过 [capabilities](capabilities.md) 提供；capabilities 会把 tools 与 hooks、instructions 和 model settings 打包在一起。

Toolsets 的用途之一，是定义 agent 可用的 [MCP servers](mcp/client.md)。Pydantic AI 包含下文介绍的多种 toolsets；你也可以继承 [`AbstractToolset`][pydantic_ai.toolsets.AbstractToolset] class 来定义 [custom toolset](#building-a-custom-toolset)。

Agent run 期间可用的 toolsets 可以通过四种方式指定：

* 在 agent 构造时，通过传给 `Agent` 的 [`toolsets`][pydantic_ai.agent.Agent.__init__] keyword argument；它既接受 toolset instances，也接受基于 agent [run context][pydantic_ai.tools.RunContext] [动态](#dynamically-building-a-toolset)生成 toolsets 的函数
* 在 agent run 时，通过 [`agent.run()`][pydantic_ai.agent.AbstractAgent.run]、[`agent.run_sync()`][pydantic_ai.agent.AbstractAgent.run_sync]、[`agent.run_stream()`][pydantic_ai.agent.AbstractAgent.run_stream] 或 [`agent.iter()`][pydantic_ai.agent.Agent.iter] 的 `toolsets` keyword argument；这些 toolsets 会作为 `Agent` 上已注册 toolsets 的补充
* [动态](#dynamically-building-a-toolset)指定，通过 [`@agent.toolset`][pydantic_ai.agent.Agent.toolset] decorator，基于 agent [run context][pydantic_ai.tools.RunContext] 构建 toolset
* 作为 contextual override，通过 [`agent.override()`][pydantic_ai.agent.Agent.iter] context manager 的 `toolsets` keyword argument；在该 context manager 生命周期内，这些 toolsets 会替换 agent 构造或 run 时提供的 toolsets

```python {title="toolsets.py"}
from pydantic_ai import Agent, FunctionToolset
from pydantic_ai.models.test import TestModel


def agent_tool():
    return "I'm registered directly on the agent"


def extra_tool():
    return "I'm passed as an extra tool for a specific run"


def override_tool():
    return 'I override all other tools'


agent_toolset = FunctionToolset(tools=[agent_tool]) # (1)!
extra_toolset = FunctionToolset(tools=[extra_tool])
override_toolset = FunctionToolset(tools=[override_tool])

test_model = TestModel() # (2)!
agent = Agent(test_model, toolsets=[agent_toolset])

result = agent.run_sync('What tools are available?')
print([t.name for t in test_model.last_model_request_parameters.function_tools])
#> ['agent_tool']

result = agent.run_sync('What tools are available?', toolsets=[extra_toolset])
print([t.name for t in test_model.last_model_request_parameters.function_tools])
#> ['agent_tool', 'extra_tool']

with agent.override(toolsets=[override_toolset]):
    result = agent.run_sync('What tools are available?', toolsets=[extra_toolset]) # (3)!
    print([t.name for t in test_model.last_model_request_parameters.function_tools])
    #> ['override_tool']
```

1. 下一节会详细解释 [`FunctionToolset`][pydantic_ai.toolsets.FunctionToolset]。
2. 这里使用 [`TestModel`][pydantic_ai.models.test.TestModel]，因为它能方便地查看每次 run 中哪些工具可用。
3. 这个 `extra_toolset` 会被忽略，因为我们处在 override context 内。

_（这个示例是完整的，可以"原样"运行）_

## Function Toolset（函数工具集） {#function-toolset}

顾名思义，[`FunctionToolset`][pydantic_ai.toolsets.FunctionToolset] 会把本地定义的函数作为工具提供。

可以通过四种方式把 functions 添加为 tools：

* 通过 [`@toolset.tool`][pydantic_ai.toolsets.FunctionToolset.tool] decorator，用于需要访问 agent [context][pydantic_ai.tools.RunContext] 的工具
* 通过 [`@toolset.tool_plain`][pydantic_ai.toolsets.FunctionToolset.tool_plain] decorator，用于不需要访问 agent [context][pydantic_ai.tools.RunContext] 的工具
* 通过 constructor 的 [`tools`][pydantic_ai.toolsets.FunctionToolset.__init__] keyword argument；它可以接受普通 functions 或 [`Tool`][pydantic_ai.tools.Tool] instances
* 通过 [`toolset.add_function()`][pydantic_ai.toolsets.FunctionToolset.add_function] 和 [`toolset.add_tool()`][pydantic_ai.toolsets.FunctionToolset.add_tool] methods；它们分别可以接受普通 function 或 [`Tool`][pydantic_ai.tools.Tool] instance

`add_function()` 和 `add_tool()` methods 也可以在 tool function 内使用，以便在 run 期间动态注册新工具，供后续 run steps 使用。

```python {title="function_toolset.py"}
from datetime import datetime

from pydantic_ai import Agent, FunctionToolset, RunContext
from pydantic_ai.models.test import TestModel


def temperature_celsius(city: str) -> float:
    return 21.0


def temperature_fahrenheit(city: str) -> float:
    return 69.8


weather_toolset = FunctionToolset(tools=[temperature_celsius, temperature_fahrenheit])


@weather_toolset.tool
def conditions(ctx: RunContext, city: str) -> str:
    if ctx.run_step % 2 == 0:
        return "It's sunny"
    else:
        return "It's raining"


datetime_toolset = FunctionToolset()
datetime_toolset.add_function(lambda: datetime.now(), name='now')

test_model = TestModel()  # (1)!
agent = Agent(test_model)

result = agent.run_sync('What tools are available?', toolsets=[weather_toolset])
print([t.name for t in test_model.last_model_request_parameters.function_tools])
#> ['temperature_celsius', 'temperature_fahrenheit', 'conditions']

result = agent.run_sync('What tools are available?', toolsets=[datetime_toolset])
print([t.name for t in test_model.last_model_request_parameters.function_tools])
#> ['now']
```

1. 这里使用 [`TestModel`][pydantic_ai.models.test.TestModel]，因为它能方便地查看每次 run 中哪些工具可用。

_（这个示例是完整的，可以"原样"运行）_

### Toolset Instructions（工具集指令） {#toolset-instructions}

[`FunctionToolset`][pydantic_ai.toolsets.FunctionToolset] 可以提供自动包含在 model request 中的 instructions。这样每个 toolset 都能在携带工具的同时携带自己的使用指引，你无需在每个使用该 toolset 的 agent 上重复 instructions。

Instructions 可以作为 strings、functions（sync 或 async，带或不带 [`RunContext`][pydantic_ai.tools.RunContext]），或两者混合提供：

```python {title="toolset_instructions.py"}
from pydantic_ai import Agent, FunctionToolset
from pydantic_ai.models.test import TestModel

search_toolset = FunctionToolset(
    instructions='Always use the search tool before answering factual questions.',
)


@search_toolset.tool_plain
def search(query: str) -> str:
    """Search for information."""
    return f'Results for: {query}'


test_model = TestModel()
agent = Agent(test_model, toolsets=[search_toolset])
result = agent.run_sync('What is the capital of France?')
print(result.all_messages()[0].instructions)
#> Always use the search tool before answering factual questions.
```

_（这个示例是完整的，可以"原样"运行）_

你也可以使用 [`@toolset.instructions`][pydantic_ai.toolsets.FunctionToolset.instructions] decorator 注册可访问 run context 的动态 instruction functions：

```python {title="toolset_instructions_decorator.py"}
from pydantic_ai import Agent, FunctionToolset, RunContext
from pydantic_ai.models.test import TestModel

math_toolset = FunctionToolset[str]()


@math_toolset.instructions
def math_instructions(ctx: RunContext[str]) -> str:
    return f'You are helping: {ctx.deps}. Always show your work when using the calculator.'


@math_toolset.tool_plain
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    return '4'


test_model = TestModel()
agent = Agent(test_model, toolsets=[math_toolset], deps_type=str)
result = agent.run_sync('What is 2+2?', deps='Alice')
print(result.all_messages()[0].instructions)
#> You are helping: Alice. Always show your work when using the calculator.
```

_（这个示例是完整的，可以"原样"运行）_

当带 instructions 的 toolset 与 agent-level [`instructions`][pydantic_ai.agent.Agent.__init__] 一起使用时，toolset instructions 会追加在 agent instructions 之后：

```python {title="toolset_instructions_combined.py"}
from pydantic_ai import Agent, FunctionToolset
from pydantic_ai.models.test import TestModel

toolset = FunctionToolset(instructions='Use the greeting tool for all greetings.')


@toolset.tool_plain
def greeting(name: str) -> str:
    """Greet someone."""
    return f'Hello, {name}!'


test_model = TestModel()
agent = Agent(
    test_model,
    instructions='You are a friendly assistant.',
    toolsets=[toolset],
)
result = agent.run_sync('Hi there!')
print(result.all_messages()[0].instructions)
"""
You are a friendly assistant.

Use the greeting tool for all greetings.
"""
```

_（这个示例是完整的，可以"原样"运行）_

当多个带 instructions 的 toolsets 注册到同一个 agent 上时，它们的 instructions 会被组合起来：

```python {title="toolset_instructions_multiple.py"}
from pydantic_ai import Agent, FunctionToolset
from pydantic_ai.models.test import TestModel

weather_toolset = FunctionToolset(instructions='Use weather tools for forecasts.')


@weather_toolset.tool_plain
def forecast(city: str) -> str:
    """Get weather forecast."""
    return 'Sunny'


calendar_toolset = FunctionToolset(instructions='Use calendar tools for scheduling.')


@calendar_toolset.tool_plain
def schedule(event: str) -> str:
    """Schedule an event."""
    return 'Scheduled'


test_model = TestModel()
agent = Agent(test_model, toolsets=[weather_toolset, calendar_toolset])
result = agent.run_sync('Plan my day')
print(result.all_messages()[0].instructions)
"""
Use weather tools for forecasts.

Use calendar tools for scheduling.
"""
```

_（这个示例是完整的，可以"原样"运行）_

## Toolset Composition（组合） {#toolset-composition}

Toolsets 可以被组合起来，以动态过滤可用工具、修改 tool definitions，或改变工具执行行为。多个 toolsets 也可以组合成一个。

### 组合 Toolsets {#combining-toolsets}

[`CombinedToolset`][pydantic_ai.toolsets.CombinedToolset] 接受一组 toolsets，并让它们像一个 toolset 一样使用。

```python {title="combined_toolset.py" requires="function_toolset.py"}
from pydantic_ai import Agent, CombinedToolset
from pydantic_ai.models.test import TestModel

from function_toolset import datetime_toolset, weather_toolset

combined_toolset = CombinedToolset([weather_toolset, datetime_toolset])

test_model = TestModel() # (1)!
agent = Agent(test_model, toolsets=[combined_toolset])
result = agent.run_sync('What tools are available?')
print([t.name for t in test_model.last_model_request_parameters.function_tools])
#> ['temperature_celsius', 'temperature_fahrenheit', 'conditions', 'now']
```

1. 这里使用 [`TestModel`][pydantic_ai.models.test.TestModel]，因为它能方便地查看每次 run 中哪些工具可用。

_（这个示例是完整的，可以"原样"运行）_

### 过滤工具 {#filtering-tools}

[`FilteredToolset`][pydantic_ai.toolsets.FilteredToolset] 会包装一个 toolset，并在每个 run step 之前根据用户定义函数过滤可用工具。该函数会收到 agent [run context][pydantic_ai.tools.RunContext] 和每个工具的 [`ToolDefinition`][pydantic_ai.tools.ToolDefinition]，并返回 boolean 表示某个工具是否应当可用。

为了方便串联不同修改，你也可以在任意 toolset 上调用 [`filtered()`][pydantic_ai.toolsets.AbstractToolset.filtered]，而不是直接构造 `FilteredToolset`。

```python {title="filtered_toolset.py" requires="function_toolset.py,combined_toolset.py"}
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from combined_toolset import combined_toolset

filtered_toolset = combined_toolset.filtered(lambda ctx, tool_def: 'fahrenheit' not in tool_def.name)

test_model = TestModel() # (1)!
agent = Agent(test_model, toolsets=[filtered_toolset])
result = agent.run_sync('What tools are available?')
print([t.name for t in test_model.last_model_request_parameters.function_tools])
#> ['weather_temperature_celsius', 'weather_conditions', 'datetime_now']
```

1. 这里使用 [`TestModel`][pydantic_ai.models.test.TestModel]，因为它能方便地查看每次 run 中哪些工具可用。

_（这个示例是完整的，可以"原样"运行）_

### 为工具名称添加前缀 {#prefixing-tool-names}

[`PrefixedToolset`][pydantic_ai.toolsets.PrefixedToolset] 会包装一个 toolset，并为每个 tool name 添加前缀，以防止不同 toolsets 之间的工具名冲突。

为了方便串联不同修改，你也可以在任意 toolset 上调用 [`prefixed()`][pydantic_ai.toolsets.AbstractToolset.prefixed]，而不是直接构造 `PrefixedToolset`。

```python {title="combined_toolset.py" requires="function_toolset.py"}
from pydantic_ai import Agent, CombinedToolset
from pydantic_ai.models.test import TestModel

from function_toolset import datetime_toolset, weather_toolset

combined_toolset = CombinedToolset(
    [
        weather_toolset.prefixed('weather'),
        datetime_toolset.prefixed('datetime')
    ]
)

test_model = TestModel() # (1)!
agent = Agent(test_model, toolsets=[combined_toolset])
result = agent.run_sync('What tools are available?')
print([t.name for t in test_model.last_model_request_parameters.function_tools])
"""
[
    'weather_temperature_celsius',
    'weather_temperature_fahrenheit',
    'weather_conditions',
    'datetime_now',
]
"""
```

1. 这里使用 [`TestModel`][pydantic_ai.models.test.TestModel]，因为它能方便地查看每次 run 中哪些工具可用。

_（这个示例是完整的，可以"原样"运行）_

### 重命名工具 {#renaming-tools}

[`RenamedToolset`][pydantic_ai.toolsets.RenamedToolset] 会包装一个 toolset，并允许你用一个从新名称映射到原名称的 dictionary 重命名工具。当某个 toolset 提供的名称含糊，或会与其他 toolsets 定义的工具冲突，但[添加前缀](#prefixing-tool-names)又会生成不必要的长名称或让模型困惑时，这很有用。

为了方便串联不同修改，你也可以在任意 toolset 上调用 [`renamed()`][pydantic_ai.toolsets.AbstractToolset.renamed]，而不是直接构造 `RenamedToolset`。

```python {title="renamed_toolset.py" requires="function_toolset.py,combined_toolset.py"}
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

from combined_toolset import combined_toolset

renamed_toolset = combined_toolset.renamed(
    {
        'current_time': 'datetime_now',
        'temperature_celsius': 'weather_temperature_celsius',
        'temperature_fahrenheit': 'weather_temperature_fahrenheit'
    }
)

test_model = TestModel() # (1)!
agent = Agent(test_model, toolsets=[renamed_toolset])
result = agent.run_sync('What tools are available?')
print([t.name for t in test_model.last_model_request_parameters.function_tools])
"""
['temperature_celsius', 'temperature_fahrenheit', 'weather_conditions', 'current_time']
"""
```

1. 这里使用 [`TestModel`][pydantic_ai.models.test.TestModel]，因为它能方便地查看每次 run 中哪些工具可用。

_（这个示例是完整的，可以"原样"运行）_

### 动态 Tool Definitions {#preparing-tool-definitions}

[`PreparedToolset`][pydantic_ai.toolsets.PreparedToolset] 允许你在 agent run 的每一步之前，用用户定义函数修改完整的可用工具列表。该函数接受 agent [run context][pydantic_ai.tools.RunContext] 和一组 [`ToolDefinition`s][pydantic_ai.tools.ToolDefinition]，并返回该步骤要暴露的 tool definitions。

这是 toolset-specific 版本的 [`prepare_tools`](tools-advanced.md#prepare-tools) `Agent` 参数；后者会准备 agent 上跨 toolsets 注册的所有 tool definitions。二者遵循相同的返回值规则。

请注意，无法使用 `PreparedToolset` 添加或重命名工具。请改用 [`FunctionToolset.add_function()`](#function-toolset) 或 [`RenamedToolset`](#renaming-tools)。

为了方便串联不同修改，你也可以在任意 toolset 上调用 [`prepared()`][pydantic_ai.toolsets.AbstractToolset.prepared]，而不是直接构造 `PreparedToolset`。

```python {title="prepared_toolset.py" requires="function_toolset.py,combined_toolset.py,renamed_toolset.py"}
from dataclasses import replace

from pydantic_ai import Agent, RunContext, ToolDefinition
from pydantic_ai.models.test import TestModel

from renamed_toolset import renamed_toolset

descriptions = {
    'temperature_celsius': 'Get the temperature in degrees Celsius',
    'temperature_fahrenheit': 'Get the temperature in degrees Fahrenheit',
    'weather_conditions': 'Get the current weather conditions',
    'current_time': 'Get the current time',
}

async def add_descriptions(ctx: RunContext, tool_defs: list[ToolDefinition]) -> list[ToolDefinition] | None:
    return [
        replace(tool_def, description=description)
        if (description := descriptions.get(tool_def.name, None))
        else tool_def
        for tool_def
        in tool_defs
    ]

prepared_toolset = renamed_toolset.prepared(add_descriptions)

test_model = TestModel() # (1)!
agent = Agent(test_model, toolsets=[prepared_toolset])
result = agent.run_sync('What tools are available?')
print(test_model.last_model_request_parameters.function_tools)
"""
[
    ToolDefinition(
        name='temperature_celsius',
        parameters_json_schema={
            'additionalProperties': False,
            'properties': {'city': {'type': 'string'}},
            'required': ['city'],
            'type': 'object',
        },
        description='Get the temperature in degrees Celsius',
    ),
    ToolDefinition(
        name='temperature_fahrenheit',
        parameters_json_schema={
            'additionalProperties': False,
            'properties': {'city': {'type': 'string'}},
            'required': ['city'],
            'type': 'object',
        },
        description='Get the temperature in degrees Fahrenheit',
    ),
    ToolDefinition(
        name='weather_conditions',
        parameters_json_schema={
            'additionalProperties': False,
            'properties': {'city': {'type': 'string'}},
            'required': ['city'],
            'type': 'object',
        },
        description='Get the current weather conditions',
    ),
    ToolDefinition(
        name='current_time',
        parameters_json_schema={
            'additionalProperties': False,
            'properties': {},
            'type': 'object',
        },
        description='Get the current time',
    ),
]
"""
```

1. 这里使用 [`TestModel`][pydantic_ai.models.test.TestModel]，因为它能方便地查看每次 run 中哪些工具可用。

### 要求工具审批 {#requiring-tool-approval}

[`ApprovalRequiredToolset`][pydantic_ai.toolsets.ApprovalRequiredToolset] 会包装一个 toolset，并允许你基于用户定义函数，为某个 tool call 动态[要求审批](deferred-tools.md#human-in-the-loop-tool-approval)。该函数会收到 agent [run context][pydantic_ai.tools.RunContext]、工具的 [`ToolDefinition`][pydantic_ai.tools.ToolDefinition]，以及已验证的 tool call arguments。如果未提供函数，所有 tool calls 都会要求审批。

为了方便串联不同修改，你也可以在任意 toolset 上调用 [`approval_required()`][pydantic_ai.toolsets.AbstractToolset.approval_required]，而不是直接构造 `ApprovalRequiredToolset`。

关于如何处理调用了需审批工具的 agent runs，以及如何传入结果，请参阅 [Human-in-the-Loop Tool Approval](deferred-tools.md#human-in-the-loop-tool-approval) 文档。

```python {title="approval_required_toolset.py" requires="function_toolset.py,combined_toolset.py,renamed_toolset.py,prepared_toolset.py"}
from pydantic_ai import Agent, DeferredToolRequests, DeferredToolResults
from pydantic_ai.models.test import TestModel

from prepared_toolset import prepared_toolset

approval_required_toolset = prepared_toolset.approval_required(lambda ctx, tool_def, tool_args: tool_def.name.startswith('temperature'))

test_model = TestModel(call_tools=['temperature_celsius', 'temperature_fahrenheit']) # (1)!
agent = Agent(
    test_model,
    toolsets=[approval_required_toolset],
    output_type=[str, DeferredToolRequests],
)
result = agent.run_sync('Call the temperature tools')
messages = result.all_messages()
print(result.output)
"""
DeferredToolRequests(
    calls=[],
    approvals=[
        ToolCallPart(
            tool_name='temperature_celsius',
            args={'city': 'a'},
            tool_call_id='pyd_ai_tool_call_id__temperature_celsius',
        ),
        ToolCallPart(
            tool_name='temperature_fahrenheit',
            args={'city': 'a'},
            tool_call_id='pyd_ai_tool_call_id__temperature_fahrenheit',
        ),
    ],
    metadata={},
)
"""

result = agent.run_sync(
    message_history=messages,
    deferred_tool_results=DeferredToolResults(
        approvals={
            'pyd_ai_tool_call_id__temperature_celsius': True,
            'pyd_ai_tool_call_id__temperature_fahrenheit': False,
        }
    )
)
print(result.output)
#> {"temperature_celsius":21.0,"temperature_fahrenheit":"The tool call was denied."}
```

1. 这里使用 [`TestModel`][pydantic_ai.models.test.TestModel]，因为它可以方便地指定要调用哪些工具。

_（这个示例是完整的，可以"原样"运行）_

### Deferred Loading（延迟加载） {#deferred-loading}

[`DeferredLoadingToolset`][pydantic_ai.toolsets.DeferredLoadingToolset] 会包装一个 toolset，并把它的工具标记为 deferred loading，使这些工具在通过 [tool search](tools-advanced.md#tool-search) 被发现前对模型隐藏。这适用于大型 toolsets（例如有许多 endpoints 的 MCP servers），因为把所有 tool definitions 都加载进模型 context 会很浪费。

[`FunctionToolset`][pydantic_ai.toolsets.FunctionToolset] 的 constructor 也接受 `defer_loading=True`，用于将所有工具标记为 deferred loading。对于其他 toolsets，请调用 [`.defer_loading()`][pydantic_ai.toolsets.AbstractToolset.defer_loading]；传入 tool names list 可只隐藏特定工具，传入 `None`（默认值）可隐藏全部工具。

```python {title="deferred_loading_toolset.py" lint="skip" test="skip"}
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerHTTP

mcp = MCPServerHTTP('http://localhost:8000/mcp')
agent = Agent('openai:gpt-5.2', toolsets=[mcp.defer_loading()])
```

### 包含 Return Schemas {#including-return-schemas}

[`IncludeReturnSchemasToolset`][pydantic_ai.toolsets.IncludeReturnSchemasToolset] 会包装一个 toolset，并在其所有工具上设置 `include_return_schema=True`，让模型收到 return type information。对于原生支持 return schemas 的 models（例如 Google Gemini），schema 会作为结构化 API 字段传入。对于其他 models，它会作为 JSON text 注入 tool description。

为了方便串联不同修改，你也可以在任意 toolset 上调用 [`.include_return_schemas()`][pydantic_ai.toolsets.AbstractToolset.include_return_schemas]，而不是直接构造 `IncludeReturnSchemasToolset`。

```python {title="include_return_schemas_toolset.py"}
from pydantic_ai import Agent, FunctionToolset
from pydantic_ai.models.test import TestModel


def get_temperature(city: str) -> float:
    """Get the temperature for a city."""
    return 21.0


toolset = FunctionToolset(tools=[get_temperature])

test_model = TestModel()
agent = Agent(test_model, toolsets=[toolset.include_return_schemas()])
result = agent.run_sync('What is the temperature?')
params = test_model.last_model_request_parameters
assert params is not None
assert params.function_tools[0].include_return_schema is True
```

_（这个示例是完整的，可以"原样"运行）_

这是 toolset-level 版本的 [`IncludeToolReturnSchemas`][pydantic_ai.capabilities.IncludeToolReturnSchemas] capability；后者可应用于所有 toolsets 或选定子集。

### 设置工具 Metadata {#setting-tool-metadata}

[`SetMetadataToolset`][pydantic_ai.toolsets.SetMetadataToolset] 会包装一个 toolset，并把 metadata key-value pairs 合并到它的所有工具上。它适合给工具打上可供其他 capabilities 或自定义逻辑检查的配置标签。

为了方便串联不同修改，你也可以在任意 toolset 上调用 [`.with_metadata()`][pydantic_ai.toolsets.AbstractToolset.with_metadata]，而不是直接构造 `SetMetadataToolset`。

```python {title="set_metadata_toolset.py"}
from pydantic_ai import Agent, FunctionToolset
from pydantic_ai.models.test import TestModel


def search(query: str) -> str:
    """Search for information."""
    return f'Results for: {query}'


toolset = FunctionToolset(tools=[search])

test_model = TestModel()
agent = Agent(test_model, toolsets=[toolset.with_metadata(sensitive=True)])
result = agent.run_sync('Search for something')
params = test_model.last_model_request_parameters
assert params is not None
assert params.function_tools[0].metadata is not None
assert params.function_tools[0].metadata['sensitive'] is True
```

_（这个示例是完整的，可以"原样"运行）_

这是 toolset-level 版本的 [`SetToolMetadata`][pydantic_ai.capabilities.SetToolMetadata] capability；后者可应用于所有 toolsets 或选定子集。

### 改变工具执行 {#changing-tool-execution}

[`WrapperToolset`][pydantic_ai.toolsets.WrapperToolset] 会包装另一个 toolset，并把所有职责委托给它。

它默认是 no-op，但你可以 subclass `WrapperToolset`，并通过 override [`call_tool()`][pydantic_ai.toolsets.AbstractToolset.call_tool] method 来改变被包装 toolset 的工具执行行为。

```python {title="logging_toolset.py" requires="function_toolset.py,combined_toolset.py,renamed_toolset.py,prepared_toolset.py"}
import asyncio

from typing_extensions import Any

from pydantic_ai import Agent, RunContext, ToolsetTool, WrapperToolset
from pydantic_ai.models.test import TestModel

from prepared_toolset import prepared_toolset

LOG = []

class LoggingToolset(WrapperToolset):
    async def call_tool(self, name: str, tool_args: dict[str, Any], ctx: RunContext, tool: ToolsetTool) -> Any:
        LOG.append(f'Calling tool {name!r} with args: {tool_args!r}')
        try:
            await asyncio.sleep(0.1 * len(LOG)) # (1)!

            result = await super().call_tool(name, tool_args, ctx, tool)
            LOG.append(f'Finished calling tool {name!r} with result: {result!r}')
        except Exception as e:
            LOG.append(f'Error calling tool {name!r}: {e}')
            raise e
        else:
            return result


logging_toolset = LoggingToolset(prepared_toolset)

agent = Agent(TestModel(), toolsets=[logging_toolset]) # (2)!
result = agent.run_sync('Call all the tools')
print(LOG)
"""
[
    "Calling tool 'temperature_celsius' with args: {'city': 'a'}",
    "Calling tool 'temperature_fahrenheit' with args: {'city': 'a'}",
    "Calling tool 'weather_conditions' with args: {'city': 'a'}",
    "Calling tool 'current_time' with args: {}",
    "Finished calling tool 'temperature_celsius' with result: 21.0",
    "Finished calling tool 'temperature_fahrenheit' with result: 69.8",
    'Finished calling tool \'weather_conditions\' with result: "It\'s raining"',
    "Finished calling tool 'current_time' with result: datetime.datetime(...)",
]
"""
```

1. 所有 docs examples 都会在 CI 中测试，并验证其输出，因此每次运行这段代码时，`LOG` 都必须保持相同顺序。由于工具可能以任意顺序完成，我们会根据当前是第几个 tool call 逐渐增加 sleep 时间，以确保它们按调用顺序完成并记录日志。
2. 这里使用 [`TestModel`][pydantic_ai.models.test.TestModel]，因为它会自动调用每个工具。

_（这个示例是完整的，可以"原样"运行）_

## External Toolset（外部工具集） {#external-toolset}

如果 agent 需要调用由上游服务或前端提供并执行的 [external tools](deferred-tools.md#external-tool-execution)，你可以用一组 [`ToolDefinition`s][pydantic_ai.tools.ToolDefinition] 构建 [`ExternalToolset`][pydantic_ai.toolsets.ExternalToolset]；这些定义包含工具名称、arguments JSON schemas 和 descriptions。

当模型调用 external tool 时，该调用会被视为 ["deferred"](deferred-tools.md#deferred-tools)，agent run 会以 [`DeferredToolRequests`][pydantic_ai.output.DeferredToolRequests] output object 结束。该对象带有 `calls` list，其中保存 [`ToolCallPart`s][pydantic_ai.messages.ToolCallPart]，包含工具名称、已验证 arguments 和唯一 tool call ID。你应把这些内容传给将生成结果的上游服务或前端。

从上游服务或前端收到 tool call results 后，你可以构建一个 [`DeferredToolResults`][pydantic_ai.tools.DeferredToolResults] object，其 `calls` dictionary 将每个 tool call ID 映射到要返回给模型的任意值、[`ToolReturn`](tools-advanced.md#advanced-tool-returns) object，或在 tool call 失败且模型应[重试](tools-advanced.md#tool-retries)时映射到 [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] exception。随后可以把这个 `DeferredToolResults` object 作为 `deferred_tool_results` 提供给某个 agent run method，并同时提供原始 run 的 [message history](message-history.md)。

请注意，你需要把 `DeferredToolRequests` 添加到 `Agent` 或 `agent.run()` 的 [`output_type`](output.md#structured-output)，这样 agent run output 的可能类型才能被正确推断。更多信息请参阅 [Deferred Tools](deferred-tools.md#deferred-tools) 文档。

为了演示，先定义一个_不带_ deferred tools 的简单 agent：

```python {title="deferred_toolset_agent.py"}
from pydantic import BaseModel

from pydantic_ai import Agent, FunctionToolset

toolset = FunctionToolset()


@toolset.tool_plain
def get_default_language():
    return 'en-US'


@toolset.tool_plain
def get_user_name():
    return 'David'


class PersonalizedGreeting(BaseModel):
    greeting: str
    language_code: str


agent = Agent('openai:gpt-5.2', toolsets=[toolset], output_type=PersonalizedGreeting)

result = agent.run_sync('Greet the user in a personalized way')
print(repr(result.output))
#> PersonalizedGreeting(greeting='Hello, David!', language_code='en-US')
```

接下来定义一个函数，表示假想的 "run agent" API endpoint。前端可以调用它，并传入要发送给模型的 messages list、frontend tool definitions list，以及可选 deferred tool results。这就是 `ExternalToolset`、`DeferredToolRequests` 和 `DeferredToolResults` 派上用场的地方：

```python {title="deferred_toolset_api.py" requires="deferred_toolset_agent.py"}
from pydantic_ai import (
    DeferredToolRequests,
    DeferredToolResults,
    ExternalToolset,
    ModelMessage,
    ToolDefinition,
)

from deferred_toolset_agent import PersonalizedGreeting, agent


def run_agent(
    messages: list[ModelMessage] = [],
    frontend_tools: list[ToolDefinition] = {},
    deferred_tool_results: DeferredToolResults | None = None,
) -> tuple[PersonalizedGreeting | DeferredToolRequests, list[ModelMessage]]:
    deferred_toolset = ExternalToolset(frontend_tools)
    result = agent.run_sync(
        toolsets=[deferred_toolset], # (1)!
        output_type=[agent.output_type, DeferredToolRequests], # (2)!
        message_history=messages, # (3)!
        deferred_tool_results=deferred_tool_results,
    )
    return result.output, result.new_messages()
```

1. 如 [Deferred Tools](deferred-tools.md#deferred-tools) 文档所述，这些 `toolsets` 会补充 `Agent` constructor 中提供的 toolsets。
2. 如 [Deferred Tools](deferred-tools.md#deferred-tools) 文档所述，这里的 `output_type` 会覆盖 `Agent` constructor 中提供的值，因此必须确保没有丢失原本的类型。
3. 这里不包含 `user_prompt` keyword argument，因为我们期望前端通过 `messages` 提供它。

现在，假设下面的代码在前端实现，而 `run_agent` 代表一次调用后端运行 agent 的 API 请求。这里会真正执行 deferred tool calls，并在包含新结果的情况下启动新的 run：

```python {title="deferred_tools.py" requires="deferred_toolset_agent.py,deferred_toolset_api.py"}
from pydantic_ai import (
    DeferredToolRequests,
    DeferredToolResults,
    ModelMessage,
    ModelRequest,
    ModelRetry,
    ToolDefinition,
    UserPromptPart,
)

from deferred_toolset_api import run_agent

frontend_tool_definitions = [
    ToolDefinition(
        name='get_preferred_language',
        parameters_json_schema={'type': 'object', 'properties': {'default_language': {'type': 'string'}}},
        description="Get the user's preferred language from their browser",
    )
]

def get_preferred_language(default_language: str) -> str:
    return 'es-MX' # (1)!

frontend_tool_functions = {'get_preferred_language': get_preferred_language}

messages: list[ModelMessage] = [
    ModelRequest(
        parts=[
            UserPromptPart(content='Greet the user in a personalized way')
        ]
    )
]

deferred_tool_results: DeferredToolResults | None = None

final_output = None
while True:
    output, new_messages = run_agent(messages, frontend_tool_definitions, deferred_tool_results)
    messages += new_messages

    if not isinstance(output, DeferredToolRequests):
        final_output = output
        break

    print(output.calls)
    """
    [
        ToolCallPart(
            tool_name='get_preferred_language',
            args={'default_language': 'en-US'},
            tool_call_id='pyd_ai_tool_call_id',
        )
    ]
    """
    deferred_tool_results = DeferredToolResults()
    for tool_call in output.calls:
        if function := frontend_tool_functions.get(tool_call.tool_name):
            result = function(**tool_call.args_as_dict())
        else:
            result = ModelRetry(f'Unknown tool {tool_call.tool_name!r}')
        deferred_tool_results.calls[tool_call.tool_call_id] = result

print(repr(final_output))
"""
PersonalizedGreeting(greeting='Hola, David! Espero que tengas un gran día!', language_code='es-MX')
"""
```

1. 假设这里返回前端的 [`navigator.language`](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/language)。

_（这个示例是完整的，可以"原样"运行）_

## 动态构建 Toolset {#dynamically-building-a-toolset}

Toolsets 可以在每个 agent run 或 run step 之前通过函数动态构建。该函数接受 agent [run context][pydantic_ai.tools.RunContext]，并返回 toolset 或 `None`。当某个 toolset（例如 MCP server）依赖特定于 agent run 的信息（例如其 [dependencies](./dependencies.md)）时，这很有用。

要注册 dynamic toolset，可以把接受 [`RunContext`][pydantic_ai.tools.RunContext] 的函数传给 `Agent` constructor 的 `toolsets` argument，或用 [`@agent.toolset`][pydantic_ai.agent.Agent.toolset] decorator 包装一个符合要求的函数。

默认情况下，该函数会在每个 agent run step 前重新调用。如果使用 decorator，可以选择提供 `per_run_step=False` argument，表示整个 run 只需要构建一次 toolset。

```python {title="dynamic_toolset.py", requires="function_toolset.py"}
from dataclasses import dataclass
from typing import Literal

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.test import TestModel

from function_toolset import datetime_toolset, weather_toolset


@dataclass
class ToggleableDeps:
    active: Literal['weather', 'datetime']

    def toggle(self):
        if self.active == 'weather':
            self.active = 'datetime'
        else:
            self.active = 'weather'

test_model = TestModel()  # (1)!
agent = Agent(
    test_model,
    deps_type=ToggleableDeps  # (2)!
)

@agent.toolset
def toggleable_toolset(ctx: RunContext[ToggleableDeps]):
    if ctx.deps.active == 'weather':
        return weather_toolset
    else:
        return datetime_toolset

@agent.tool
def toggle(ctx: RunContext[ToggleableDeps]):
    ctx.deps.toggle()

deps = ToggleableDeps('weather')

result = agent.run_sync('Toggle the toolset', deps=deps)
print([t.name for t in test_model.last_model_request_parameters.function_tools])  # (3)!
#> ['toggle', 'now']

result = agent.run_sync('Toggle the toolset', deps=deps)
print([t.name for t in test_model.last_model_request_parameters.function_tools])
#> ['toggle', 'temperature_celsius', 'temperature_fahrenheit', 'conditions']
```

1. 这里使用 [`TestModel`][pydantic_ai.models.test.TestModel]，因为它能方便地查看每次 run 中哪些工具可用。
2. 这里使用 agent 的 dependencies，让 `toggle` 工具能通过 `RunContext` argument 访问 `active`。
3. 这里展示的是 `toggle` 工具执行_之后_的可用工具，因为 "last model request" 是把 `toggle` tool result 返回给模型的那一次请求。

_（这个示例是完整的，可以"原样"运行）_

## 构建自定义 Toolset {#building-a-custom-toolset}

如果要定义完全自定义的 toolset，并自行实现列出可用工具和处理工具调用的逻辑，可以 subclass [`AbstractToolset`][pydantic_ai.toolsets.AbstractToolset]，并实现 [`get_tools()`][pydantic_ai.toolsets.AbstractToolset.get_tools] 和 [`call_tool()`][pydantic_ai.toolsets.AbstractToolset.call_tool] methods。

你还可以 override [`get_instructions()`][pydantic_ai.toolsets.AbstractToolset.get_instructions] method，用于提供如何使用该 toolset 工具的说明。这段说明会注入 agent instructions，帮助模型理解如何有效使用你的 toolset tools。

!!! tip
    如果你的 toolset 还需要提供 model settings 或 hooks，请考虑改为构建 [custom capability](capabilities.md#building-custom-capabilities)。

Toolset lifecycle 提供了用于在不同 scopes 管理 state 的 hooks：

- [`for_run()`][pydantic_ai.toolsets.AbstractToolset.for_run]：在每次 agent run 前调用一次。返回一个新实例可以隔离 per-run state（例如重置 counters、创建新 session）。Framework 会 enter 和 exit 返回的实例。
- [`for_run_step()`][pydantic_ai.toolsets.AbstractToolset.for_run_step]：在每个 run step 开始时调用。返回修改后的实例，用于 per-step state transitions。如果要管理内部 toolset transitions（例如在两个 toolsets 之间切换），你需要负责内部 lifecycle（退出旧的、进入新的）。
- [`__aenter__()`][pydantic_ai.toolsets.AbstractToolset.__aenter__] 和 [`__aexit__()`][pydantic_ai.toolsets.AbstractToolset.__aexit__]：设置和清理应在 agent run 持续期间存在的资源（例如 network connections）。

### Per-run 和 per-step lifecycle {#per-run-and-per-step-lifecycle}

Toolsets 支持用于 per-run isolation 和 per-step state management 的 lifecycle hooks：

- [`for_run(ctx)`][pydantic_ai.toolsets.AbstractToolset.for_run]：每个 agent run 调用一次，在 `__aenter__` 之前调用。返回一个新实例可隔离不同 runs 之间的 state。默认返回 `self`。
- [`for_run_step(ctx)`][pydantic_ai.toolsets.AbstractToolset.for_run_step]：在每个 run step 开始时调用。用于原地管理内部 transitions（例如刷新工具可用性）。默认返回 `self`。

## 第三方 Toolsets {#third-party-toolsets}

第三方 toolsets 也可以包装为 [capabilities](capabilities.md)，以便把 tools 与 hooks、instructions 和 model settings 打包在一起。完整生态请参阅 [Extensibility](extensibility.md)。

### MCP Servers（MCP 服务器）

Pydantic AI 提供两个 toolsets，允许 agent 连接并调用本地和远程 MCP Servers 上的工具：

1. `MCPServer`：[MCP SDK-based Client](./mcp/client.md)，直接利用 MCP SDK 提供更直接的控制
2. `FastMCPToolset`：[FastMCP-based Client](./mcp/fastmcp-client.md)，提供 Tool Transformation、更简单的 OAuth 配置等额外能力

### Agent Skills（Agent 技能）

实现 [Agent Skills](https://agentskills.io) 支持的 toolsets，可让 agents 高效发现并执行特定任务：

* [`pydantic-ai-skills`](https://github.com/DougTrajano/pydantic-ai-skills) - `SkillsToolset` 通过 progressive disclosure 实现 Agent Skills 支持（按需加载 skills 以减少 tokens）。支持 filesystem 和 programmatic skills；兼容 [agentskills.io](https://agentskills.io)。

### 任务管理 {#task-management}

用于 task planning 和 progress tracking 的 toolsets，可帮助 agents 组织复杂工作，并提供 agent progress 可见性：

* [`pydantic-ai-todo`](https://github.com/vstorm-co/pydantic-ai-todo) - 带有 `read_todos` 和 `write_todos` tools 的 `TodoToolset`。包含在第三方 [`pydantic-deep`](https://github.com/vstorm-co/pydantic-deepagents) [deep agent](multi-agent-applications.md#deep-agents) framework 中。

### 文件操作 {#file-operations}

用于 file operations 的 toolsets 可帮助 agents 读取、写入和编辑文件：

* [`pydantic-ai-filesystem-sandbox`](https://github.com/zby/pydantic-ai-filesystem-sandbox) - 带 sandbox 和 LLM-friendly errors 的 `FileSystemToolset`
* [`pydantic-deep`](https://github.com/vstorm-co/pydantic-deepagents) - deep agent framework，包含支持多个 backends（in-memory、real filesystem、Docker sandbox）的 `FilesystemToolset`

### 代码执行 {#code-execution}

用于 sandboxed code execution 的 toolsets 可帮助 agents 在 sandboxed environment 中运行代码：

* [`mcp-run-python`](https://github.com/pydantic/mcp-run-python) - Pydantic 团队提供的 MCP server，可在 sandboxed environment 中运行 Python 代码。可以用作 `MCPServerStdio('uv', args=['run', 'mcp-run-python', 'stdio'])`。

### LangChain Tools（LangChain 工具） {#langchain-tools}

如果想在 Pydantic AI 中使用 LangChain [community tool library](https://python.langchain.com/docs/integrations/tools/) 中的 tools 或 [toolkit](https://python.langchain.com/docs/concepts/tools/#toolkits)，可以使用 [`LangChainToolset`][pydantic_ai.ext.langchain.LangChainToolset]，它接受 LangChain tools list。请注意，这种情况下 Pydantic AI 不会验证 arguments；需要由模型提供与 LangChain tool 指定 schema 匹配的 arguments，并由 LangChain tool 在 arguments 无效时引发错误。

你需要安装 `langchain-community` package，以及相关 tools 所需的其他 packages。

```python {test="skip"}
from langchain_community.agent_toolkits import SlackToolkit

from pydantic_ai import Agent
from pydantic_ai.ext.langchain import LangChainToolset

toolkit = SlackToolkit()
toolset = LangChainToolset(toolkit.get_tools())

agent = Agent('openai:gpt-5.2', toolsets=[toolset])
# ...
```

### ACI.dev Tools（ACI.dev 工具） {#aci-tools}

!!! warning "1.x 中已弃用，2.0 中移除"
    `pydantic_ai.ext.aci`（`tool_from_aci` 和 `ACIToolset`）已弃用，并将在 2.0 中移除（见 [#5467](https://github.com/pydantic/pydantic-ai/pull/5467)）。请针对 `aci.ACI().functions.get_definition(...)` 使用 [`Tool.from_schema`][pydantic_ai.tools.Tool.from_schema] 自行包装 ACI.dev tools，或直接调用上游 `aci-sdk` 集成。

如果想在 Pydantic AI 中使用 [ACI.dev tool library](https://www.aci.dev/tools) 中的 tools，可以使用 [`ACIToolset`][pydantic_ai.ext.aci.ACIToolset] [toolset](toolsets.md)，它接受 ACI tool names list 和 `linked_account_owner_id`。请注意，这种情况下 Pydantic AI 不会验证 arguments；需要由模型提供与 ACI tool 指定 schema 匹配的 arguments，并由 ACI tool 在 arguments 无效时引发错误。

你需要安装 `aci-sdk` package，在 `ACI_API_KEY` environment variable 中设置 ACI API key，并把 ACI "linked account owner ID" 传给该函数。

```python {test="skip"}
import os

from pydantic_ai import Agent
from pydantic_ai.ext.aci import ACIToolset

toolset = ACIToolset(
    [
        'OPEN_WEATHER_MAP__CURRENT_WEATHER',
        'OPEN_WEATHER_MAP__FORECAST',
    ],
    linked_account_owner_id=os.getenv('LINKED_ACCOUNT_OWNER_ID'),
)

agent = Agent('openai:gpt-5.2', toolsets=[toolset])
```

### pydantic-ai-ejentum 集成 {#ejentum-tools}

[`pydantic-ai-ejentum`](https://pypi.org/project/pydantic-ai-ejentum/) 会把 [Ejentum Reasoning Harness](https://ejentum.com) 包装为 `FunctionToolset` subclass。`EjentumToolset` 注册四个 agent-callable tools（`harness_reasoning`、`harness_code`、`harness_anti_deception`、`harness_memory`）。Agent 会在生成前调用其中一个；每次调用都会返回结构化 cognitive scaffold（命名 failure pattern、可执行 procedure、suppression vectors、falsification test），模型会在内部读取它来塑造下一次响应。

你需要安装 `pydantic-ai-ejentum` package，并在 `EJENTUM_API_KEY` environment variable 中设置 Ejentum API key（免费和付费 tiers 见 <https://ejentum.com/pricing>），或把 `api_key=` 传给 constructor。

```python {test="skip" lint="skip"}
from pydantic_ai import Agent
from pydantic_ai_ejentum import EjentumToolset

toolset = EjentumToolset()

agent = Agent('openai:gpt-5.2', toolsets=[toolset])
```

该 toolset 会发出 PydanticAI `instructions`，提示 agent 在生成前调用匹配的 `harness_*` tool。传入 `add_instructions=False` 可以抑制这些 instructions，并改为从你自己的 system prompt 提供 routing guidance。
