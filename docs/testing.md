# 单元测试

为 Pydantic AI 代码编写单元测试，就像为其他 Python 代码编写单元测试一样。

因为它们大体上并没有什么新东西，所以我们已经有非常成熟的工具和模式来编写和运行这类测试。

除非你非常确定自己有更好的办法，否则大致应遵循以下策略：

- 使用 [`pytest`](https://docs.pytest.org/en/stable/) 作为测试框架
- 如果发现自己在写很长的断言，使用 [inline-snapshot](https://15r10nk.github.io/inline-snapshot/latest/)
- 类似地，[dirty-equals](https://dirty-equals.helpmanual.io/latest/) 对比较大型数据结构很有用
- 使用 [`TestModel`][pydantic_ai.models.test.TestModel] 或 [`FunctionModel`][pydantic_ai.models.function.FunctionModel] 代替真实模型，以避免真实 LLM 调用的使用成本、延迟和可变性
- 使用 [`Agent.override`][pydantic_ai.agent.Agent.override] 在应用逻辑中替换智能体的模型、依赖或 toolsets
- 全局设置 [`ALLOW_MODEL_REQUESTS=False`][pydantic_ai.models.ALLOW_MODEL_REQUESTS]，阻止测试中意外向非测试模型发起请求

### 使用 `TestModel` 进行单元测试

执行大多数应用代码的最简单、最快方式是使用 [`TestModel`][pydantic_ai.models.test.TestModel]。默认情况下，它会调用智能体中的所有工具，然后根据智能体返回类型返回纯文本或结构化响应。

!!! note "`TestModel` 不是魔法"
    `TestModel` 中“聪明”（但没有过度聪明）的部分是：它会尝试基于已注册工具的 schema，为 [function tools](tools.md) 和[输出类型](output.md#structured-output)生成有效的结构化数据。

    `TestModel` 中没有 ML 或 AI，它只是普通的过程式 Python 代码，尝试生成满足工具 JSON schema 的数据。

    生成的数据不会漂亮或相关，但多数情况下应该能通过 Pydantic 校验。
    如果你想要更复杂的能力，请使用 [`FunctionModel`][pydantic_ai.models.function.FunctionModel] 并编写自己的数据生成逻辑。

!!! note "测试带原生工具的智能体"
    [`TestModel`][pydantic_ai.models.test.TestModel] 无法模拟由 provider 执行的[原生工具](native-tools.md)。
    如果你的生产智能体通过 `capabilities` 配置了原生工具，请在测试中使用
    `agent.override(model=TestModel(), native_tools=[])` 覆盖它们，除非测试专门检查原生工具是否传给模型。

我们来为以下应用代码编写单元测试：

```python {title="weather_app.py"}
import asyncio
from datetime import date

from pydantic_ai import Agent, RunContext

from fake_database import DatabaseConn  # (1)!
from weather_service import WeatherService  # (2)!

weather_agent = Agent(
    'openai:gpt-5.2',
    deps_type=WeatherService,
    instructions='Providing a weather forecast at the locations the user provides.',
)


@weather_agent.tool
def weather_forecast(
    ctx: RunContext[WeatherService], location: str, forecast_date: date
) -> str:
    if forecast_date < date.today():  # (3)!
        return ctx.deps.get_historic_weather(location, forecast_date)
    else:
        return ctx.deps.get_forecast(location, forecast_date)


async def run_weather_forecast(  # (4)!
    user_prompts: list[tuple[str, int]], conn: DatabaseConn
):
    """Run weather forecast for a list of user prompts and save."""
    async with WeatherService() as weather_service:

        async def run_forecast(prompt: str, user_id: int):
            result = await weather_agent.run(prompt, deps=weather_service)
            await conn.store_forecast(user_id, result.output)

        # run all prompts in parallel
        await asyncio.gather(
            *(run_forecast(prompt, user_id) for (prompt, user_id) in user_prompts)
        )
```

1. `DatabaseConn` 是一个保存数据库连接的类
2. `WeatherService` 有获取天气预报和历史天气数据的方法
3. 我们需要根据日期是过去还是未来调用不同 endpoint；下面会看到为什么这个细节很重要
4. 这是我们想要测试的函数，以及它使用的智能体

这里有一个函数，它接受 `#!python (user_prompt, user_id)` 元组列表，为每个 prompt 获取天气预报，并将结果存储到数据库中。

**我们想测试这段代码，但不想 mock 某些对象，也不想修改代码来传入测试对象。**

下面是使用 [`TestModel`][pydantic_ai.models.test.TestModel] 编写测试的方式：

```python {title="test_weather_app.py" call_name="test_forecast" requires="weather_app.py"}
from datetime import timezone
import pytest

from dirty_equals import IsNow, IsStr

from pydantic_ai import models, capture_run_messages, RequestUsage
from pydantic_ai.models.test import TestModel
from pydantic_ai import (
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
    ModelRequest,
)

from fake_database import DatabaseConn
from weather_app import run_weather_forecast, weather_agent

pytestmark = pytest.mark.anyio  # (1)!
models.ALLOW_MODEL_REQUESTS = False  # (2)!


async def test_forecast():
    conn = DatabaseConn()
    user_id = 1
    with capture_run_messages() as messages:
        with weather_agent.override(model=TestModel()):  # (3)!
            prompt = 'What will the weather be like in London on 2024-11-28?'
            await run_weather_forecast([(prompt, user_id)], conn)  # (4)!

    forecast = await conn.get_forecast(user_id)
    assert forecast == '{"weather_forecast":"Sunny with a chance of rain"}'  # (5)!

    assert messages == [  # (6)!
        ModelRequest(
            parts=[
                UserPromptPart(
                    content='What will the weather be like in London on 2024-11-28?',
                    timestamp=IsNow(tz=timezone.utc),  # (7)!
                ),
            ],
            instructions='Providing a weather forecast at the locations the user provides.',
            timestamp=IsNow(tz=timezone.utc),
            run_id=IsStr(),
            conversation_id=IsStr(),
        ),
        ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name='weather_forecast',
                    args={
                        'location': 'a',
                        'forecast_date': '2024-01-01',  # (8)!
                    },
                    tool_call_id=IsStr(),
                )
            ],
            usage=RequestUsage(
                input_tokens=60,
                output_tokens=7,
            ),
            model_name='test',
            timestamp=IsNow(tz=timezone.utc),
            run_id=IsStr(),
            conversation_id=IsStr(),
        ),
        ModelRequest(
            parts=[
                ToolReturnPart(
                    tool_name='weather_forecast',
                    content='Sunny with a chance of rain',
                    tool_call_id=IsStr(),
                    timestamp=IsNow(tz=timezone.utc),
                ),
            ],
            instructions='Providing a weather forecast at the locations the user provides.',
            timestamp=IsNow(tz=timezone.utc),
            run_id=IsStr(),
            conversation_id=IsStr(),
        ),
        ModelResponse(
            parts=[
                TextPart(
                    content='{"weather_forecast":"Sunny with a chance of rain"}',
                )
            ],
            usage=RequestUsage(
                input_tokens=66,
                output_tokens=16,
            ),
            model_name='test',
            timestamp=IsNow(tz=timezone.utc),
            run_id=IsStr(),
            conversation_id=IsStr(),
        ),
    ]
```

1. 我们使用 [anyio](https://anyio.readthedocs.io/en/stable/) 运行 async tests。
2. 这是安全措施，确保测试时不会意外向 LLM 发起真实请求；更多细节见 [`ALLOW_MODEL_REQUESTS`][pydantic_ai.models.ALLOW_MODEL_REQUESTS]。
3. 我们使用 [`Agent.override`][pydantic_ai.agent.Agent.override] 将智能体模型替换为 [`TestModel`][pydantic_ai.models.test.TestModel]。`override` 的好处是可以在 agent 内部替换模型，而不需要访问调用 agent `run*` 方法的位置。
4. 现在我们在 `override` context manager 中调用想测试的函数。
5. 默认情况下，`TestModel` 会返回一个 JSON 字符串，总结调用了哪些工具以及返回了什么。如果你想自定义更贴近领域的响应，可以在定义 `TestModel` 时添加 [`custom_output_text='Sunny'`][pydantic_ai.models.test.TestModel.custom_output_text]。
6. 到目前为止，我们其实还不知道调用了哪些工具以及使用了哪些值。可以使用 [`capture_run_messages`][pydantic_ai.capture_run_messages] 检查最近一次 run 的 messages，并断言智能体与模型之间的交互如预期发生。
7. [`IsNow`][dirty_equals.IsNow] helper 允许我们对包含随时间变化 timestamp 的数据使用声明式断言。
8. `TestModel` 并没有聪明到能从 prompt 中提取值，所以这些值是硬编码的。

### 使用 `FunctionModel` 进行单元测试

上面的测试是一个很好的开始，但仔细的读者会注意到，`WeatherService.get_forecast` 从未被调用，因为 `TestModel` 使用过去的日期调用了 `weather_forecast`。

为了完整执行 `weather_forecast`，我们需要使用 [`FunctionModel`][pydantic_ai.models.function.FunctionModel] 自定义工具调用方式。

下面是使用 `FunctionModel` 以自定义输入测试 `weather_forecast` 工具的示例：

```python {title="test_weather_app2.py" call_name="test_forecast_future" requires="weather_app.py"}
import re

import pytest

from pydantic_ai import models
from pydantic_ai import (
    ModelMessage,
    ModelResponse,
    TextPart,
    ToolCallPart,
)
from pydantic_ai.models.function import AgentInfo, FunctionModel

from fake_database import DatabaseConn
from weather_app import run_weather_forecast, weather_agent

pytestmark = pytest.mark.anyio
models.ALLOW_MODEL_REQUESTS = False


def call_weather_forecast(  # (1)!
    messages: list[ModelMessage], info: AgentInfo
) -> ModelResponse:
    if len(messages) == 1:
        # first call, call the weather forecast tool
        user_prompt = messages[0].parts[-1]
        m = re.search(r'\d{4}-\d{2}-\d{2}', user_prompt.content)
        assert m is not None
        args = {'location': 'London', 'forecast_date': m.group()}  # (2)!
        return ModelResponse(parts=[ToolCallPart('weather_forecast', args)])
    else:
        # second call, return the forecast
        msg = messages[-1].parts[0]
        assert msg.part_kind == 'tool-return'
        return ModelResponse(parts=[TextPart(f'The forecast is: {msg.content}')])


async def test_forecast_future():
    conn = DatabaseConn()
    user_id = 1
    with weather_agent.override(model=FunctionModel(call_weather_forecast)):  # (3)!
        prompt = 'What will the weather be like in London on 2032-01-01?'
        await run_weather_forecast([(prompt, user_id)], conn)

    forecast = await conn.get_forecast(user_id)
    assert forecast == 'The forecast is: Rainy with a chance of sun'
```

1. 我们定义 `call_weather_forecast` 函数，它会被 `FunctionModel` 调用来代替 LLM。这个函数可以访问组成 run 的 [`ModelMessage`][pydantic_ai.messages.ModelMessage] 列表，以及包含 agent、function tools 和 return tools 信息的 [`AgentInfo`][pydantic_ai.models.function.AgentInfo]。
2. 我们的函数稍微有点智能，会尝试从 prompt 中提取日期，但 location 仍是硬编码。
3. 我们使用 [`FunctionModel`][pydantic_ai.models.function.FunctionModel] 将智能体模型替换为自定义函数。

### 通过 pytest fixtures 覆盖模型

如果你要编写大量都需要覆盖模型的测试，可以使用 [pytest fixtures](https://docs.pytest.org/en/6.2.x/fixture.html)，以可复用方式用 [`TestModel`][pydantic_ai.models.test.TestModel] 或 [`FunctionModel`][pydantic_ai.models.function.FunctionModel] 覆盖模型。

下面是一个用 `TestModel` 覆盖模型的 fixture 示例：

```python {title="test_agent.py" requires="weather_app.py"}
import pytest

from pydantic_ai.models.test import TestModel

from weather_app import weather_agent


@pytest.fixture
def override_weather_agent():
    with weather_agent.override(model=TestModel()):
        yield


async def test_forecast(override_weather_agent: None):
    ...
    # test code here
```
