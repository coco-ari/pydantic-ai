# 直接模型请求

`direct` 模块提供底层方法，用于以命令式方式向 LLM 发起请求；这里唯一的抽象是输入和输出 schema 转换，让你可以用同一个 API 使用所有模型。

这些方法是 [`Model`][pydantic_ai.models.Model] 实现之上的薄包装。当你不需要 [`Agent`][pydantic_ai.Agent] 的完整功能时，它们提供了更简单的接口。

可用函数如下：

- [`model_request`][pydantic_ai.direct.model_request]：向模型发起非流式 async 请求
- [`model_request_sync`][pydantic_ai.direct.model_request_sync]：向模型发起非流式同步请求
- [`model_request_stream`][pydantic_ai.direct.model_request_stream]：向模型发起流式 async 请求
- [`model_request_stream_sync`][pydantic_ai.direct.model_request_stream_sync]：向模型发起流式同步请求

## 基础示例

下面是一个简单示例，展示如何使用 direct API 发起基础请求：

```python title="direct_basic.py"
from pydantic_ai import ModelRequest
from pydantic_ai.direct import model_request_sync

# Make a synchronous request to the model
model_response = model_request_sync(
    'anthropic:claude-haiku-4-5',
    [ModelRequest.user_text_prompt('What is the capital of France?')]
)

print(model_response.parts[0].content)
#> The capital of France is Paris.
print(model_response.usage)
#> RequestUsage(input_tokens=56, output_tokens=7)
```

_（这个示例是完整的，可以“原样”运行。）_

!!! note
    Instructions 不会在 message history 中累计。如果多个 [`ModelRequest`][pydantic_ai.messages.ModelRequest] 包含 [`instructions`][pydantic_ai.messages.ModelRequest.instructions]，direct API 会使用最新的一条。

## 带工具调用的高级示例

你也可以使用 direct API 处理 function/tool calling。

即使在这里，我们也可以使用 Pydantic 为工具生成 JSON schema：

```python
from typing import Literal

from pydantic import BaseModel

from pydantic_ai import ModelRequest, ToolDefinition
from pydantic_ai.direct import model_request
from pydantic_ai.models import ModelRequestParameters


class Divide(BaseModel):
    """Divide two numbers."""

    numerator: float
    denominator: float
    on_inf: Literal['error', 'infinity'] = 'infinity'


async def main():
    # Make a request to the model with tool access
    model_response = await model_request(
        'openai:gpt-5-nano',
        [ModelRequest.user_text_prompt('What is 123 / 456?')],
        model_request_parameters=ModelRequestParameters(
            function_tools=[
                ToolDefinition(
                    name=Divide.__name__.lower(),
                    description=Divide.__doc__,
                    parameters_json_schema=Divide.model_json_schema(),
                )
            ],
            allow_text_output=True,  # Allow model to either use tools or respond directly
        ),
    )
    print(model_response)
    """
    ModelResponse(
        parts=[
            ToolCallPart(
                tool_name='divide',
                args={'numerator': '123', 'denominator': '456'},
                tool_call_id='pyd_ai_2e0e396768a14fe482df90a29a78dc7b',
            )
        ],
        usage=RequestUsage(input_tokens=55, output_tokens=7),
        model_name='gpt-5-nano',
        timestamp=datetime.datetime(...),
    )
    """
```

_（这个示例是完整的，可以“原样”运行；你需要添加 `asyncio.run(main())` 来运行 `main`。）_

## 何时使用 direct API 而不是 Agent

direct API 适合以下情况：

1. 你需要对模型交互进行更直接的控制
2. 你想围绕模型请求实现自定义行为
3. 你正在模型交互之上构建自己的抽象

对大多数应用用例而言，更高层的 [`Agent`][pydantic_ai.Agent] API 提供了更方便的接口，并附带原生工具执行、重试、结构化输出解析等额外功能。

## OpenTelemetry 或 Logfire 插桩

和 [agents][pydantic_ai.Agent] 一样，只需几行额外代码就可以启用 OpenTelemetry/Logfire 插桩：

```python {title="direct_instrumented.py" hl_lines="1 6 7"}
import logfire

from pydantic_ai import ModelRequest
from pydantic_ai.direct import model_request_sync

logfire.configure()
logfire.instrument_pydantic_ai()

# Make a synchronous request to the model
model_response = model_request_sync(
    'anthropic:claude-haiku-4-5',
    [ModelRequest.user_text_prompt('What is the capital of France?')],
)

print(model_response.parts[0].content)
#> The capital of France is Paris.
```

_（这个示例是完整的，可以“原样”运行。）_

你也可以按单次调用启用 OpenTelemetry：

```python {title="direct_instrumented.py" hl_lines="1 6 12"}
import logfire

from pydantic_ai import ModelRequest
from pydantic_ai.direct import model_request_sync

logfire.configure()

# Make a synchronous request to the model
model_response = model_request_sync(
    'anthropic:claude-haiku-4-5',
    [ModelRequest.user_text_prompt('What is the capital of France?')],
    instrument=True
)

print(model_response.parts[0].content)
#> The capital of France is Paris.
```

更多细节参见[调试和监控](logfire.md)，包括如何在不使用 Logfire 的情况下用普通 OpenTelemetry 插桩。
