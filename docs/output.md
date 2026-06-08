"Output" 指的是 [运行 agent](agent.md#running-agents) 后返回的最终值。它可以是纯文本、[结构化数据](#structured-output)、[图像](#image-output)，也可以是由模型提供参数后调用某个 [function](#output-functions) 得到的结果。

Output 会包装在 [`AgentRunResult`][pydantic_ai.agent.AgentRunResult] 或 [`StreamedRunResult`][pydantic_ai.result.StreamedRunResult] 中，因此你还可以访问其他数据，例如该 run 的 [usage][pydantic_ai.usage.RunUsage] 和 [message history](message-history.md#accessing-messages-from-results)。

`AgentRunResult` 和 `StreamedRunResult` 都会以其包装的数据作为泛型参数，因此 agent 返回数据的类型信息会被保留下来。

当模型返回某个 output type 时，run 就会结束；如果没有指定 output type，或 `str` 是允许的选项之一，则收到纯文本响应时 run 会结束。如果超出 usage limits，run 也可能被取消，参见 [Usage Limits](agent.md#usage-limits)。

下面的示例使用 Pydantic model 作为 `output_type`，强制模型返回符合我们规范的数据：

```python {title="olympics.py" line_length="90"}
from pydantic import BaseModel

from pydantic_ai import Agent


class CityLocation(BaseModel):
    city: str
    country: str


agent = Agent('google:gemini-3-flash-preview', output_type=CityLocation)
result = agent.run_sync('Where were the olympics held in 2012?')
print(result.output)
#> city='London' country='United Kingdom'
print(result.usage)
#> RunUsage(input_tokens=57, output_tokens=8, requests=1)
```

_（这个示例是完整的，可以"原样"运行）_

## 结构化输出数据 {#structured-output}

[`Agent`][pydantic_ai.Agent] class constructor 接受 `output_type` argument，它可以接收一个或多个类型或 [output functions](#output-functions)。它支持简单标量类型、list 和 dict 类型（包括 `TypedDict`s 与 [`StructuredDict`s](#structured-dict)）、dataclasses、Pydantic models，以及 type unions；一般来说，Pydantic model 中支持的 type hints 都可使用。你也可以传入包含多个选项的 list。

默认情况下，Pydantic AI 会利用模型的 tool calling 能力，让模型返回结构化数据。当指定多个 output types（通过 union 或 list）时，每个成员都会作为单独的 output tool 注册给模型，以降低 schema 复杂度，并最大化模型正确响应的概率。这种方式已证明能在大量模型上良好工作。如果你想修改 output tools 的名称、使用模型原生 structured output 功能，或把 output schema 通过 [instructions](agent.md#instructions) 传给模型，可以使用 [output mode](#output-modes) marker class。

当没有指定 output type，或 `str` 位于 output types 中时，模型返回的任何纯文本响应都会作为 output data。
如果 `str` 不在 output types 中，模型会被强制返回结构化数据或调用 output function。

如果 output type schema 不是 `"object"` 类型（例如它是 `int` 或 `list[int]`），该 output type 会被包装进一个单元素 object，因此所有注册给模型的 tools schema 都是 object schemas。

Structured outputs（和 tools 一样）使用 Pydantic 构建 tool 使用的 JSON schema，并验证模型返回的数据。

!!! note "类型检查注意事项"
    Agent class 以其 output type 作为泛型参数，该类型会一直传递到 `AgentRunResult.output` 和 `StreamedRunResult.output`，这样当你的代码没有正确处理这些 outputs 可能包含的所有值时，IDE 或静态类型检查器就能给出警告。

    pyright 和 mypy 这类静态类型检查器会尽力根据你指定的 `output_type` 推断 agent 的 output type，但当你提供 functions，或在 union/list 中提供多个类型时，它们不一定总能正确推断，即使 Pydantic AI 的运行时行为是正确的。出现这种情况时，即使你确信传入的是有效 `output_type`，类型检查器也可能报错；你需要在 `Agent` constructor 上显式指定泛型参数来帮助类型检查器。下面第二个示例和后面的 output functions 示例展示了这种做法。

    具体来说，以下三种有效使用 `output_type` 的场景需要这样做：

    1. 使用类型 union 时，例如 `output_type=Foo | Bar`。在 [PEP-747](https://peps.python.org/pep-0747/) "Annotating Type Forms" 于 Python 3.15 落地之前，类型检查器不会把它们视为 `output_type` 的有效值。除了在 `Agent` constructor 上指定泛型参数外，你还需要在把 union 传给 `output_type` 的那一行添加 `# type: ignore`。也可以改用 list：`output_type=[Foo, Bar]`。
    2. 使用 mypy 时：当使用 list 作为与 union 功能等价的替代方案，或因为你传入了 [output functions](#output-functions) 时。Pyright 能正确处理这种情况；我们已经向 mypy 提交了 [issue](https://github.com/python/mypy/issues/19142)，希望修复它。
    3. 使用 mypy 时：当使用 async output function 时。Pyright 能正确处理这种情况；我们已经向 mypy 提交了 [issue](https://github.com/python/mypy/issues/19143)，希望修复它。

下面是返回文本或结构化数据的示例：

```python {title="box_or_error.py"}

from pydantic import BaseModel

from pydantic_ai import Agent


class Box(BaseModel):
    width: int
    height: int
    depth: int
    units: str


agent = Agent(
    'openai:gpt-5-mini',
    output_type=[Box, str], # (1)!
    instructions=(
        "Extract me the dimensions of a box, "
        "if you can't extract all data, ask the user to try again."
    ),
)

result = agent.run_sync('The box is 10x20x30')
print(result.output)
#> Please provide the units for the dimensions (e.g., cm, in, m).

result = agent.run_sync('The box is 10x20x30 cm')
print(result.output)
#> width=10 height=20 depth=30 units='cm'
```

1. 这里也可以使用 union：`output_type=Box | str`。不过如上文"类型检查注意事项"一节所述，要让它正确通过类型检查，需要在 `Agent` constructor 上显式指定泛型参数，并在这一行添加 `# type: ignore`。

_（这个示例是完整的，可以"原样"运行）_

下面是使用 union return type 的示例；它会注册多个 output tools，并把非 object schemas 包装到 object 中：

```python {title="colors_or_sizes.py"}
from pydantic_ai import Agent

agent = Agent[None, list[str] | list[int]](
    'openai:gpt-5-mini',
    output_type=list[str] | list[int],  # type: ignore # (1)!
    instructions='Extract either colors or sizes from the shapes provided.',
)

result = agent.run_sync('red square, blue circle, green triangle')
print(result.output)
#> ['red', 'blue', 'green']

result = agent.run_sync('square size 10, circle size 20, triangle size 30')
print(result.output)
#> [10, 20, 30]
```

1. 如上文"类型检查注意事项"一节所述，使用 union 而不是 list 时，需要在 `Agent` constructor 上显式指定泛型参数，并在这一行添加 `# type: ignore`，才能正确通过类型检查。

_（这个示例是完整的，可以"原样"运行）_

### Output functions（输出函数） {#output-functions}

除了纯文本或结构化数据之外，你可能希望 agent run 的 output 是某个函数的结果，而该函数由模型提供参数来调用。例如，这可用于进一步处理或验证通过参数提供的数据（并可以要求模型重试），或把任务 hand off 给另一个 agent。

Output functions 类似于 [function tools](tools.md)，但模型会被强制调用其中一个函数；该调用会结束 agent run，并且结果不会再传回模型。

与 tool functions 一样，模型提供的 output function arguments 会使用 Pydantic 验证（可带可选 [validation context](#validation-context)），也可以选择把 [`RunContext`][pydantic_ai.tools.RunContext] 作为第一个 argument，并且可以 raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry]，要求模型用修改后的 arguments（或不同的 output type）重试。

要指定 output functions，可以把 agent 的 `output_type` 设置为单个 function（或绑定的 instance method），也可以设置为 functions list。这个 list 也可以包含其他 output types，例如简单标量或完整的 Pydantic models。
通常不应同时把 output function 注册为 tool（使用 `@agent.tool` decorator 或 `tools` argument），因为这可能让模型混淆应该调用哪个。

下面的示例展示了这些功能如何协同工作：

```python {title="output_functions.py"}
import re

from pydantic import BaseModel

from pydantic_ai import Agent, ModelRetry, RunContext, UnexpectedModelBehavior


class Row(BaseModel):
    name: str
    country: str


tables = {
    'capital_cities': [
        Row(name='Amsterdam', country='Netherlands'),
        Row(name='Mexico City', country='Mexico'),
    ]
}


class SQLFailure(BaseModel):
    """An unrecoverable failure. Only use this when you can't change the query to make it work."""

    explanation: str


def run_sql_query(query: str) -> list[Row]:
    """Run a SQL query on the database."""

    select_table = re.match(r'SELECT (.+) FROM (\w+)', query)
    if select_table:
        column_names = select_table.group(1)
        if column_names != '*':
            raise ModelRetry("Only 'SELECT *' is supported, you'll have to do column filtering manually.")

        table_name = select_table.group(2)
        if table_name not in tables:
            raise ModelRetry(
                f"Unknown table '{table_name}' in query '{query}'. Available tables: {', '.join(tables.keys())}."
            )

        return tables[table_name]

    raise ModelRetry(f"Unsupported query: '{query}'.")


sql_agent = Agent[None, list[Row] | SQLFailure](
    'openai:gpt-5.2',
    output_type=[run_sql_query, SQLFailure],
    instructions='You are a SQL agent that can run SQL queries on a database.',
)


async def hand_off_to_sql_agent(ctx: RunContext, query: str) -> list[Row]:
    """I take natural language queries, turn them into SQL, and run them on a database."""

    # Drop the final message with the output tool call, as it shouldn't be passed on to the SQL agent
    messages = ctx.messages[:-1]
    try:
        result = await sql_agent.run(query, message_history=messages)
        output = result.output
        if isinstance(output, SQLFailure):
            raise ModelRetry(f'SQL agent failed: {output.explanation}')
        return output
    except UnexpectedModelBehavior as e:
        # Bubble up potentially retryable errors to the router agent
        if (cause := e.__cause__) and isinstance(cause, ModelRetry):
            raise ModelRetry(f'SQL agent failed: {cause.message}') from e
        else:
            raise


class RouterFailure(BaseModel):
    """Use me when no appropriate agent is found or the used agent failed."""

    explanation: str


router_agent = Agent[None, list[Row] | RouterFailure](
    'openai:gpt-5.2',
    output_type=[hand_off_to_sql_agent, RouterFailure],
    instructions='You are a router to other agents. Never try to solve a problem yourself, just pass it on.',
)

result = router_agent.run_sync('Select the names and countries of all capitals')
print(result.output)
"""
[
    Row(name='Amsterdam', country='Netherlands'),
    Row(name='Mexico City', country='Mexico'),
]
"""

result = router_agent.run_sync('Select all pets')
print(repr(result.output))
"""
RouterFailure(explanation="The requested table 'pets' does not exist in the database. The only available table is 'capital_cities', which does not contain data about pets.")
"""

result = router_agent.run_sync('How do I fly from Amsterdam to Mexico City?')
print(repr(result.output))
"""
RouterFailure(explanation='I am not equipped to provide travel information, such as flights from Amsterdam to Mexico City.')
"""
```

#### 文本输出 {#text-output}

如果提供一个接收 string 的 output function，Pydantic AI 默认会像处理其他 output function 一样创建 output tool。如果你希望模型通过纯文本 output 提供该 string，可以用 [`TextOutput`][pydantic_ai.output.TextOutput] marker class 包装这个 function。

如果需要，可以在传给 `output_type` 的 list 中，把这个 marker class 与一个或多个 [`ToolOutput`](#tool-output) marker classes（或未标记的类型或 functions）一起使用。

与其他 output functions 一样，text output functions 可以选择把 [`RunContext`][pydantic_ai.tools.RunContext] 作为第一个 argument，并可以 raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry]，要求模型使用修改后的 arguments（或不同的 output type）重试。

```python {title="text_output_function.py"}
from pydantic_ai import Agent, TextOutput


def split_into_words(text: str) -> list[str]:
    return text.split()


agent = Agent(
    'openai:gpt-5.2',
    output_type=TextOutput(split_into_words),
)
result = agent.run_sync('Who was Albert Einstein?')
print(result.output)
#> ['Albert', 'Einstein', 'was', 'a', 'German-born', 'theoretical', 'physicist.']
```

_（这个示例是完整的，可以"原样"运行）_

#### 在 output functions 中处理部分输出 {#handling-partial-output-in-output-functions}

使用 `run_stream()` 或 `run_stream_sync()` 流式运行时，output functions 会被调用**多次**：模型每产生一次 partial output 会调用一次，最终完整 output 也会调用一次。

当你的 output function 有**副作用**（例如发送通知、写日志、更新数据库），且这些副作用只应在最终 output 上执行时，应检查 [`RunContext.partial_output`][pydantic_ai.tools.RunContext.partial_output] flag。

流式运行时，每个 partial output 的 `partial_output` 都是 `True`，最终完整 output 的 `partial_output` 是 `False`。
对所有[其他 run methods](agent.md#running-agents)，`partial_output` 始终为 `False`，因为 function 只会在完整 output 上调用一次。

```python {title="output_function_with_side_effects.py"}
from pydantic import BaseModel

from pydantic_ai import Agent, RunContext


class DatabaseRecord(BaseModel):
    name: str
    value: int | None = None  # Make optional to allow partial output


def save_to_database(ctx: RunContext, record: DatabaseRecord) -> DatabaseRecord:
    """Output function with side effect - only save final output to database."""
    if ctx.partial_output:
        # Skip side effects for partial outputs
        return record

    # Only execute side effect for the final output
    print(f'Saving to database: {record.name} = {record.value}')
    #> Saving to database: test = 42
    return record


agent = Agent('openai:gpt-5.2', output_type=save_to_database)


async def main():
    async with agent.run_stream('Create a record with name "test" and value 42') as result:
        async for output in result.stream_output(debounce_by=None):
            print(output)
            #> name='test' value=None
            #> name='test' value=42
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

### Output modes（输出模式） {#output-modes}

Pydantic AI 实现了三种让模型输出结构化数据的方法：

1. [Tool Output](#tool-output)：使用 tool calls 生成 output。
2. [Native Output](#native-output)：要求模型生成符合给定 JSON schema 的文本内容。
3. [Prompted Output](#prompted-output)：把包含目标 JSON schema 的 prompt 注入 model instructions，并尝试按需解析模型的纯文本响应。

#### Tool Output（工具输出） {#tool-output}

在默认的 Tool Output mode 中，每个 output type（或 function）的 output JSON schema 会作为一个特殊 output tool 的 parameters schema 提供给模型。这是默认方式，因为几乎所有模型都支持，并且实践表明效果很好。

如果想修改 output tool 的名称、传入自定义 description 来帮助模型，或开启/关闭 strict mode，可以用 [`ToolOutput`][pydantic_ai.output.ToolOutput] marker class 包装相应 type(s)，并提供对应 arguments。请注意，默认情况下 description 来自 Pydantic model 或 output function 上指定的 docstring，因此通常不需要通过 marker class 显式指定。

使用 output tools 时，每个 tool 都有自己的 retry counter。agent retry budget 中 output 侧的预算（通过 `Agent(retries={'output': N})` 用 [`AgentRetries`][pydantic_ai.agent.AgentRetries] 设置，或通过 `agent.run(retries={'output': N})` 在单次 run 上设置）是*默认 per-tool limit*。要覆盖单个 output tool 的限制，请在 `ToolOutput` 上传入 [`max_retries`][pydantic_ai.output.ToolOutput.max_retries]：`ToolOutput(Fruit, max_retries=2)`。它与 text-output 路径全局预算之间的关系参见 [How output retries are enforced](agent.md#how-output-retries-are-enforced)。

要在 agent run 期间动态修改或过滤可用 output tools，可以定义 agent-wide 的 `prepare_output_tools` function，它会在 run 的每一步之前调用。这个 function 应为 [`ToolsPrepareFunc`][pydantic_ai.tools.ToolsPrepareFunc] 类型，接收 [`RunContext`][pydantic_ai.tools.RunContext] 和一组 [`ToolDefinition`][pydantic_ai.tools.ToolDefinition]，并返回新的 tool definitions list；其返回值规则与 [`prepare_tools` function](tools-advanced.md#prepare-tools) 相同。这相当于非 output tools 的 `prepare_tools`。

```python {title="tool_output.py"}
from pydantic import BaseModel

from pydantic_ai import Agent, ToolOutput


class Fruit(BaseModel):
    name: str
    color: str


class Vehicle(BaseModel):
    name: str
    wheels: int


agent = Agent(
    'openai:gpt-5.2',
    output_type=[ # (1)!
        ToolOutput(Fruit, name='return_fruit'),
        ToolOutput(Vehicle, name='return_vehicle'),
    ],
)
result = agent.run_sync('What is a banana?')
print(repr(result.output))
#> Fruit(name='banana', color='yellow')
```

1. 如果只传入 `Fruit` 和 `Vehicle`，且不需要自定义 tool names，本可以使用 union：`output_type=Fruit | Vehicle`。但由于 `ToolOutput` 是 object 而不是 type，因此这里必须使用 list。

_（这个示例是完整的，可以"原样"运行）_

##### 并行 Output Tool Calls {#parallel-output-tool-calls}

当模型在调用 output tool 的同时并行调用其他 tools 时，可以通过设置 agent 的 [`end_strategy`][pydantic_ai.agent.Agent.end_strategy] 控制 tool calls 的执行方式：

- `'early'`（默认）：先执行 output tools。一旦找到有效最终结果，就跳过剩余 function 和 output tool calls
- `'graceful'`：先执行 output tools。一旦找到有效最终结果，就跳过剩余 output tool calls，但仍执行 function tools
- `'exhaustive'`：先执行 output tools，然后执行所有 function tools。第一个有效 output tool result 会成为最终 output

| 策略 | Function tools | Output tools |
|---|---|---|
| `'early'`（默认） | 跳过剩余项 | 跳过剩余项 |
| `'graceful'` | 全部执行 | 跳过剩余项 |
| `'exhaustive'` | 全部执行 | 全部执行（第一个有效结果获胜） |

当 function tools 有重要副作用（例如 logging、发送通知或更新 metrics）且必须始终执行时，`'graceful'` 和 `'exhaustive'` strategies 很有用。如果想避免不必要地执行额外 output tools，应优先使用 `'graceful'` 而不是 `'exhaustive'`；例如，当 output tools 有只应触发一次的副作用时。

!!! warning "Streaming methods 中 output 和 deferred tools 的优先级"
    [`run_stream()`][pydantic_ai.agent.AbstractAgent.run_stream] 和 [`run_stream_sync()`][pydantic_ai.agent.AbstractAgent.run_stream_sync] methods 会把第一个匹配 [output type](output.md#structured-output) 的 output（可能是文本、[output tool](output.md#tool-output) call，或 [deferred](deferred-tools.md) tool call）视为 agent run 的最终 output，即使模型在这个"最终" output 之后又生成了（额外的）tool calls。

    这意味着使用这些 methods 时，如果模型先调用 deferred tools 再调用 output tools，deferred tool calls 会决定 agent run 的最终 output；而其他 [run methods](agent.md#running-agents) 会优先使用 tool output。


#### Native Output（原生输出） {#native-output}

Native Output mode 使用模型原生的 "Structured Outputs" 功能（也称 "JSON Schema response format"），强制模型只输出匹配给定 JSON schema 的文本。请注意，并非所有模型都支持它，而且有时会有额外限制。例如 Gemini 不能在 structured output 的同时使用 tools；尝试这样做会导致错误。

要使用此 mode，可以用 [`NativeOutput`][pydantic_ai.output.NativeOutput] marker class 包装 output type(s)。如果 type 或 function 的名称与 docstring 不够充分，它还允许你指定 `name` 和 `description`。

```python {title="native_output.py" requires="tool_output.py"}
from pydantic_ai import Agent, NativeOutput

from tool_output import Fruit, Vehicle

agent = Agent(
    'openai:gpt-5.2',
    output_type=NativeOutput(
        [Fruit, Vehicle], # (1)!
        name='Fruit_or_vehicle',
        description='Return a fruit or vehicle.'
    ),
)
result = agent.run_sync('What is a Ford Explorer?')
print(repr(result.output))
#> Vehicle(name='Ford Explorer', wheels=4)
```

1. 这里也可以使用 union：`output_type=Fruit | Vehicle`。不过如上文"类型检查注意事项"一节所述，要让它正确通过类型检查，需要在 `Agent` constructor 上显式指定泛型参数，并在这一行添加 `# type: ignore`。

_（这个示例是完整的，可以"原样"运行）_

#### Prompted Output（提示输出） {#prompted-output}

在此 mode 中，会通过模型的 [instructions](agent.md#instructions) 提示模型输出匹配给定 JSON schema 的文本，是否正确解释这些 instructions 取决于模型自身。它适用于所有模型，但通常是最不可靠的方式，因为模型并未被强制匹配 schema。

一般建议优先从 tool 或 native output 开始，但在某些情况下，此 mode 可能生成质量更高的 outputs；对于没有原生 tool calling 或 structured output 支持的模型，它也是生成 structured outputs 的唯一选择。

如果 model API 支持 "JSON Mode" 功能（也称 "JSON Object response format"），用于强制模型输出有效 JSON，Pydantic AI 会启用它；但模型是否遵守 schema 仍取决于模型自身。Pydantic AI 会验证返回的结构化数据，并在验证失败时要求模型重试，但如果模型能力不足，这可能仍不够。

要使用此 mode，可以用 [`PromptedOutput`][pydantic_ai.output.PromptedOutput] marker class 包装 output type(s)。如果 type 或 function 的名称与 docstring 不够充分，它还允许你指定 `name` 和 `description`。此外，`template` 允许你指定自定义 instructions template 来替代 [default][pydantic_ai.profiles.ModelProfile.prompted_output_template]，或用 `template=False` 完全禁用 schema prompt。

```python {title="prompted_output.py" requires="tool_output.py"}
from pydantic import BaseModel

from pydantic_ai import Agent, PromptedOutput

from tool_output import Vehicle


class Device(BaseModel):
    name: str
    kind: str


agent = Agent(
    'openai:gpt-5.2',
    output_type=PromptedOutput(
        [Vehicle, Device], # (1)!
        name='Vehicle or device',
        description='Return a vehicle or device.'
    ),
)
result = agent.run_sync('What is a MacBook?')
print(repr(result.output))
#> Device(name='MacBook', kind='laptop')

agent = Agent(
    'openai:gpt-5.2',
    output_type=PromptedOutput(
        [Vehicle, Device],
        template='Gimme some JSON: {schema}'
    ),
)
result = agent.run_sync('What is a Ford Explorer?')
print(repr(result.output))
#> Vehicle(name='Ford Explorer', wheels=4)
```

1. 这里也可以使用 union：`output_type=Vehicle | Device`。不过如上文"类型检查注意事项"一节所述，要让它正确通过类型检查，需要在 `Agent` constructor 上显式指定泛型参数，并在这一行添加 `# type: ignore`。

_（这个示例是完整的，可以"原样"运行）_

### 自定义 JSON schema {#structured-dict}

如果无法用 Pydantic `BaseModel`、dataclass 或 `TypedDict` 定义所需的 structured output object，例如 JSON schema 来自外部来源或需要动态生成，可以使用 [`StructuredDict()`][pydantic_ai.output.StructuredDict] helper function，生成一个附带 JSON schema 的 `dict[str, Any]` subclass，Pydantic AI 会把它传给模型。

请注意，Pydantic AI 不会对收到的 JSON object 执行任何验证；模型需要自行正确解释 schema 及其中表达的约束，例如 required fields 或 integer value ranges。

output type 会是 `dict[str, Any]`，你的代码需要防御性地读取它，以应对模型出错的情况。你可以使用 [output validator](#output-validator-functions) 把 validation errors 反馈给模型并让它重试。

除了 JSON schema，还可以选择传入 `name` 和 `description` arguments，为模型提供额外上下文：

```python
from pydantic_ai import Agent, StructuredDict

HumanDict = StructuredDict(
    {
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'age': {'type': 'integer'}
        },
        'required': ['name', 'age']
    },
    name='Human',
    description='A human with a name and age',
)

agent = Agent('openai:gpt-5.2', output_type=HumanDict)
result = agent.run_sync('Create a person')
#> {'name': 'John Doe', 'age': 30}
```

### Validation context（验证上下文） {#validation-context}

有些 validation 依赖额外的 Pydantic [context](https://docs.pydantic.dev/latest/concepts/validators/#validation-context) object。你可以在定义 `Agent` 时，通过其 [`validation_context`][pydantic_ai.agent.Agent.__init__] parameter 传入这个 object。它会同时用于 structured outputs 和 [tool arguments](tools-advanced.md#tool-retries) 的验证。

这个 validation context 可以是：

- context object 本身（`Any`），原样用于验证 outputs；或
- 一个接收 [`RunContext`][pydantic_ai.tools.RunContext] 并返回 context object（`Any`）的 function。这个 function 会在每次验证之前自动调用，从而允许你构建动态 validation context。

!!! warning "不要把这个 _validation_ context 和 _LLM_ context 混淆"
    这个 Pydantic validation context object 仅在 Pydantic AI 内部用于 tool arg 和 output validation。尤其要注意，它**不会**包含在发送给语言模型的 prompts 或 messages 中。

```python {title="validation_context.py"}
from dataclasses import dataclass

from pydantic import BaseModel, ValidationInfo, field_validator

from pydantic_ai import Agent


class Value(BaseModel):
    x: int

    @field_validator('x')
    def increment_value(cls, value: int, info: ValidationInfo):
        return value + (info.context or 0)


agent = Agent(
    'google:gemini-3-flash-preview',
    output_type=Value,
    validation_context=10,
)
result = agent.run_sync('Give me a value of 5.')
print(repr(result.output))  # 5 from the model + 10 from the validation context
#> Value(x=15)


@dataclass
class Deps:
    increment: int


agent = Agent(
    'google:gemini-3-flash-preview',
    output_type=Value,
    deps_type=Deps,
    validation_context=lambda ctx: ctx.deps.increment,
)
result = agent.run_sync('Give me a value of 5.', deps=Deps(increment=10))
print(repr(result.output))  # 5 from the model + 10 from the validation context
#> Value(x=15)
```

_（这个示例是完整的，可以"原样"运行）_

### Output validators（输出验证器） {#output-validator-functions}

有些 validation 放在 Pydantic validators 中并不方便，甚至无法实现，尤其是 validation 需要 IO 且为异步时。Pydantic AI 提供了通过 [`agent.output_validator`][pydantic_ai.agent.Agent.output_validator] decorator 添加 validation functions 的方式。

这里 raise 的每个 [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] 都会消耗该 run 的 output retry budget 中的一个单位。预算默认为 `1`，可以通过 `Agent(retries={'output': N})` 使用 [`AgentRetries`][pydantic_ai.agent.AgentRetries] 在 agent 上设置，也可以通过 `agent.run(retries={'output': N})` 在单次 run 上设置，或通过 [`ToolOutput(max_retries=N)`](#tool-output) 针对每个 output tool 设置。在 validator 内部，[`ctx.max_retries`][pydantic_ai.tools.RunContext.max_retries] 反映真正会让你停止的限制（text 路径上的全局预算，或 tool 路径上的 per-tool limit），而 [`ctx.retry`][pydantic_ai.tools.RunContext.retry] 是全局 retry counter，因此在单次 run 内切换 output tools 时仍保持一致。完整执行模型参见 [How output retries are enforced](agent.md#how-output-retries-are-enforced)。

如果想为不同 output types 实现独立 validation logic，建议改用 [output functions](#output-functions)，这样就不必在 output validator 内部执行 `isinstance` 检查。
如果希望模型输出纯文本，再由你自行处理或验证，并让 agent 的最终 output 成为你的 function 结果，建议使用带 [`TextOutput` marker class](#text-output) 的 [output function](#output-functions)。

下面是 [SQL Generation example](examples/sql-gen.md) 的简化变体：

```python {title="sql_gen.py"}
from fake_database import DatabaseConn, QueryError
from pydantic import BaseModel

from pydantic_ai import Agent, RunContext, ModelRetry


class Success(BaseModel):
    sql_query: str


class InvalidRequest(BaseModel):
    error_message: str


Output = Success | InvalidRequest
agent = Agent[DatabaseConn, Output](
    'google:gemini-3-flash-preview',
    output_type=Output,  # type: ignore
    deps_type=DatabaseConn,
    instructions='Generate PostgreSQL flavored SQL queries based on user input.',
)


@agent.output_validator
async def validate_sql(ctx: RunContext[DatabaseConn], output: Output) -> Output:
    if isinstance(output, InvalidRequest):
        return output
    try:
        await ctx.deps.execute(f'EXPLAIN {output.sql_query}')
    except QueryError as e:
        raise ModelRetry(f'Invalid query: {e}') from e
    else:
        return output


result = agent.run_sync(
    'get me users who were last active yesterday.', deps=DatabaseConn()
)
print(result.output)
#> sql_query='SELECT * FROM users WHERE last_active::date = today() - interval 1 day'
```

_（这个示例是完整的，可以"原样"运行）_

#### 在 output validators 中处理部分输出 {#handling-partial-output-in-output-validators}

使用 `run_stream()` 或 `run_stream_sync()` 流式运行时，output validators 会被调用**多次**：模型每产生一次 partial output 会调用一次，最终完整 output 也会调用一次。

当你想**只验证完整结果**，而不是验证中间 partial values 时，应检查 [`RunContext.partial_output`][pydantic_ai.tools.RunContext.partial_output] flag。

流式运行时，每个 partial output 的 `partial_output` 都是 `True`，最终完整 output 的 `partial_output` 是 `False`。
对所有[其他 run methods](agent.md#running-agents)，`partial_output` 始终为 `False`，因为 validator 只会在完整 output 上调用一次。

```python {title="partial_validation_streaming.py" line_length="120"}
from pydantic_ai import Agent, ModelRetry, RunContext

agent = Agent('openai:gpt-5.2')


@agent.output_validator
def validate_output(ctx: RunContext, output: str) -> str:
    if ctx.partial_output:
        return output

    if len(output) < 50:
        raise ModelRetry('Output is too short.')
    return output


async def main():
    async with agent.run_stream('Write a long story about a cat') as result:
        async for message in result.stream_text():
            print(message)
            #> Once upon a
            #> Once upon a time, there was
            #> Once upon a time, there was a curious cat
            #> Once upon a time, there was a curious cat named Whiskers who
            #> Once upon a time, there was a curious cat named Whiskers who loved to explore
            #> Once upon a time, there was a curious cat named Whiskers who loved to explore the world around
            #> Once upon a time, there was a curious cat named Whiskers who loved to explore the world around him...
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

## 图像输出 {#image-output}

有些模型可以把生成的图像作为响应的一部分，例如支持 [Image Generation native tool](native-tools.md#image-generation-tool) 的模型，以及在被要求生成图表时使用 [Code Execution native tool](native-tools.md#code-execution-tool) 的 OpenAI models。

要把生成的图像作为 agent run 的 output，可以把 `output_type` 设置为 [`BinaryImage`][pydantic_ai.messages.BinaryImage]。如果没有显式指定生成图像的 native tool，[`ImageGenerationTool`][pydantic_ai.native_tools.ImageGenerationTool] 会自动启用。

```py {title="image_output.py"}
from pydantic_ai import Agent, BinaryImage

agent = Agent('openai-responses:gpt-5.2', output_type=BinaryImage)

result = agent.run_sync('Generate an image of an axolotl.')
assert isinstance(result.output, BinaryImage)
```

_（这个示例是完整的，可以"原样"运行）_

如果 agent 不需要总是生成图像，可以使用 `BinaryImage` 和 `str` 的 union。如果模型二者都生成，图像会优先作为 output，文本则可通过 [`ModelResponse.text`][pydantic_ai.messages.ModelResponse.text] 获取：

```py {title="image_output_union.py"}
from pydantic_ai import Agent, BinaryImage

agent = Agent('openai-responses:gpt-5.2', output_type=BinaryImage | str)

result = agent.run_sync('Tell me a two-sentence story about an axolotl, no image please.')
print(result.output)
"""
Once upon a time, in a hidden underwater cave, lived a curious axolotl named Pip who loved to explore. One day, while venturing further than usual, Pip discovered a shimmering, ancient coin that granted wishes!
"""

result = agent.run_sync('Tell me a two-sentence story about an axolotl with an illustration.')
assert isinstance(result.output, BinaryImage)
print(result.response.text)
"""
Once upon a time, in a hidden underwater cave, lived a curious axolotl named Pip who loved to explore. One day, while venturing further than usual, Pip discovered a shimmering, ancient coin that granted wishes!
"""
```

## Optional output（允许 `None`） {#optional-output}

有些 agents 完全通过 tool calls 完成工作，并不需要生成最终 output。例如，一个 agent 通过 tool 更新某条记录后就停止。某些模型（尤其是 [Anthropic](models/anthropic.md)）在这种情况下会返回空响应；默认情况下，这会导致 Pydantic AI 重试，直到模型生成内容。

如果想把空响应视为成功 run，请在 `output_type` 中包含 `None`：

```python {title="optional_output.py"}
from pydantic_ai import Agent

agent = Agent('anthropic:claude-opus-4-6', output_type=str | None)


@agent.tool_plain
def mark_task_done(task_id: int) -> str:
    """Mark the task as done."""
    return f'Task {task_id} marked done.'


result = agent.run_sync('Mark task 1 as done, then stop without saying anything.')
print(result.output)
#> None
```

当模型返回空响应且 `None` 是允许的 output type 时，agent 会返回 `None` 而不是重试。[Output validator functions](#output-validator-functions) 仍会以 `None` 作为 argument 运行，因此你可以在需要时 raise [`ModelRetry`][pydantic_ai.exceptions.ModelRetry] 来拒绝它。

`output_type=str | None` 是典型场景：它会作为常规 text output 处理，模型发出 `None` 信号的**唯一**方式是返回空响应，不涉及 output tool 或 structured schema。这与普通 `str` 已被特殊处理为 free-form text output 而不是 structured tool call 的方式一致。

其他 output modes 也支持 `None`；除了（或替代）empty-response fallback，还会有额外的 structured commit path：

- **使用 tool mode 且包含 `None` 的裸 unions**：例如 `output_type=int | None`、`output_type=[int, float, None]`，或 `output_type=[ToolOutput(Foo), None]`。专用的 `final_result_NoneType` output tool 会与其他 output tools 一起暴露，因此模型可以通过 tool call 提交 `None`。与 `str | None` 一样，空 model response 仍会被视为 `None`。
- **显式 output mode markers**：例如 `output_type=ToolOutput(int | None)`、`output_type=NativeOutput([int, None])`，或 `output_type=PromptedOutput([int, None])`。`None` 会作为 wrapper 生成的 structured schema 的一个分支。模型会通过用 `null` 调用 tool（对 `ToolOutput`），或选择 discriminated schema 的 `NoneType` 分支（对 `NativeOutput`/`PromptedOutput`）来提交。空响应**不会**被接受；一旦你选择显式 structured output mode，就预期模型通过 schema 提交结果。

!!! note "注意"
    单独使用 `output_type=None` 无效；必须至少在 `None` 旁边提供一个其他 output type。

!!! note "注意"
    使用 optional output type 调用 [`agent.run_stream()`][pydantic_ai.Agent.run_stream] 时，空 model response 没有可 yield 的中间值，因此 [`stream_output()`][pydantic_ai.result.StreamedRunResult.stream_output] 在这种情况下会产生空 iterator。请改用 [`get_output()`][pydantic_ai.result.StreamedRunResult.get_output] 获取最终的 `None` 值。

## 流式结果 {#streamed-results}

流式结果有两个主要挑战：

1. 在结构化响应完成之前验证它们。这通过 Pydantic 最近在 [pydantic/pydantic#10748](https://github.com/pydantic/pydantic/pull/10748) 中加入的 "partial validation" 实现。
2. 接收响应时，如果不先开始 stream 并查看内容，就无法知道它是否是最终响应。Pydantic AI 会 stream 足够多的响应内容，用来判断它是 tool call 还是 output；然后继续 stream 完整内容并调用 tools，或把 stream 作为 [`StreamedRunResult`][pydantic_ai.result.StreamedRunResult] 返回。

!!! note "注意"
    由于 `run_stream()` method 会把第一个匹配 `output_type` 的 output 视为最终 output，
    它会停止运行 agent graph，并且不会执行模型在这个"最终" output 之后发出的任何 tool calls。

    如果希望始终把 agent graph 运行到完成，并 stream 模型 streaming response 以及 agent 执行 tools 时产生的所有 events，
    请改用 [`agent.run_stream_events()`][pydantic_ai.agent.AbstractAgent.run_stream_events]（[文档](agent.md#streaming-all-events)）或 [`agent.iter()`][pydantic_ai.agent.AbstractAgent.iter]（[文档](agent.md#streaming-all-events-and-output)）。

### 流式文本 {#streaming-text}

流式文本 output 示例：

```python {title="streamed_hello_world.py" line_length="120"}
from pydantic_ai import Agent

agent = Agent('google:gemini-3-flash-preview')  # (1)!


async def main():
    async with agent.run_stream('Where does "hello world" come from?') as result:  # (2)!
        async for message in result.stream_text():  # (3)!
            print(message)
            #> The first known
            #> The first known use of "hello,
            #> The first known use of "hello, world" was in
            #> The first known use of "hello, world" was in a 1974 textbook
            #> The first known use of "hello, world" was in a 1974 textbook about the C
            #> The first known use of "hello, world" was in a 1974 textbook about the C programming language.
```

1. Streaming 可与标准 [`Agent`][pydantic_ai.Agent] class 一起使用，不需要任何特殊设置，只需要支持 streaming 的模型（目前所有模型都支持 streaming）。
2. [`Agent.run_stream()`][pydantic_ai.agent.AbstractAgent.run_stream] method 用于启动 streamed run；该 method 返回 context manager，因此 stream 完成时可以关闭连接。
3. [`StreamedRunResult.stream_text()`][pydantic_ai.result.StreamedRunResult.stream_text] yield 的每一项都是完整文本响应，并会随着接收新数据而扩展。

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

也可以把文本作为 deltas 流式输出，而不是在每一项中输出完整文本：

```python {title="streamed_delta_hello_world.py"}
from pydantic_ai import Agent

agent = Agent('google:gemini-3-flash-preview')


async def main():
    async with agent.run_stream('Where does "hello world" come from?') as result:
        async for message in result.stream_text(delta=True):  # (1)!
            print(message)
            #> The first known
            #> use of "hello,
            #> world" was in
            #> a 1974 textbook
            #> about the C
            #> programming language.
```

1. 如果响应不是文本，[`stream_text`][pydantic_ai.result.StreamedRunResult.stream_text] 会报错。

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

!!! warning "`messages` 中不包含 output message"
    如果使用 `.stream_text(delta=True)`，最终 output message **不会**添加到 result messages 中；
    更多信息请参阅 [Messages and chat history](message-history.md)。

### 流式结构化输出 {#streaming-structured-output}

下面是随着 user profile 构建过程进行流式输出的示例：

```python {title="streamed_user_profile.py" line_length="120"}
from datetime import date

from typing_extensions import NotRequired, TypedDict

from pydantic_ai import Agent


class UserProfile(TypedDict):
    name: str
    dob: NotRequired[date]
    bio: NotRequired[str]


agent = Agent(
    'openai:gpt-5.2',
    output_type=UserProfile,
    instructions='Extract a user profile from the input',
)


async def main():
    user_input = 'My name is Ben, I was born on January 28th 1990, I like the chain the dog and the pyramid.'
    async with agent.run_stream(user_input) as result:
        async for profile in result.stream_output():
            print(profile)
            #> {'name': 'Ben'}
            #> {'name': 'Ben'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the '}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyr'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
```

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

由于设置 `output_type` 默认使用 [Tool Output](#tool-output) mode，因此只有模型支持 streaming tool arguments 时，这种方式才有效。对于 Gemini 这类不支持的模型，请改用 [Native Output](#native-output) 或 [Prompted Output](#prompted-output)。

### 流式 Model Responses {#streaming-model-responses}

如果需要对 validation 进行细粒度控制，可以使用下面的模式获取完整的 partial [`ModelResponse`][pydantic_ai.messages.ModelResponse]：

```python {title="streamed_user_profile.py" line_length="120"}
from datetime import date

from pydantic import ValidationError
from typing_extensions import TypedDict

from pydantic_ai import Agent


class UserProfile(TypedDict, total=False):
    name: str
    dob: date
    bio: str


agent = Agent('openai:gpt-5.2', output_type=UserProfile)


async def main():
    user_input = 'My name is Ben, I was born on January 28th 1990, I like the chain the dog and the pyramid.'
    async with agent.run_stream(user_input) as result:
        async for message in result.stream_response(debounce_by=0.01):  # (1)!
            try:
                profile = await result.validate_response_output(  # (2)!
                    message,
                    allow_partial=message.state == 'incomplete',
                )
            except ValidationError:
                continue
            print(profile)
            #> {'name': 'Ben'}
            #> {'name': 'Ben'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the '}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyr'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
            #> {'name': 'Ben', 'dob': date(1990, 1, 28), 'bio': 'Likes the chain the dog and the pyramid'}
```

1. [`stream_response`][pydantic_ai.result.StreamedRunResult.stream_response] 会把数据作为 [`ModelResponse`][pydantic_ai.messages.ModelResponse] objects 进行 stream，因此 iteration 不会因 `ValidationError` 失败。
2. [`validate_response_output`][pydantic_ai.result.StreamedRunResult.validate_response_output] 会验证数据；`allow_partial=True` 会启用 pydantic 在 `TypeAdapter` 上的 [`experimental_allow_partial` flag][pydantic.type_adapter.TypeAdapter.validate_json]。

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

### 取消 Streams {#cancelling-streams}

有时你需要在 streaming response 完成前停止它：用户在 chat UI 中点击"停止生成"，你已经收到足够数据可以做决定，或想避免继续接收更多 tokens。[`run_stream()`][pydantic_ai.agent.AbstractAgent.run_stream] 和 [`iter()`][pydantic_ai.agent.Agent.iter] 支持通过关闭底层 model stream 来显式取消。[`run_stream_events()`][pydantic_ai.agent.AbstractAgent.run_stream_events] 应作为 async context manager 使用，这样在停止消费 events 时可以确定性地执行 cleanup。

!!! note "模型支持"
    [`OutlinesModel`][pydantic_ai.models.outlines.OutlinesModel] 和已弃用的 [`GeminiModel`][pydantic_ai.models.gemini.GeminiModel] 目前不支持 stream cancellation。
    Google、xAI 和 Hugging Face SDKs 只把 streaming 暴露为 async iterators，这会限制 [`cancel()`][pydantic_ai.result.StreamedRunResult.cancel] 能在何时中断正在进行的 chunk read。推荐模式请参阅 [Google](models/google.md#streaming-cancellation)、[xAI](models/xai.md#streaming-cancellation) 和 [Hugging Face](models/huggingface.md#streaming-cancellation) provider docs。

#### 清理 `run_stream_events` {#cleaning-up-run-stream-events}

[`run_stream_events()`][pydantic_ai.agent.AbstractAgent.run_stream_events] 返回 [`AgentEventStream`][pydantic_ai.result.AgentEventStream]，应将其作为 async context manager 使用：

```python {title="stream_cancel_run_stream_events.py"}
from pydantic_ai import Agent, FinalResultEvent, PartStartEvent

agent = Agent('openai:gpt-5.2')


async def main():
    async with agent.run_stream_events('Write a long essay about Python') as stream:  # (1)!
        async for event in stream:
            if isinstance(event, PartStartEvent):
                print(f'Started: {event.part!r}')
                #> Started: TextPart(content='Python is a ')
            elif isinstance(event, FinalResultEvent):
                break  # (2)!
```

1. 使用 `async with` 确保正确清理 background task 和 HTTP connection。不带 `async with` 直接 iteration `run_stream_events()` 已弃用。
2. 跳出 loop 会离开 `async with` block，从而关闭 event stream 并执行 cleanup。

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

`run_stream_events()` 不暴露 `cancel()` method。如果需要显式 model-response cancellation handle，请使用 [`run_stream()`][pydantic_ai.agent.AbstractAgent.run_stream] 或 [`agent.iter()`][pydantic_ai.agent.Agent.iter]。

#### 取消 `run_stream` {#cancelling-run-stream}

在 [`StreamedRunResult`][pydantic_ai.result.StreamedRunResult] 上调用 `cancel()` 可以取消 stream：

```python {title="stream_cancel_run_stream.py"}
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')


async def main():
    async with agent.run_stream('Write a long essay about Python') as result:
        text = ''
        async for chunk in result.stream_text(delta=True):
            text += chunk
            if len(text) > 100:  # (1)!
                await result.cancel()  # (2)!
                break
        print(result.cancelled)  # (3)!
        #> True
        print(result.response.state == 'interrupted')  # (4)!
        #> True
```

1. 在 streaming 期间检查某个条件，例如是否已经收到足够文本。
2. `cancel()` 会告诉 model provider 停止生成 tokens，并在 model integration 支持时关闭 HTTP connection。
3. `cancelled` property 反映 cancellation state。
4. 最终 [`ModelResponse`][pydantic_ai.messages.ModelResponse] 会标记为 `state='interrupted'`，让下游代码能够识别 incomplete responses。

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

如果从 `stream_text()` 中 `break`，然后离开外层 `async with` block，stream 会在 context 退出时被清理。当你想立即停止生成，而不只是停止本地消费时，请使用 `cancel()`。

!!! warning "被中断的 tool calls"
    取消或跳出 model response stream 后，最终 [`ModelResponse`][pydantic_ai.messages.ModelResponse] 可能带有不完整的 tool-call arguments。Pydantic AI 会用 `state='interrupted'` 记录该响应，但不会过滤不完整 tool calls、合成 tool returns，或为这些 partial responses 定义 run-resumption 行为。如果你用 [`agent.iter()`][pydantic_ai.agent.Agent.iter] 控制 graph，也要停止外层 run loop，或在允许 run 继续进入 tool execution 前检查 `response.state == 'interrupted'`。

#### 使用 `iter` 取消 {#cancelling-with-iter}

使用 [`agent.iter()`][pydantic_ai.agent.Agent.iter] 对 agent graph 进行细粒度控制时，可以在 `ModelRequestNode.stream()` context 内取消 [`AgentStream`][pydantic_ai.result.AgentStream]：

```python {title="stream_cancel_iter.py"}
from pydantic_ai import Agent, FinalResultEvent

agent = Agent('openai:gpt-5.2')


async def main():
    async with agent.iter('Write a long essay about Python') as run:
        async for node in run:
            if Agent.is_model_request_node(node):
                async with node.stream(run.ctx) as stream:
                    async for event in stream:
                        if isinstance(event, FinalResultEvent):
                            await stream.cancel()  # (1)!
                            break
```

1. `AgentStream.cancel()` 会在 model request 层级取消 stream。

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

#### 取消后的 Message History {#message-history-after-cancellation}

当 stream 被取消时，响应会以 `state='interrupted'` 记录在 message history 中。History 会包含取消前收到的所有 partial content：

```python {title="stream_cancel_history.py"}
from pydantic_ai import Agent

agent = Agent('openai:gpt-5.2')


async def main():
    async with agent.run_stream('Tell me about Python') as result:
        async for text in result.stream_text(delta=True):
            break
        await result.cancel()

    messages = result.all_messages()  # (1)!
    print(messages[-1].state)  # (2)!
    #> interrupted
```

1. Message history 包含被中断的响应，以及取消前收到的所有 partial content。
2. Interrupted response state 允许你的应用在复用 history 前决定是保留、检查还是丢弃 partial response。

_（这个示例是完整的，可以"原样"运行；你需要添加 `asyncio.run(main())` 来运行 `main`）_

!!! warning "复用 interrupted history"
    Pydantic AI 不会清理 interrupted responses 中不完整的 tool calls。因此，如果取消发生时模型正在生成 tool call，直接把 interrupted history 传入另一个 run 可能会失败或导致 retries。目前，复用 interrupted history 的应用应检查 `state='interrupted'` responses，并应用自己的策略。

!!! info "已取消 streams 的 usage tracking"
    取消后 `usage()` 报告的 token usage 是部分数据，并且依赖 provider。Pydantic AI 会立即停止从 stream 拉取数据，因此最终 usage events 可能永远不会到达；某些 provider SDKs 也可能在本地 stream 关闭后继续在服务端生成。不要依赖 cancelled-stream usage 进行成本关键的 accounting。
    对于 OpenAI chat completions，[`openai_continuous_usage_stats`][pydantic_ai.models.openai.OpenAIChatModelSettings] 可以通过随每个 chunk 请求累计 usage data 来改善 in-stream usage reporting，但 cancelled-stream usage 仍是 best-effort。

## 示例 {#examples}

以下示例展示如何在 Pydantic AI 中使用 streamed responses：

- [流式 Markdown](examples/stream-markdown.md)
- [流式 Whales 示例](examples/stream-whales.md)
