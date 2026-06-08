# `pydantic_ai.models.function`

由本地函数控制的模型。

[`FunctionModel`][pydantic_ai.models.function.FunctionModel] 与 [`TestModel`](test.md) 类似，
但可以更细致地控制模型行为。

它的主要用例是执行比 `TestModel` 更高级的单元测试。

下面是一个最小示例：

```py {title="function_model_usage.py" call_name="test_my_agent" noqa="I001"}
from pydantic_ai import Agent
from pydantic_ai import ModelMessage, ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel, AgentInfo

my_agent = Agent('openai:gpt-5.2')


async def model_function(
    messages: list[ModelMessage], info: AgentInfo
) -> ModelResponse:
    print(messages)
    """
    [
        ModelRequest(
            parts=[
                UserPromptPart(
                    content='Testing my agent...',
                    timestamp=datetime.datetime(...),
                )
            ],
            timestamp=datetime.datetime(...),
            run_id='...',
            conversation_id='...',
        )
    ]
    """
    print(info)
    """
    AgentInfo(
        function_tools=[],
        allow_text_output=True,
        output_tools=[],
        model_settings=None,
        model_request_parameters=ModelRequestParameters(
            function_tools=[], native_tools=[], output_tools=[]
        ),
        instructions=None,
    )
    """
    return ModelResponse(parts=[TextPart('hello world')])


async def test_my_agent():
    """Unit test for my_agent, to be run by pytest."""
    with my_agent.override(model=FunctionModel(model_function)):
        result = await my_agent.run('Testing my agent...')
        assert result.output == 'hello world'
```

详细文档请参见[使用 `FunctionModel` 进行单元测试](../../testing.md#unit-testing-with-functionmodel)。

::: pydantic_ai.models.function
