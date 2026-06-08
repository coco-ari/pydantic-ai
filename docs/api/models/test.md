# `pydantic_ai.models.test`

用于快速测试使用 Pydantic AI 构建的应用的工具模型。

下面是一个最小示例：

```py {title="test_model_usage.py" call_name="test_my_agent" noqa="I001"}
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel

my_agent = Agent('openai:gpt-5.2', instructions='...')


async def test_my_agent():
    """Unit test for my_agent, to be run by pytest."""
    m = TestModel()
    with my_agent.override(model=m):
        result = await my_agent.run('Testing my agent...')
        assert result.output == 'success (no tool calls)'
    assert m.last_model_request_parameters.function_tools == []
```

详细文档请参见[使用 `TestModel` 进行单元测试](../../testing.md#unit-testing-with-testmodel)。

::: pydantic_ai.models.test
