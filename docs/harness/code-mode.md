# Code Mode 代码模式 {#code-mode}

Code mode 是 [**Pydantic AI Harness**](overview.md) 中的一项能力，Pydantic AI Harness 是 Pydantic AI 的官方能力库。完整文档位于 [harness 仓库](https://github.com/pydantic/pydantic-ai-harness)，本页只是简短介绍。

[`CodeMode`](https://github.com/pydantic/pydantic-ai-harness/blob/main/pydantic_ai_harness/code_mode/README.md) 会把你的工具包装成一个由 [Monty](https://github.com/pydantic/monty) 沙箱驱动的 `run_code` 工具。模型会编写 Python，在一次工具调用中使用循环、条件、变量和 `asyncio.gather` 调用多个工具。

标准工具调用每次工具调用都需要一次模型往返。一个需要获取 10 个项目并逐个处理的智能体会产生 11 次以上模型调用，速度慢、成本高且占用大量上下文。Code mode 会把这些压缩为一次调用。

## 使用

```bash
uv add "pydantic-ai-harness[code-mode]"
```

```python {test="skip" noqa="I001"}
from pydantic_ai import Agent
from pydantic_ai_harness import CodeMode

agent = Agent('anthropic:claude-sonnet-4-6', capabilities=[CodeMode()])


@agent.tool_plain
def get_weather(city: str) -> dict:
    """Get current weather for a city."""
    return {'city': city, 'temp_f': 72, 'condition': 'sunny'}


@agent.tool_plain
def convert_temp(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius."""
    return round((fahrenheit - 32) * 5 / 9, 1)


result = agent.run_sync("What's the weather in Paris and Tokyo, in Celsius?")
print(result.output)
```

模型会编写类似下面的代码：

```python {test="skip" lint="skip"}
paris, tokyo = await asyncio.gather(
    get_weather(city='Paris'),
    get_weather(city='Tokyo'),
)
paris_c = await convert_temp(fahrenheit=paris['temp_f'])
tokyo_c = await convert_temp(fahrenheit=tokyo['temp_f'])
{'paris': paris_c, 'tokyo': tokyo_c}
```

## 完整文档

有关选择性工具沙箱、基于元数据的选择、返回值处理、REPL 状态、可观测性、沙箱限制、完整 API 和 agent spec 用法，请参见 harness 仓库中的 [Code Mode README](https://github.com/pydantic/pydantic-ai-harness/blob/main/pydantic_ai_harness/code_mode/README.md)。
